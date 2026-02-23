from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests
import streamlit as st

NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"
CHICAGO_TZ = ZoneInfo("America/Chicago")

SEVERE_EVENTS = {
    "Tornado Warning",
    "Severe Thunderstorm Warning",
    "Tornado Watch",
    "Severe Thunderstorm Watch",
}

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: your-email@example.com)",
    "Accept": "application/geo+json, application/json",
}


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _format_central_time(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    return dt.astimezone(CHICAGO_TZ).strftime("%I:%M %p CT").lstrip("0")


def _short_event_name(event: str) -> str:
    mapping = {
        "Tornado Warning": "TORNADO WARNING",
        "Severe Thunderstorm Warning": "SEVERE TSTM WARNING",
        "Tornado Watch": "TORNADO WATCH",
        "Severe Thunderstorm Watch": "SEVERE TSTM WATCH",
    }
    return mapping.get(event, event.upper())


def _short_area(area_desc: str, max_len: int = 120) -> str:
    text = (area_desc or "").strip()
    if not text:
        return "U.S."
    return text if len(text) <= max_len else f"{text[: max_len - 1].rstrip()}..."


def _build_display_text(event: str, area_desc: str, ends_dt: Optional[datetime]) -> str:
    event_txt = _short_event_name(event)
    area_txt = _short_area(area_desc)
    time_txt = _format_central_time(ends_dt)
    if not time_txt:
        return f"{event_txt} - {area_txt}"
    tail = "Until" if event.endswith("Watch") else "Expires"
    return f"{event_txt} - {area_txt} - {tail} {time_txt}"


def _parse_features(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()

    for feat in features:
        props = (feat or {}).get("properties", {}) or {}
        event = str(props.get("event") or "").strip()
        if event not in SEVERE_EVENTS:
            continue

        status = str(props.get("status") or "").strip()
        if status and status != "Actual":
            continue

        alert_id = str(props.get("id") or props.get("@id") or "").strip()
        if alert_id and alert_id in seen_ids:
            continue
        if alert_id:
            seen_ids.add(alert_id)

        area_desc = str(props.get("areaDesc") or "").strip()
        end_raw = (
            str(props.get("ends") or "").strip()
            or str(props.get("expires") or "").strip()
        )
        ends_dt = _parse_dt(end_raw)

        results.append(
            {
                "event": event,
                "areaDesc": area_desc,
                "ends_dt": ends_dt,
                "display_text": _build_display_text(event, area_desc, ends_dt),
            }
        )

    return results


def fetch_us_severe_alerts(timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetch active nationwide severe watch/warning alerts.

    Keeps only exact event matches:
    - Tornado Warning
    - Severe Thunderstorm Warning
    - Tornado Watch
    - Severe Thunderstorm Watch
    """
    try:
        resp = requests.get(NWS_ALERTS_URL, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        data = resp.json() or {}
        features = data.get("features", []) or []
    except Exception:
        return []

    return _parse_features(features)


@st.cache_data(ttl=90, show_spinner=False)
def get_cached_severe_alerts_payload() -> Tuple[List[Dict[str, Any]], bool]:
    """Return (alerts, had_error)."""
    try:
        resp = requests.get(NWS_ALERTS_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json() or {}
        features = data.get("features", []) or []
    except Exception:
        return [], True
    return _parse_features(features), False
