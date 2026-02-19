# utils/observations.py
import streamlit as st
import requests
from typing import Any, Dict, Optional, Tuple
import time


HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/geo+json, application/json",
}

def _get_nearest_radar_id(lat: float, lon: float) -> str | None:
    """
    Uses api.weather.gov points endpoint; returns radarStation like 'KTLX' when available.
    """
    try:
        points = _get_json(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}")
        return _safe(points, "properties", "radarStation")
    except Exception:
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _get_json(url: str, timeout: int = 20) -> Dict[str, Any]:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _safe(d: Dict[str, Any], *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _c_to_f(c: Optional[float]) -> Optional[float]:
    if c is None:
        return None
    return c * 9/5 + 32

def _ms_to_mph(ms: Optional[float]) -> Optional[float]:
    if ms is None:
        return None
    return ms * 2.236936

def _fmt_num(x: Optional[float], suffix: str = "", digits: int = 0) -> str:
    if x is None:
        return "—"
    if digits == 0:
        return f"{int(round(x))}{suffix}"
    return f"{x:.{digits}f}{suffix}"

def _fmt_wind(dir_deg: Optional[float], spd_mph: Optional[float], gust_mph: Optional[float]) -> str:
    if spd_mph is None and gust_mph is None:
        return "—"
    d = "—" if dir_deg is None else f"{int(round(dir_deg))}°"
    s = "—" if spd_mph is None else f"{int(round(spd_mph))} mph"
    if gust_mph is not None and gust_mph > 0:
        return f"{d} @ {s} (gust {int(round(gust_mph))})"
    return f"{d} @ {s}"

def _get_nws_latest_obs_near_point(lat: float, lon: float) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Returns (obs_properties, station_id). Uses api.weather.gov points -> observationStations -> first station -> observations/latest
    """
    try:
        points = _get_json(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}")
        stations_url = _safe(points, "properties", "observationStations")
        if not stations_url:
            return None, None

        stations = _get_json(stations_url)
        features = stations.get("features", [])
        if not features:
            return None, None

        first_station = features[0]
        station_id = _safe(first_station, "properties", "stationIdentifier")

        latest_url = _safe(first_station, "properties", "stationObservations")
        if not latest_url:
            # fallback if stationObservations missing for some reason
            if station_id:
                latest_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"

        latest = _get_json(latest_url)
        props = latest.get("properties", {})
        return props, station_id
    except Exception:
        return None, None

def render(CITY_PRESETS, set_location):
    st.header("Observations")

    
    
    # --------------------
    # Location selector (same pattern as Home)
    # --------------------
    preset_keys = list(CITY_PRESETS.keys())
    options = preset_keys  # keep it simple here (no device location yet)

    # default selection
    default_city = st.session_state.city_key if st.session_state.city_key in preset_keys else preset_keys[0]
    default_index = options.index(default_city)

    left, right = st.columns([1, 3], gap="large")
    with left:
        selection = st.selectbox("Location", options, index=default_index, key="obs_location_select")

    if selection != st.session_state.city_key:
        lat, lon = CITY_PRESETS[selection]
        set_location(selection, lat, lon)
        st.rerun()

    # current point
    lat = float(st.session_state.lat)
    lon = float(st.session_state.lon)

    st.subheader("Radar")

    radar_id = _get_nearest_radar_id(lat, lon) or "KTLX"  # fallback for Oklahoma
#    Cache-bust once per minute so the gif actually updates in browsers/CDNs
    bust = int(time.time() // 60)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(f"**Base Reflectivity ({radar_id})**")
        st.image(
        f"https://radar.weather.gov/ridge/standard/{radar_id}_loop.gif?b={bust}",
        use_container_width=True,
    )

    with col2:
        st.markdown(f"**Base Velocity ({radar_id})**")
        st.image(
        f"https://radar.weather.gov/ridge/standard/base_velocity/{radar_id}_loop.gif?b={bust}",
        use_container_width=True,
    )

    st.caption("Radar imagery: NOAA/NWS RIDGE (loop GIFs).")


    # --------------------
    # Pull latest NWS observation
    # --------------------
    obs, station_id = _get_nws_latest_obs_near_point(lat, lon)

    if not obs:
        st.error("Could not load latest observations from NWS for this location.")
        st.stop()

    # Extract core fields (NWS uses SI units in many fields)
    temp_c = _safe(obs, "temperature", "value")
    dew_c  = _safe(obs, "dewpoint", "value")

    wind_dir = _safe(obs, "windDirection", "value")
    wind_spd_ms = _safe(obs, "windSpeed", "value")
    wind_gust_ms = _safe(obs, "windGust", "value")

    slp_pa = _safe(obs, "seaLevelPressure", "value")  # Pa
    vis_m  = _safe(obs, "visibility", "value")        # m
    rh     = _safe(obs, "relativeHumidity", "value")  # %

    desc = obs.get("textDescription")
    obs_time = obs.get("timestamp")


    temp_f = _c_to_f(temp_c)
    dew_f = _c_to_f(dew_c)
    wind_spd_mph = _ms_to_mph(wind_spd_ms)
    wind_gust_mph = _ms_to_mph(wind_gust_ms)

    slp_mb = None if slp_pa is None else slp_pa / 100.0
    vis_mi = None if vis_m is None else vis_m / 1609.344

    st.markdown(f"### Latest near **{st.session_state.city_key}**")
    if station_id:
        st.caption(f"NWS station: {station_id} • {obs_time if obs_time else ''}")


    # Metrics row
    c1, c2, c3, c4, c5 = st.columns(5, gap="large")
    c1.metric("Temp", _fmt_num(temp_f, "°F", 0))
    c2.metric("Dewpoint", _fmt_num(dew_f, "°F", 0))
    c3.metric("RH", _fmt_num(rh, "%", 0))
    c4.metric("SLP", _fmt_num(slp_mb, " mb", 1))
    c5.metric("Visibility", _fmt_num(vis_mi, " mi", 1))

    st.write("**Wind:**", _fmt_wind(wind_dir, wind_spd_mph, wind_gust_mph))
    if desc:
        st.info(desc)

    st.divider()

    
    
