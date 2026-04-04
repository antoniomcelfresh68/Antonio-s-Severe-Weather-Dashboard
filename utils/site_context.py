from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

from utils.about import ABOUT_CONTENT_MARKDOWN
from utils.config import APP_TITLE
from utils.external_context import (
    get_external_weather_context,
    merge_internal_and_external_context,
)
from utils.nws import get_nws_point_properties
from utils.satelite import GOES_BASE, GOES_PRODUCTS, GOES_SATS, GOES_SECTORS


AI_PAGE_CONTEXT_KEY = "ai_page_context"
AI_CURRENT_PAGE_KEY = "ai_current_page"

NAVIGATION_STRUCTURE = [
    {
        "label": "Home",
        "page_key": "Home",
        "description": "Landing view with glance panels, national Day 1 SPC summary, and Day 1-8 outlook imagery.",
    },
    {
        "label": "Observations",
        "page_key": "Observations",
        "description": "Mesoanalysis, local radar loops, nearby station observations, and GOES satellite imagery.",
    },
    {
        "label_template": "Forecast for {location}",
        "page_key": "Forecast",
        "description": "Location-aware NOAA/NWS hourly and multi-period forecast summaries.",
    },
    {
        "label": "Photo Gallery",
        "page_key": "Photo Gallery",
        "description": "Storm photography and visual portfolio content.",
    },
    {
        "label": "About",
        "page_key": "About",
        "description": "Feature guide, project purpose, architecture notes, and roadmap.",
    },
]

DATA_SOURCE_NOTES = [
    {
        "source": "SPC",
        "products": ["Convective outlooks", "Hazard probabilities", "Mesoanalysis"],
        "caveat": "SPC outlooks describe severe-weather risk areas and probabilities, not a guarantee that severe weather will occur at a point.",
    },
    {
        "source": "NOAA/NWS api.weather.gov",
        "products": ["Forecast periods", "Observation station metadata", "Radar station metadata", "Time zone and CWA metadata"],
        "caveat": "Forecast and observation values are official but can update between assistant turns, so time sensitivity should be acknowledged.",
    },
    {
        "source": "NOAA/NWS RIDGE",
        "products": ["Radar reflectivity and base velocity loops"],
        "caveat": "Loop GIFs provide visual situational awareness but are not a substitute for interrogating full radar datasets.",
    },
    {
        "source": "NOAA NESDIS STAR",
        "products": ["GOES satellite imagery"],
        "caveat": "Satellite products help with cloud-top and large-scale pattern assessment but do not directly measure surface hazards.",
    },
    {
        "source": "OpenStreetMap Nominatim",
        "products": ["Location search and geocoding"],
        "caveat": "Search labels are convenience names and may differ from forecast office naming conventions.",
    },
]

UI_EXPLAINERS = {
    "dashboard_role": "The assistant should behave like a dashboard guide and weather explainer, using live state when available and static site knowledge when a section is not loaded.",
    "spc_categories": {
        "TSTM": "General thunderstorm risk without a highlighted severe category.",
        "MRGL": "Marginal severe risk, usually isolated severe reports.",
        "SLGT": "Slight severe risk, scattered severe storms are possible.",
        "ENH": "Enhanced severe risk, a more concentrated severe corridor is possible.",
        "MDT": "Moderate severe risk, a significant organized severe setup may be unfolding.",
        "HIGH": "High severe risk, reserved for the most dangerous major outbreak setups.",
    },
    "hazard_fields": {
        "tornado_percent": "SPC point probability for tornadoes at the selected location.",
        "wind_percent": "SPC point probability for severe wind at the selected location.",
        "hail_percent": "SPC point probability for severe hail at the selected location.",
        "cig": "Conditional Intensity Group tag used by SPC on some hazard probabilities to flag stronger-event potential.",
    },
    "observations": {
        "mesoanalysis": "SPC mesoanalysis is an expert analysis page showing environment fields like pressure, instability, shear, and moisture.",
        "radar": "Radar loops show recent reflectivity and velocity trends for the nearest available radar site.",
        "satellite": "GOES imagery provides cloud and upper-level pattern context; current dashboard defaults to GOES-East CONUS GeoColor.",
    },
    "forecast": {
        "hero": "The forecast hero summarizes the current period and a near-term trend cue.",
        "hourly": "Hour By Hour condenses the next 12 forecast periods into temperature and precipitation trends.",
        "daily": "The Bigger Picture lists longer detailed forecast periods and may insert front-like trend callouts.",
    },
    "location_tools": {
        "search": "City or address search updates the shared dashboard location.",
        "device": "Use Device requests browser geolocation and swaps the dashboard to the nearest city label.",
        "local_office": "The Local NWS Office link jumps to the forecast office associated with the selected point.",
    },
}


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _compact_text(value: str | None, *, max_chars: int = 420) -> str | None:
    if not value:
        return None
    text = " ".join(str(value).split())
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3].rstrip()}..."


def _local_nws_office_url(lat: float | None, lon: float | None) -> str | None:
    if lat is None or lon is None:
        return None
    try:
        office_code = get_nws_point_properties(lat, lon).get("cwa")
        if isinstance(office_code, str) and office_code:
            return f"https://www.weather.gov/{office_code.lower()}/"
    except Exception:
        return None
    return None


def _get_page_context(page_name: str) -> dict[str, Any]:
    page_contexts = st.session_state.get(AI_PAGE_CONTEXT_KEY, {})
    raw_context = page_contexts.get(page_name, {})
    return raw_context if isinstance(raw_context, dict) else {}


def _iso_now_strings(lat: float | None, lon: float | None) -> dict[str, str]:
    tz_name = "UTC"
    if lat is not None and lon is not None:
        try:
            tz_name = str(get_nws_point_properties(lat, lon).get("timeZone") or "UTC")
        except Exception:
            tz_name = "UTC"

    now_utc = datetime.now(timezone.utc)
    try:
        local_zone = ZoneInfo(tz_name)
    except Exception:
        local_zone = timezone.utc
        tz_name = "UTC"

    now_local = now_utc.astimezone(local_zone)
    return {
        "timezone": tz_name,
        "local_time": now_local.isoformat(),
        "utc_time": now_utc.isoformat(),
    }


def _build_navigation_structure(location_name: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for item in NAVIGATION_STRUCTURE:
        label = item.get("label")
        if label is None:
            label = str(item["label_template"]).format(location=location_name)
        items.append(
            {
                "label": label,
                "page_key": str(item["page_key"]),
                "description": str(item["description"]),
            }
        )
    return items


def _build_current_location_context(lat: float | None, lon: float | None, location_name: str) -> dict[str, Any]:
    if lat is None or lon is None:
        return {
            "name": location_name,
            "latitude": lat,
            "longitude": lon,
        }

    point_props: dict[str, Any] = {}
    try:
        point_props = get_nws_point_properties(lat, lon)
    except Exception:
        point_props = {}

    relative_location = (point_props.get("relativeLocation") or {}).get("properties", {})
    return {
        "name": location_name,
        "latitude": lat,
        "longitude": lon,
        "location_source": st.session_state.get("location_source") or "unknown",
        "timezone": point_props.get("timeZone"),
        "radar_station": point_props.get("radarStation"),
        "forecast_office": point_props.get("cwa"),
        "forecast_zone": point_props.get("forecastZone"),
        "county": point_props.get("county"),
        "fire_weather_zone": point_props.get("fireWeatherZone"),
        "grid_id": point_props.get("gridId"),
        "grid_x": point_props.get("gridX"),
        "grid_y": point_props.get("gridY"),
        "relative_location": {
            "city": relative_location.get("city"),
            "state": relative_location.get("state"),
        },
        "local_nws_office_url": _local_nws_office_url(lat, lon),
    }


def _build_active_user_selection(current_page: str) -> dict[str, Any]:
    observations_page_context = _get_page_context("Observations")
    forecast_page_context = _get_page_context("Forecast")
    return {
        "current_page": current_page,
        "selected_navigation_key": st.session_state.get("nav") or current_page,
        "location_source": st.session_state.get("location_source") or "unknown",
        "selected_mesoanalysis_sector": st.session_state.get("selected_mesoanalysis_sector") or "19",
        "selected_mesoanalysis_parameter": (
            st.session_state.get("selected_mesoanalysis_parameter")
            or observations_page_context.get("selected_mesoanalysis_parameter")
            or "pmsl"
        ),
        "selected_model_name": st.session_state.get("selected_model_name") or forecast_page_context.get("selected_model"),
        "selected_model_run": st.session_state.get("selected_model_run") or forecast_page_context.get("selected_model_run"),
        "selected_forecast_hour": st.session_state.get("selected_forecast_hour") or forecast_page_context.get("selected_forecast_hour"),
        "open_spc_detail_day": st.session_state.get("spc_open_detail_day"),
        "assistant_modal_open": bool(st.session_state.get("show_ai", False)),
        "device_geolocation_pending": bool(st.session_state.get("device_loc_pending", False)),
        "simulate_outbreak_mode": bool(st.session_state.get("simulate_outbreak_mode", False)),
        "simulate_outbreak_scenario": st.session_state.get("simulate_outbreak_scenario"),
        "session_page_context_keys": sorted((st.session_state.get(AI_PAGE_CONTEXT_KEY) or {}).keys()),
    }


def get_home_context(lat: float | None, lon: float | None, location_name: str) -> dict[str, Any]:
    home_page_context = _get_page_context("Home")
    if lat is None or lon is None:
        return {
            "summary": "Home tab combines glance panels and SPC outlook content, but the current location is unavailable.",
            "page_context": home_page_context,
        }

    from utils.home import svr_count_cached, tor_count_cached
    from utils.observations import get_location_glance
    from utils.spc import (
        get_day1_location_risk_summary,
        get_spc_day1_national_summary_cached,
        get_spc_location_percents_cached,
    )

    current_year = datetime.now(UTC).year
    with ThreadPoolExecutor(max_workers=4) as executor:
        obs_future = executor.submit(get_location_glance, lat, lon)
        tor_future = executor.submit(tor_count_cached, current_year)
        svr_future = executor.submit(svr_count_cached, current_year)
        spc_future = executor.submit(get_spc_location_percents_cached, lat, lon)

    temp_f, dew_f, wind_text, conditions_text = obs_future.result()
    local_spc = spc_future.result()
    national_spc = get_spc_day1_national_summary_cached()
    local_risk_summary = get_day1_location_risk_summary(local_spc)

    return {
        "summary": "Home is the site-wide severe-weather overview page with live local glance metrics and SPC outlook imagery.",
        "glance_cards": {
            "temperature_and_dewpoint": {
                "temperature_f": _safe_int(temp_f),
                "dewpoint_f": _safe_int(dew_f),
                "wind": wind_text,
                "conditions": conditions_text,
            },
            "year_to_date_warning_counts": {
                "year": current_year,
                "tornado_warnings": tor_future.result(),
                "severe_thunderstorm_warnings": svr_future.result(),
            },
            "selected_location_day1_hazards": {
                "tornado_percent": local_spc.get("d1_tor"),
                "wind_percent": local_spc.get("d1_wind"),
                "hail_percent": local_spc.get("d1_hail"),
            },
        },
        "local_risk_summary": {
            "location": location_name,
            "day1_category": local_spc.get("day1_cat"),
            "hazards": local_risk_summary.get("hazards"),
            "message": local_risk_summary.get("message"),
            "day2_hazards": {
                "tornado_percent": local_spc.get("d2_tor"),
                "wind_percent": local_spc.get("d2_wind"),
                "hail_percent": local_spc.get("d2_hail"),
            },
            "day3_probability_percent": local_spc.get("d3_prob"),
        },
        "national_day1_summary": national_spc,
        "outlook_layout": {
            "primary_group": ["Day 1 Categorical", "Day 2 Categorical", "Day 3 Categorical"],
            "secondary_group": ["Day 4 Probability", "Day 5 Probability", "Day 6 Probability", "Day 7 Probability", "Day 8 Probability"],
            "detail_modal_available_for_days": [1, 2, 3],
        },
        "page_context": home_page_context,
    }


def get_observations_context(lat: float | None, lon: float | None, location_name: str) -> dict[str, Any]:
    observations_page_context = _get_page_context("Observations")
    from utils.observations import (
        DEFAULT_MESO_PARAMETER,
        DEFAULT_MESO_SECTOR,
        _build_spc_meso_url,
        _c_to_f,
        _deg_to_compass,
        _get_nearest_radar_id,
        _get_nws_latest_obs_near_point,
        _ms_to_mph,
        _safe,
    )

    sector = st.session_state.get("selected_mesoanalysis_sector") or DEFAULT_MESO_SECTOR
    parameter = (
        st.session_state.get("selected_mesoanalysis_parameter")
        or observations_page_context.get("selected_mesoanalysis_parameter")
        or DEFAULT_MESO_PARAMETER
    )

    if lat is None or lon is None:
        return {
            "summary": "Observations tab contains mesoanalysis, radar, station observations, and satellite views, but no location is selected.",
            "mesoanalysis": {
                "selected_sector": sector,
                "selected_parameter": parameter,
                "viewer_url": _build_spc_meso_url(sector, parameter),
            },
            "satellite": {
                "default_view": {
                    "satellite": GOES_SATS["GOES-East"],
                    "sector": GOES_SECTORS["CONUS"],
                    "product": GOES_PRODUCTS["GeoColor"],
                },
            },
            "page_context": observations_page_context,
        }

    obs, station_id = _get_nws_latest_obs_near_point(lat, lon)
    radar_id = _get_nearest_radar_id(lat, lon) or observations_page_context.get("radar_station") or "KTLX"

    latest_observation = None
    if obs:
        latest_observation = {
            "station_id": station_id,
            "timestamp": obs.get("timestamp"),
            "temperature_f": _safe_int(_c_to_f(_safe(obs, "temperature", "value"))),
            "dewpoint_f": _safe_int(_c_to_f(_safe(obs, "dewpoint", "value"))),
            "relative_humidity_percent": _safe_int(_safe(obs, "relativeHumidity", "value")),
            "wind_direction_cardinal": _deg_to_compass(_safe(obs, "windDirection", "value")),
            "wind_speed_mph": _safe_int(_ms_to_mph(_safe(obs, "windSpeed", "value"))),
            "wind_gust_mph": _safe_int(_ms_to_mph(_safe(obs, "windGust", "value"))),
            "conditions": obs.get("textDescription"),
        }

    return {
        "summary": "Observations collects environmental analysis, recent radar loops, nearby surface observations, and satellite imagery.",
        "mesoanalysis": {
            "selected_sector": sector,
            "selected_parameter": parameter,
            "viewer_url": _build_spc_meso_url(sector, parameter),
            "available_functionality": "Embedded SPC mesoanalysis page for parameter-based environmental analysis.",
        },
        "radar": {
            "station": radar_id,
            "reflectivity_loop_url": f"https://radar.weather.gov/ridge/standard/{radar_id}_loop.gif",
            "base_velocity_loop_url": f"https://radar.weather.gov/ridge/standard/base_velocity/{radar_id}_loop.gif",
        },
        "latest_observation": latest_observation,
        "satellite": {
            "default_view": {
                "satellite": GOES_SATS["GOES-East"],
                "sector": GOES_SECTORS["CONUS"],
                "product": GOES_PRODUCTS["GeoColor"],
                "base_url": GOES_BASE,
            },
            "available_satellites": list(GOES_SATS.keys()),
            "available_sectors": list(GOES_SECTORS.keys()),
            "available_products": list(GOES_PRODUCTS.keys()),
        },
        "page_context": observations_page_context,
    }


def get_forecast_context(lat: float | None, lon: float | None, location_name: str) -> dict[str, Any]:
    forecast_page_context = _get_page_context("Forecast")
    if lat is None or lon is None:
        return {
            "summary": "Forecast tab contains NOAA/NWS forecast views, but no location is selected.",
            "model_content": {
                "available": False,
                "message": "No dedicated numerical model controls are currently available in this dashboard state.",
            },
            "page_context": forecast_page_context,
        }

    from utils.forecast import (
        _detect_front_signal,
        _daytime_period_indices,
        _format_temp,
        _format_wind,
        _hero_outlook,
        _precip_value,
        get_location_forecast,
    )

    try:
        forecast = get_location_forecast(lat, lon)
    except Exception:
        return {
            "summary": "Forecast tab provides NOAA/NWS hourly and daily periods, but live forecast data is unavailable right now.",
            "model_content": {
                "available": False,
                "message": "No dedicated numerical model controls are currently available in this dashboard state.",
            },
            "page_context": forecast_page_context,
        }

    hourly_periods = forecast.get("hourly_periods") or []
    daily_periods = forecast.get("daily_periods") or []
    hero = _hero_outlook(hourly_periods, daily_periods) if hourly_periods or daily_periods else None

    hourly_summary = []
    for period in hourly_periods[:6]:
        hourly_summary.append(
            {
                "name": period.get("name"),
                "temperature": _format_temp(period),
                "precipitation_percent": _precip_value(period),
                "wind": _format_wind(period),
                "short_forecast": period.get("shortForecast"),
            }
        )

    daily_summary = []
    for period in daily_periods[:4]:
        daily_summary.append(
            {
                "name": period.get("name"),
                "temperature": _format_temp(period),
                "wind": _format_wind(period),
                "precipitation_percent": _precip_value(period),
                "short_forecast": period.get("shortForecast"),
                "detailed_forecast": _compact_text(period.get("detailedForecast"), max_chars=220),
            }
        )

    front_signals = []
    daytime_indices = _daytime_period_indices(daily_periods[:8])
    for index in range(len(daytime_indices) - 1):
        current_index = daytime_indices[index]
        next_index = daytime_indices[index + 1]
        signal = _detect_front_signal(daily_periods[current_index], daily_periods[next_index])
        if signal:
            front_signals.append(signal)

    return {
        "summary": "Forecast tab provides a quick hero outlook, 12-hour trend scan, and longer detailed NWS forecast periods.",
        "hero_outlook": hero,
        "hourly_summary": hourly_summary,
        "daily_summary": daily_summary,
        "front_signals": front_signals,
        "model_content": {
            "available": False,
            "message": "This dashboard currently uses NOAA/NWS forecast periods rather than a dedicated selectable model plot workflow.",
            "session_model_fields": {
                "selected_model_name": st.session_state.get("selected_model_name"),
                "selected_model_run": st.session_state.get("selected_model_run"),
                "selected_forecast_hour": st.session_state.get("selected_forecast_hour"),
            },
        },
        "page_context": {
            **forecast_page_context,
            "location": location_name,
            "hourly_period_count": len(hourly_periods),
            "daily_period_count": len(daily_periods),
        },
    }


def _build_spc_detail_summary(day: int) -> dict[str, Any] | None:
    from utils.spc_outlooks import get_day1_3_detail_payload

    try:
        payload = get_day1_3_detail_payload(day)
    except Exception:
        return None

    maps = payload.get("maps") or []
    return {
        "day": day,
        "title": payload.get("title"),
        "updated": payload.get("updated"),
        "valid_period": payload.get("valid_period"),
        "map_labels": [item.get("label") for item in maps if item.get("label")],
        "discussion_excerpt": _compact_text(payload.get("discussion"), max_chars=700),
        "page_url": payload.get("page_url"),
    }


def _build_spc_outlooks_context(lat: float | None, lon: float | None, location_name: str) -> dict[str, Any]:
    from utils.spc import get_day1_location_risk_summary, get_spc_location_percents_cached
    from utils.spc_outlooks import (
        get_day1_categorical_image_url,
        get_day2_categorical_image_url,
        get_day3_categorical_image_url,
        get_day4_8_prob_image_url,
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            "day1": executor.submit(get_day1_categorical_image_url),
            "day2": executor.submit(get_day2_categorical_image_url),
            "day3": executor.submit(get_day3_categorical_image_url),
            "day4": executor.submit(get_day4_8_prob_image_url, 4),
            "day5": executor.submit(get_day4_8_prob_image_url, 5),
            "day6": executor.submit(get_day4_8_prob_image_url, 6),
            "day7": executor.submit(get_day4_8_prob_image_url, 7),
            "day8": executor.submit(get_day4_8_prob_image_url, 8),
        }

        location_future = executor.submit(get_spc_location_percents_cached, lat, lon) if lat is not None and lon is not None else None
        detail_futures = {day: executor.submit(_build_spc_detail_summary, day) for day in (1, 2, 3)}

    location_summary = location_future.result() if location_future is not None else {}
    risk_summary = get_day1_location_risk_summary(location_summary) if location_summary else {"hazards": [], "message": None}

    day_cards = []
    for day in range(1, 9):
        image_key = f"day{day}"
        image_url = futures[image_key].result()
        card = {
            "day": day,
            "title": f"Day {day}",
            "image_available": bool(image_url),
            "image_url": image_url,
        }
        if day in detail_futures:
            card["detail_summary"] = detail_futures[day].result()
        day_cards.append(card)

    return {
        "summary": "SPC outlook content spans near-term categorical maps, longer-range probabilities, location-specific point values, and Day 1-3 discussion detail payloads.",
        "selected_location": location_name,
        "location_summary": {
            "day1_category": location_summary.get("day1_cat"),
            "day1_hazards": {
                "tornado_percent": location_summary.get("d1_tor"),
                "wind_percent": location_summary.get("d1_wind"),
                "hail_percent": location_summary.get("d1_hail"),
                "tornado_cig": location_summary.get("d1_tor_cig"),
                "wind_cig": location_summary.get("d1_wind_cig"),
                "hail_cig": location_summary.get("d1_hail_cig"),
            },
            "day2_hazards": {
                "tornado_percent": location_summary.get("d2_tor"),
                "wind_percent": location_summary.get("d2_wind"),
                "hail_percent": location_summary.get("d2_hail"),
                "tornado_cig": location_summary.get("d2_tor_cig"),
                "wind_cig": location_summary.get("d2_wind_cig"),
                "hail_cig": location_summary.get("d2_hail_cig"),
            },
            "day3_probability_percent": location_summary.get("d3_prob"),
            "qualitative_day1_risk": risk_summary,
        },
        "day_cards": day_cards,
    }


def get_popup_context(lat: float | None, lon: float | None, location_name: str) -> dict[str, Any]:
    open_spc_day = st.session_state.get("spc_open_detail_day")
    current_popup = None
    if open_spc_day in (1, 2, 3):
        current_popup = {
            "type": "spc_detail_dialog",
            "selected_day": open_spc_day,
            "payload": _build_spc_detail_summary(open_spc_day),
        }

    return {
        "current_popup": current_popup,
        "available_popups": [
            {
                "type": "assistant_modal",
                "description": "Chat modal for dashboard guidance and weather explanation using full-site context.",
                "is_open": bool(st.session_state.get("show_ai", False)),
            },
            {
                "type": "spc_detail_dialog",
                "description": "Day 1-3 outlook detail modal with validity period, map set, discussion text, and location summary.",
                "supported_days": [1, 2, 3],
                "selected_location": location_name if lat is not None and lon is not None else None,
            },
        ],
    }


def get_ui_explainer_context() -> dict[str, Any]:
    return UI_EXPLAINERS


def _build_about_context() -> dict[str, Any]:
    return {
        "summary": "About tab explains the dashboard purpose, major features, architecture, and roadmap.",
        "content_excerpt": _compact_text(ABOUT_CONTENT_MARKDOWN, max_chars=1000),
        "highlights": [
            "Nationwide severe alert ticker for tornado and severe thunderstorm watches and warnings.",
            "Shared location controls that propagate across Home, Observations, Forecast, and assistant context.",
            "Operational NOAA/NWS, SPC, radar, and GOES products arranged for quick situational awareness.",
        ],
    }


def _build_limitations_and_sources() -> dict[str, Any]:
    return {
        "sources": DATA_SOURCE_NOTES,
        "general_limitations": [
            "Assistant answers should distinguish between point-specific values, broader outlook areas, and explanatory site content.",
            "If a live section fails to load, the assistant should still explain what the section normally contains and note that current data is unavailable.",
            "The dashboard is informational and educational, not a substitute for official warning reception or emergency decision support.",
        ],
    }


def build_global_site_context() -> dict[str, Any]:
    current_page = str(st.session_state.get(AI_CURRENT_PAGE_KEY, "Home"))
    location_name = str(st.session_state.get("city_key") or "Unknown location")
    lat = _safe_float(st.session_state.get("lat"))
    lon = _safe_float(st.session_state.get("lon"))
    time_context = _iso_now_strings(lat, lon)

    return {
        "site_overview": {
            "dashboard_name": APP_TITLE,
            "purpose": "Location-aware severe weather dashboard that blends live operational weather data with explainers and guided navigation.",
            "assistant_role": "Use the full-site context, not only the currently visible page, and answer as both a dashboard guide and weather explainer.",
            "current_page": current_page,
            "generated_at": {
                "local_time": time_context["local_time"],
                "utc_time": time_context["utc_time"],
                "timezone": time_context["timezone"],
            },
        },
        "current_location": _build_current_location_context(lat, lon, location_name),
        "active_user_selection": _build_active_user_selection(current_page),
        "navigation_structure": _build_navigation_structure(location_name),
        "home_summary": get_home_context(lat, lon, location_name),
        "observations_summary": get_observations_context(lat, lon, location_name),
        "forecast_summary": get_forecast_context(lat, lon, location_name),
        "spc_outlooks": _build_spc_outlooks_context(lat, lon, location_name),
        "popup_details": get_popup_context(lat, lon, location_name),
        "about_summary": _build_about_context(),
        "glossary_or_explanations": get_ui_explainer_context(),
        "limitations_and_data_sources": _build_limitations_and_sources(),
        "session_context_registry": st.session_state.get(AI_PAGE_CONTEXT_KEY, {}),
    }


def build_internal_site_context() -> dict[str, Any]:
    return build_global_site_context()


def build_merged_site_context() -> dict[str, Any]:
    internal_context = build_internal_site_context()
    location = internal_context.get("current_location") or {}
    lat = _safe_float(location.get("latitude"))
    lon = _safe_float(location.get("longitude"))
    external_context = get_external_weather_context(lat, lon, st.session_state)
    return merge_internal_and_external_context(internal_context, external_context)


def build_assistant_context() -> dict[str, Any]:
    """Build a deliberately smaller context payload for OpenAI requests.

    The assistant needs the selected location, current page, a compact summary of
    loaded page context, and a light live-weather snapshot. Sending the entire
    site state or UI content increases privacy risk and latency without materially
    improving most assistant replies.
    """
    current_page = str(st.session_state.get(AI_CURRENT_PAGE_KEY, "Home"))
    location_name = str(st.session_state.get("city_key") or "Unknown location")
    lat = _safe_float(st.session_state.get("lat"))
    lon = _safe_float(st.session_state.get("lon"))

    page_context = _get_page_context(current_page)
    time_context = _iso_now_strings(lat, lon)
    external_context = get_external_weather_context(lat, lon, st.session_state)

    compact_external = {
        "alerts": ((external_context.get("external_alerts") or {}).get("alerts") or [])[:3],
        "forecast": ((external_context.get("external_forecast") or {}).get("daily_periods") or [])[:3],
        "observations": external_context.get("external_observations"),
        "spc": external_context.get("external_spc"),
        "fetch_status": external_context.get("external_fetch_status"),
    }

    return {
        "site_overview": {
            "dashboard_name": APP_TITLE,
            "current_page": current_page,
            "generated_at": time_context,
        },
        "current_location": {
            "name": location_name,
            "latitude": lat,
            "longitude": lon,
        },
        "page_context": {
            "current_page": current_page,
            "context": page_context,
        },
        "live_weather": compact_external,
        "limitations": [
            "Assistant context is intentionally compact and may omit nonessential UI state.",
            "Session state is ephemeral and may reset after app restart or when served by another instance.",
        ],
    }


def serialize_site_context(context: dict[str, Any]) -> str:
    return json.dumps(context, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def build_chat_prompt(context: dict[str, Any], user_message: str) -> list[dict[str, str]]:
    context_blob = serialize_site_context(context)
    return [
        {
            "role": "system",
            "content": (
                "Structured dashboard context follows as compact JSON. "
                "It includes full internal site context plus live external weather API context anchored to the selected dashboard location. "
                "Use it as the authoritative snapshot for all tabs, popups, help text, loaded location state, and live external weather data. "
                "Current page awareness is included inside the JSON, but do not restrict answers to that page."
            ),
        },
        {
            "role": "system",
            "content": f"full_dashboard_context={context_blob}",
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]
