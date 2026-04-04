from __future__ import annotations

import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Callable

from utils.nws import HEADERS as NWS_HEADERS
from utils.nws import get_nws_point_properties
from utils.nws_alerts import _parse_dt
from utils.resilience import request_json
from utils.spc import get_day1_location_risk_summary, get_spc_location_percents_cached


LOGGER = logging.getLogger(__name__)

DEFAULT_SOURCE_TTLS = {
    "alerts": int(os.getenv("EXTERNAL_CONTEXT_TTL_ALERTS", "120")),
    "forecast": int(os.getenv("EXTERNAL_CONTEXT_TTL_FORECAST", "600")),
    "observations": int(os.getenv("EXTERNAL_CONTEXT_TTL_OBSERVATIONS", "120")),
    "spc": int(os.getenv("EXTERNAL_CONTEXT_TTL_SPC", "300")),
    "radar": int(os.getenv("EXTERNAL_CONTEXT_TTL_RADAR", "1800")),
}
REQUEST_TIMEOUT_SECONDS = int(os.getenv("EXTERNAL_CONTEXT_TIMEOUT_SECONDS", "12"))
MAX_ALERT_ITEMS = int(os.getenv("EXTERNAL_CONTEXT_MAX_ALERT_ITEMS", "5"))
MAX_FORECAST_PERIODS = int(os.getenv("EXTERNAL_CONTEXT_MAX_FORECAST_PERIODS", "3"))

_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, tuple[float, Any]] = {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _compact_text(value: str | None, *, max_chars: int = 220) -> str | None:
    if not value:
        return None
    text = " ".join(str(value).split())
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3].rstrip()}..."


def _session_value(session_state: Any, key: str, default: Any = None) -> Any:
    if isinstance(session_state, dict):
        return session_state.get(key, default)
    try:
        return session_state.get(key, default)
    except Exception:
        return default


def _session_snapshot(session_state: Any) -> dict[str, Any]:
    return {
        "city_key": _session_value(session_state, "city_key"),
        "lat": _safe_float(_session_value(session_state, "lat")),
        "lon": _safe_float(_session_value(session_state, "lon")),
        "selected_state": _session_value(session_state, "selected_state"),
        "selected_radar_station": _session_value(session_state, "selected_radar_station")
        or _session_value(session_state, "radar_station"),
        "selected_mesoanalysis_sector": _session_value(session_state, "selected_mesoanalysis_sector"),
        "selected_mesoanalysis_parameter": _session_value(session_state, "selected_mesoanalysis_parameter"),
        "spc_open_detail_day": _session_value(session_state, "spc_open_detail_day"),
        "selected_model_name": _session_value(session_state, "selected_model_name"),
        "selected_model_run": _session_value(session_state, "selected_model_run"),
        "selected_forecast_hour": _session_value(session_state, "selected_forecast_hour"),
        "location_source": _session_value(session_state, "location_source"),
        "simulate_outbreak_mode": bool(_session_value(session_state, "simulate_outbreak_mode", False)),
        "simulate_outbreak_scenario": _session_value(session_state, "simulate_outbreak_scenario"),
    }


def _cache_key(source_name: str, lat: float | None, lon: float | None, extra: dict[str, Any] | None = None) -> str:
    payload = {
        "source": source_name,
        "lat": round(lat, 4) if lat is not None else None,
        "lon": round(lon, 4) if lon is not None else None,
        "extra": extra or {},
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _get_cached(key: str) -> Any | None:
    now = time.time()
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at <= now:
            _CACHE.pop(key, None)
            return None
        return value


def _set_cached(key: str, value: Any, ttl_seconds: int) -> Any:
    with _CACHE_LOCK:
        _CACHE[key] = (time.time() + max(ttl_seconds, 1), value)
    return value


def _remember(source_name: str, lat: float | None, lon: float | None, ttl_seconds: int, builder: Callable[[], dict[str, Any]], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    key = _cache_key(source_name, lat, lon, extra)
    cached = _get_cached(key)
    if cached is not None:
        cached_copy = dict(cached)
        cached_copy["cache_status"] = "hit"
        return cached_copy

    value = builder()
    value["cache_status"] = "miss"
    return _set_cached(key, value, ttl_seconds)


def _request_json(url: str, *, params: dict[str, Any] | None = None, timeout: int = REQUEST_TIMEOUT_SECONDS) -> dict[str, Any]:
    payload, _status = request_json(
        url=url,
        params=params,
        headers=NWS_HEADERS,
        timeout=min(timeout, REQUEST_TIMEOUT_SECONDS),
        endpoint="external_context.request_json",
        source="External weather context",
        cache_key=f"external_context:{url}:{repr(sorted((params or {}).items()))}",
        validator=lambda value: value if isinstance(value, dict) else {},
    )
    return payload


def _failure_payload(source_name: str, error: Exception, *, caveat: str) -> dict[str, Any]:
    return {
        "source": source_name,
        "loaded": False,
        "timestamp": _utc_now_iso(),
        "summary": f"{source_name} data is unavailable right now.",
        "error": type(error).__name__,
        "caveats": [caveat],
    }


def get_nws_alert_context(lat: float, lon: float) -> dict[str, Any]:
    def _build() -> dict[str, Any]:
        payload = _request_json(
            "https://api.weather.gov/alerts/active",
            params={"point": f"{lat:.4f},{lon:.4f}"},
        )
        features = payload.get("features") or []
        features = sorted(
            features,
            key=lambda feature: (
                _parse_dt(((feature or {}).get("properties") or {}).get("effective"))
                or _parse_dt(((feature or {}).get("properties") or {}).get("onset"))
                or datetime.min.replace(tzinfo=timezone.utc)
            ),
            reverse=True,
        )
        alerts: list[dict[str, Any]] = []
        counts_by_event: dict[str, int] = {}

        for feature in features[:MAX_ALERT_ITEMS]:
            props = (feature or {}).get("properties") or {}
            event = str(props.get("event") or "Alert").strip()
            counts_by_event[event] = counts_by_event.get(event, 0) + 1
            alerts.append(
                {
                    "event": event,
                    "headline": props.get("headline"),
                    "severity": props.get("severity"),
                    "urgency": props.get("urgency"),
                    "certainty": props.get("certainty"),
                    "area": _compact_text(props.get("areaDesc"), max_chars=140),
                    "onset": props.get("onset"),
                    "effective": props.get("effective"),
                    "expires": props.get("expires") or props.get("ends"),
                    "summary": _compact_text(props.get("description"), max_chars=200),
                }
            )

        latest_timestamp = None
        for alert in alerts:
            for key in ("effective", "onset", "expires"):
                if alert.get(key):
                    latest_timestamp = alert[key]
                    break
            if latest_timestamp:
                break

        if alerts:
            top_events = ", ".join(f"{name} ({count})" for name, count in sorted(counts_by_event.items()))
            summary = f"{len(alerts)} active NWS alerts near the selected point. Top alert types: {top_events}."
        else:
            summary = "No active NWS alerts were returned for the selected point."

        return {
            "source": "NOAA/NWS api.weather.gov alerts",
            "loaded": True,
            "timestamp": latest_timestamp or _utc_now_iso(),
            "key_values": {
                "alert_count": len(alerts),
                "counts_by_event": counts_by_event,
            },
            "alerts": alerts,
            "summary": summary,
            "caveats": [
                "Alerts are filtered to the selected point and can change between assistant turns.",
                "A quiet alert response does not replace official warning reception methods.",
            ],
        }

    try:
        return _remember("alerts", lat, lon, DEFAULT_SOURCE_TTLS["alerts"], _build)
    except Exception as exc:
        LOGGER.warning("External alerts context failed lat=%s lon=%s error=%s", lat, lon, exc)
        return _failure_payload(
            "NOAA/NWS api.weather.gov alerts",
            exc,
            caveat="Alert context failed, so the assistant should answer from other live sources and internal site context.",
        )


def get_nws_forecast_context(lat: float, lon: float) -> dict[str, Any]:
    def _build() -> dict[str, Any]:
        from utils.forecast import _get_json as get_cached_forecast_json

        point_props = get_nws_point_properties(lat, lon)
        forecast_url = point_props.get("forecast")
        hourly_url = point_props.get("forecastHourly")
        if not forecast_url or not hourly_url:
            raise ValueError("Forecast endpoints missing from NWS points metadata.")

        daily_payload = get_cached_forecast_json(forecast_url)
        hourly_payload = get_cached_forecast_json(hourly_url)
        daily_periods = ((daily_payload.get("properties") or {}).get("periods") or [])[:MAX_FORECAST_PERIODS]
        hourly_periods = ((hourly_payload.get("properties") or {}).get("periods") or [])[:MAX_FORECAST_PERIODS]

        compact_daily = [
            {
                "name": period.get("name"),
                "temperature_f": period.get("temperature"),
                "temperature_unit": period.get("temperatureUnit"),
                "precipitation_percent": _safe_int((period.get("probabilityOfPrecipitation") or {}).get("value")),
                "wind": " ".join(
                    part for part in [str(period.get("windDirection") or "").strip(), str(period.get("windSpeed") or "").strip()] if part
                )
                or None,
                "short_forecast": period.get("shortForecast"),
                "detailed_forecast": _compact_text(period.get("detailedForecast"), max_chars=180),
                "start_time": period.get("startTime"),
            }
            for period in daily_periods
        ]
        compact_hourly = [
            {
                "name": period.get("name"),
                "temperature_f": period.get("temperature"),
                "temperature_unit": period.get("temperatureUnit"),
                "precipitation_percent": _safe_int((period.get("probabilityOfPrecipitation") or {}).get("value")),
                "short_forecast": period.get("shortForecast"),
                "start_time": period.get("startTime"),
            }
            for period in hourly_periods
        ]

        lead_daily = compact_daily[0] if compact_daily else {}
        summary = (
            f"NWS forecast near the selected point starts with {lead_daily.get('name') or 'the next period'}: "
            f"{lead_daily.get('short_forecast') or 'forecast text unavailable'}."
        )

        return {
            "source": "NOAA/NWS api.weather.gov forecast",
            "loaded": True,
            "timestamp": (daily_payload.get("properties") or {}).get("updated")
            or (hourly_payload.get("properties") or {}).get("updated")
            or _utc_now_iso(),
            "key_values": {
                "forecast_office": point_props.get("cwa"),
                "daily_period_count": len(compact_daily),
                "hourly_period_count": len(compact_hourly),
            },
            "daily_periods": compact_daily,
            "hourly_periods": compact_hourly,
            "summary": summary,
            "caveats": [
                "Forecast periods are official NWS guidance, not deterministic storm reports.",
                "Only the nearest few periods are included here to stay token-efficient.",
            ],
        }

    try:
        return _remember("forecast", lat, lon, DEFAULT_SOURCE_TTLS["forecast"], _build)
    except Exception as exc:
        LOGGER.warning("External forecast context failed lat=%s lon=%s error=%s", lat, lon, exc)
        return _failure_payload(
            "NOAA/NWS api.weather.gov forecast",
            exc,
            caveat="Forecast context failed, so the assistant should avoid quoting unavailable periods as current.",
        )


def get_nws_observation_context(lat: float, lon: float) -> dict[str, Any]:
    def _build() -> dict[str, Any]:
        from utils.observations import (
            _c_to_f,
            _deg_to_compass,
            _get_nws_latest_obs_near_point,
            _ms_to_mph,
            _safe,
        )

        obs, station_id = _get_nws_latest_obs_near_point(lat, lon)
        if not obs:
            raise ValueError("No usable nearby NWS observation station returned data.")

        temperature_f = _safe_int(_c_to_f(_safe(obs, "temperature", "value")))
        dewpoint_f = _safe_int(_c_to_f(_safe(obs, "dewpoint", "value")))
        wind_speed_mph = _safe_int(_ms_to_mph(_safe(obs, "windSpeed", "value")))
        wind_gust_mph = _safe_int(_ms_to_mph(_safe(obs, "windGust", "value")))
        wind_direction_deg = _safe(obs, "windDirection", "value")
        wind_direction_cardinal = _deg_to_compass(wind_direction_deg)
        summary_parts = []
        if temperature_f is not None:
            summary_parts.append(f"temp {temperature_f}F")
        if dewpoint_f is not None:
            summary_parts.append(f"dewpoint {dewpoint_f}F")
        if wind_speed_mph is not None:
            summary_parts.append(
                f"wind {wind_direction_cardinal or 'variable'} {wind_speed_mph} mph"
            )
        if obs.get("textDescription"):
            summary_parts.append(str(obs.get("textDescription")))

        return {
            "source": "NOAA/NWS api.weather.gov observations",
            "loaded": True,
            "timestamp": obs.get("timestamp") or _utc_now_iso(),
            "key_values": {
                "station_id": station_id,
                "temperature_f": temperature_f,
                "dewpoint_f": dewpoint_f,
                "relative_humidity_percent": _safe_int(_safe(obs, "relativeHumidity", "value")),
                "wind_direction_degrees": _safe_int(wind_direction_deg),
                "wind_direction_cardinal": wind_direction_cardinal,
                "wind_speed_mph": wind_speed_mph,
                "wind_gust_mph": wind_gust_mph,
                "conditions": obs.get("textDescription"),
            },
            "summary": "Latest nearby observation: " + ", ".join(summary_parts) if summary_parts else "Latest nearby observation is available.",
            "caveats": [
                "Nearest-station observations can lag or reflect conditions a short distance from the exact map point.",
                "Single-station data should be interpreted alongside radar, alerts, and forecast context.",
            ],
        }

    try:
        return _remember("observations", lat, lon, DEFAULT_SOURCE_TTLS["observations"], _build)
    except Exception as exc:
        LOGGER.warning("External observation context failed lat=%s lon=%s error=%s", lat, lon, exc)
        return _failure_payload(
            "NOAA/NWS api.weather.gov observations",
            exc,
            caveat="Observation context failed, so the assistant should not infer current conditions beyond the remaining data.",
        )


def get_spc_context(lat: float, lon: float, session_state: Any) -> dict[str, Any]:
    session = _session_snapshot(session_state)

    def _build() -> dict[str, Any]:
        point_summary = get_spc_location_percents_cached(lat, lon)
        qualitative = get_day1_location_risk_summary(point_summary)

        day1_hazards = {
            "tornado_percent": point_summary.get("d1_tor"),
            "wind_percent": point_summary.get("d1_wind"),
            "hail_percent": point_summary.get("d1_hail"),
            "tornado_cig": point_summary.get("d1_tor_cig"),
            "wind_cig": point_summary.get("d1_wind_cig"),
            "hail_cig": point_summary.get("d1_hail_cig"),
        }
        day2_hazards = {
            "tornado_percent": point_summary.get("d2_tor"),
            "wind_percent": point_summary.get("d2_wind"),
            "hail_percent": point_summary.get("d2_hail"),
            "tornado_cig": point_summary.get("d2_tor_cig"),
            "wind_cig": point_summary.get("d2_wind_cig"),
            "hail_cig": point_summary.get("d2_hail_cig"),
        }
        summary = (
            f"SPC point outlook for the selected location: Day 1 category {point_summary.get('day1_cat') or 'NONE'}; "
            f"Day 1 hazards tornado {day1_hazards['tornado_percent'] or 0}%, wind {day1_hazards['wind_percent'] or 0}%, "
            f"hail {day1_hazards['hail_percent'] or 0}%."
        )

        return {
            "source": "NOAA/SPC structured outlook map service",
            "loaded": True,
            "timestamp": _utc_now_iso(),
            "key_values": {
                "day1_category": point_summary.get("day1_cat"),
                "day3_probability_percent": point_summary.get("d3_prob"),
                "selected_mesoanalysis_sector": session.get("selected_mesoanalysis_sector"),
                "selected_mesoanalysis_parameter": session.get("selected_mesoanalysis_parameter"),
            },
            "day1_hazards": day1_hazards,
            "day2_hazards": day2_hazards,
            "day3_probability_percent": point_summary.get("d3_prob"),
            "qualitative_day1_risk": qualitative,
            "summary": summary,
            "caveats": [
                "SPC outlook values are probabilistic guidance for severe-weather risk, not a guarantee at the exact point.",
                "This app currently has structured SPC point data, but not a structured mesoanalysis field feed.",
            ],
        }

    try:
        return _remember(
            "spc",
            lat,
            lon,
            DEFAULT_SOURCE_TTLS["spc"],
            _build,
            extra={
                "meso_sector": session.get("selected_mesoanalysis_sector"),
                "meso_parameter": session.get("selected_mesoanalysis_parameter"),
            },
        )
    except Exception as exc:
        LOGGER.warning("External SPC context failed lat=%s lon=%s error=%s", lat, lon, exc)
        return _failure_payload(
            "NOAA/SPC structured outlook map service",
            exc,
            caveat="SPC outlook context failed, so the assistant should avoid asserting point risk values this turn.",
        )


def get_radar_context(lat: float, lon: float, session_state: Any) -> dict[str, Any]:
    session = _session_snapshot(session_state)

    def _build() -> dict[str, Any]:
        point_props = get_nws_point_properties(lat, lon)
        radar_station = session.get("selected_radar_station") or point_props.get("radarStation")
        if not radar_station:
            raise ValueError("No radar station metadata was available from the NWS points endpoint.")

        return {
            "source": "NOAA/NWS points and RIDGE radar metadata",
            "loaded": True,
            "timestamp": _utc_now_iso(),
            "key_values": {
                "radar_station": radar_station,
                "forecast_office": point_props.get("cwa"),
                "grid_id": point_props.get("gridId"),
                "grid_x": point_props.get("gridX"),
                "grid_y": point_props.get("gridY"),
            },
            "radar_station": radar_station,
            "reflectivity_loop_url": f"https://radar.weather.gov/ridge/standard/{radar_station}_loop.gif",
            "base_velocity_loop_url": f"https://radar.weather.gov/ridge/standard/base_velocity/{radar_station}_loop.gif",
            "summary": f"Nearest radar metadata points to station {radar_station}.",
            "caveats": [
                "This context includes radar metadata and loop URLs, not a parsed volumetric radar analysis.",
                "The nearest radar site may differ from a user-selected custom station if the UI adds one later.",
            ],
        }

    try:
        return _remember(
            "radar",
            lat,
            lon,
            DEFAULT_SOURCE_TTLS["radar"],
            _build,
            extra={"selected_radar_station": session.get("selected_radar_station")},
        )
    except Exception as exc:
        LOGGER.warning("External radar context failed lat=%s lon=%s error=%s", lat, lon, exc)
        return _failure_payload(
            "NOAA/NWS points and RIDGE radar metadata",
            exc,
            caveat="Radar metadata context failed, so the assistant should not assume a nearest radar station.",
        )


def summarize_external_context(raw_context: dict[str, Any]) -> dict[str, Any]:
    sections = (
        ("external_alerts", raw_context.get("external_alerts") or {}),
        ("external_forecast", raw_context.get("external_forecast") or {}),
        ("external_observations", raw_context.get("external_observations") or {}),
        ("external_spc", raw_context.get("external_spc") or {}),
        ("external_radar", raw_context.get("external_radar") or {}),
    )
    loaded_summaries = [
        str(section.get("summary"))
        for _, section in sections
        if section.get("loaded") and section.get("summary")
    ]
    failed_sections = [name for name, section in sections if not section.get("loaded", False)]

    summary = " ".join(loaded_summaries[:4]) if loaded_summaries else "External weather context is currently limited."
    limitations = list(raw_context.get("external_limitations") or [])
    if failed_sections:
        limitations.append(
            "Some external sources were unavailable during this turn: " + ", ".join(sorted(failed_sections)) + "."
        )

    return {
        "location_anchor": raw_context.get("location_anchor"),
        "summary": summary,
        "external_alerts": raw_context.get("external_alerts"),
        "external_forecast": raw_context.get("external_forecast"),
        "external_observations": raw_context.get("external_observations"),
        "external_spc": raw_context.get("external_spc"),
        "external_radar": raw_context.get("external_radar"),
        "external_data_sources": raw_context.get("external_data_sources"),
        "external_limitations": limitations,
        "external_fetch_status": raw_context.get("external_fetch_status"),
    }


def merge_internal_and_external_context(internal_context: dict[str, Any], external_context: dict[str, Any]) -> dict[str, Any]:
    merged = dict(internal_context)
    merged["external_weather_context"] = summarize_external_context(external_context)
    site_overview = dict(merged.get("site_overview") or {})
    site_overview["context_pipeline"] = {
        "steps": [
            "build_internal_site_context",
            "fetch_external_weather_context",
            "merge_internal_and_external_context",
            "serialize_context_for_model",
        ],
        "external_sources_loaded": (external_context.get("external_fetch_status") or {}).get("loaded_sources") or [],
        "external_sources_failed": (external_context.get("external_fetch_status") or {}).get("failed_sources") or [],
    }
    merged["site_overview"] = site_overview
    return merged


def get_external_weather_context(lat: float | None, lon: float | None, session_state: Any) -> dict[str, Any]:
    session = _session_snapshot(session_state)
    if lat is None or lon is None:
        return summarize_external_context(
            {
                "location_anchor": {
                    "selected_city": session.get("city_key"),
                    "latitude": lat,
                    "longitude": lon,
                    "selected_state": session.get("selected_state"),
                    "selected_radar_station": session.get("selected_radar_station"),
                    "selected_mesoanalysis_sector": session.get("selected_mesoanalysis_sector"),
                    "selected_mesoanalysis_parameter": session.get("selected_mesoanalysis_parameter"),
                },
                "external_alerts": {
                    "source": "NOAA/NWS api.weather.gov alerts",
                    "loaded": False,
                    "timestamp": _utc_now_iso(),
                    "summary": "Alerts were not requested because the selected location is unavailable.",
                },
                "external_forecast": {
                    "source": "NOAA/NWS api.weather.gov forecast",
                    "loaded": False,
                    "timestamp": _utc_now_iso(),
                    "summary": "Forecast data was not requested because the selected location is unavailable.",
                },
                "external_observations": {
                    "source": "NOAA/NWS api.weather.gov observations",
                    "loaded": False,
                    "timestamp": _utc_now_iso(),
                    "summary": "Observation data was not requested because the selected location is unavailable.",
                },
                "external_spc": {
                    "source": "NOAA/SPC structured outlook map service",
                    "loaded": False,
                    "timestamp": _utc_now_iso(),
                    "summary": "SPC point data was not requested because the selected location is unavailable.",
                },
                "external_radar": {
                    "source": "NOAA/NWS points and RIDGE radar metadata",
                    "loaded": False,
                    "timestamp": _utc_now_iso(),
                    "summary": "Radar metadata was not requested because the selected location is unavailable.",
                },
                "external_data_sources": [],
                "external_limitations": ["External live context needs a selected dashboard location with latitude and longitude."],
                "external_fetch_status": {
                    "generated_at": _utc_now_iso(),
                    "loaded_sources": [],
                    "failed_sources": ["alerts", "forecast", "observations", "spc", "radar"],
                },
            }
        )

    tasks = {
        "external_alerts": lambda: get_nws_alert_context(lat, lon),
        "external_forecast": lambda: get_nws_forecast_context(lat, lon),
        "external_observations": lambda: get_nws_observation_context(lat, lon),
        "external_spc": lambda: get_spc_context(lat, lon, session),
        "external_radar": lambda: get_radar_context(lat, lon, session),
    }
    results: dict[str, Any] = {}
    loaded_sources: list[str] = []
    failed_sources: list[str] = []

    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {executor.submit(task): name for name, task in tasks.items()}
        for future in as_completed(futures):
            section_name = futures[future]
            try:
                section = future.result()
                results[section_name] = section
                if section.get("loaded"):
                    loaded_sources.append(section_name)
                else:
                    failed_sources.append(section_name)
            except Exception as exc:
                failed_sources.append(section_name)
                source_label = section_name.replace("external_", "").replace("_", " ")
                results[section_name] = _failure_payload(
                    source_label,
                    exc,
                    caveat="The assistant should continue using the remaining external sources and internal site context.",
                )
                LOGGER.warning("External context source failed: %s error=%s", section_name, exc)

    LOGGER.info(
        "External context pipeline completed loaded=%s failed=%s location=%s",
        loaded_sources,
        failed_sources,
        {"lat": round(lat, 4), "lon": round(lon, 4), "city": session.get("city_key")},
    )

    external_context = {
        "location_anchor": {
            "selected_city": session.get("city_key"),
            "latitude": lat,
            "longitude": lon,
            "selected_state": session.get("selected_state"),
            "selected_radar_station": session.get("selected_radar_station") or (results.get("external_radar") or {}).get("radar_station"),
            "selected_mesoanalysis_sector": session.get("selected_mesoanalysis_sector"),
            "selected_mesoanalysis_parameter": session.get("selected_mesoanalysis_parameter"),
            "selected_model_name": session.get("selected_model_name"),
            "selected_model_run": session.get("selected_model_run"),
            "selected_forecast_hour": session.get("selected_forecast_hour"),
        },
        "external_alerts": results.get("external_alerts"),
        "external_forecast": results.get("external_forecast"),
        "external_observations": results.get("external_observations"),
        "external_spc": results.get("external_spc"),
        "external_radar": results.get("external_radar"),
        "external_data_sources": [
            {
                "name": "NOAA/NWS api.weather.gov",
                "sections": ["external_alerts", "external_forecast", "external_observations", "external_radar"],
            },
            {
                "name": "NOAA/SPC structured outlook map service",
                "sections": ["external_spc"],
            },
        ],
        "external_limitations": [
            "Structured API responses are summarized into compact fields rather than passed through as raw payloads.",
            "If a source fails, the assistant should note the gap and continue with the remaining sources.",
            "Radar context currently provides station metadata and loop references, not parsed radar volumes.",
        ],
        "external_fetch_status": {
            "generated_at": _utc_now_iso(),
            "loaded_sources": sorted(loaded_sources),
            "failed_sources": sorted(failed_sources),
        },
    }
    return summarize_external_context(external_context)
