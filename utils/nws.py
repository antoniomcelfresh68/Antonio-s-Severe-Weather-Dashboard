from __future__ import annotations

from typing import Any

import streamlit as st
from utils.resilience import request_json


HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/geo+json, application/json",
}


def _validate_point_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Unexpected NWS points payload type.")
    properties = payload.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("NWS points payload is missing properties.")
    return properties


@st.cache_data(ttl=1800, show_spinner=False)
def get_nws_point_properties_with_status(lat: float, lon: float, timeout: int = 8) -> tuple[dict[str, Any], dict[str, Any]]:
    properties, status = request_json(
        url=f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}",
        headers=HEADERS,
        endpoint="nws.points",
        source="NOAA/NWS points",
        timeout=timeout,
        cache_key=f"nws:points:{lat:.4f}:{lon:.4f}",
        validator=_validate_point_payload,
    )
    return properties, status


@st.cache_data(ttl=1800, show_spinner=False)
def get_nws_point_properties(lat: float, lon: float, timeout: int = 8) -> dict[str, Any]:
    properties, _status = get_nws_point_properties_with_status(lat, lon, timeout=timeout)
    return properties
