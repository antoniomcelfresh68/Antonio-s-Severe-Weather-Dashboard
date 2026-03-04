# utils/observations.py

import streamlit as st
import requests
from typing import Any, Dict, Optional, Tuple
import time
from datetime import datetime, timezone
import math
import re
from utils.ui import obs_card, obs_small_card
import streamlit.components.v1 as components
from utils.satelite import render_satellite_panel

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/geo+json, application/json",
}
SPC_MESO_BASE = "https://www.spc.noaa.gov/exper/mesoanalysis/new"
DEFAULT_MESO_SECTORS = [
    ("19", "Full CONUS Sector"),
    ("14", "Central Plains"),
    ("20", "Midwest"),
    ("21", "Great Lakes"),
    ("22", "Great Basin"),
    ("11", "Pac NW"),
    ("12", "Southwest"),
    ("13", "Northern Plains"),
    ("15", "Southern Plains"),
    ("16", "Northeast"),
    ("17", "Mid-Atlantic"),
    ("18", "Southeast"),
]
DEFAULT_MESO_PARAMETERS = [
    ("pmsl", "Mean Sea-Level Pressure"),
    ("sbcp", "Surface-Based CAPE"),
    ("mlcp", "Mixed-Layer CAPE"),
    ("mucp", "Most-Unstable CAPE"),
    ("dcape", "DCAPE"),
    ("srh1", "0-1 km SRH"),
    ("eshr", "Effective Shear"),
    ("lllr", "Low-Level Lapse Rates"),
]

def _get_nearest_radar_id(lat: float, lon: float) -> Optional[str]:
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


@st.cache_data(ttl=1800, show_spinner=False)
def _get_spc_meso_sector_options() -> list[tuple[str, str]]:
    try:
        response = requests.get(
            f"{SPC_MESO_BASE}/",
            headers={"User-Agent": HEADERS["User-Agent"], "Accept": "text/html, */*;q=0.8"},
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException:
        return DEFAULT_MESO_SECTORS

    matches = re.findall(r'<!--\s*([^>]+?)\s*-->\s*<area id="s(\d+)"', response.text)
    if not matches:
        return DEFAULT_MESO_SECTORS

    sectors = [("19", "Full CONUS Sector")]
    sectors.extend((sector_id, label.strip()) for label, sector_id in matches)
    return sectors


def _normalize_meso_param(selected_param: str) -> list[tuple[str, str]]:
    current = (selected_param or "pmsl").strip().lower() or "pmsl"
    params = list(DEFAULT_MESO_PARAMETERS)
    if all(code != current for code, _ in params):
        params.insert(0, (current, f"Custom ({current})"))
    return params


def _get_query_param(name: str, default: str) -> str:
    value = st.query_params.get(name, default)
    if isinstance(value, list):
        return value[0] if value else default
    return str(value)


def _set_meso_query_params(sector: str, parm: str) -> None:
    st.query_params["sector"] = sector
    st.query_params["parm"] = parm


def _build_spc_meso_url(sector: str, parm: str) -> str:
    return f"{SPC_MESO_BASE}/viewsector.php?sector={sector}&parm={parm}"

def _c_to_f(c: Optional[float]) -> Optional[float]:
    if c is None:
        return None
    return c * 9/5 + 32

def _ms_to_mph(ms: Optional[float]) -> Optional[float]:
    if ms is None:
        return None
    return ms * 2.236936

def _deg_to_compass(deg: Optional[float]) -> Optional[str]:
    if deg is None:
        return None
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    i = int((deg % 360) / 22.5 + 0.5) % 16
    return dirs[i]

def _fmt_num(x: Optional[float], suffix: str = "", digits: int = 0) -> str:
    if x is None:
        return "—"
    if digits == 0:
        return f"{int(round(x))}{suffix}"
    return f"{x:.{digits}f}{suffix}"


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        # NWS timestamps often end with Z
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def _get_nws_latest_obs_near_point(lat: float, lon: float) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Returns (obs_properties, station_id).
    Picks the best nearby station (most complete fields), not just features[0].
    """
    try:
        points = _get_json(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}")
        stations_url = _safe(points, "properties", "observationStations")
        if not stations_url:
            return None, None

        stations = _get_json(stations_url)
        features = stations.get("features", []) or []
        if not features:
            return None, None

        # Score stations by completeness + freshness; also prefer closer stations.
        want_fields = [
            ("temperature", "value"),
            ("dewpoint", "value"),
            ("relativeHumidity", "value"),
            ("windDirection", "value"),
            ("windSpeed", "value"),
            ("windGust", "value"),
            ("seaLevelPressure", "value"),
            ("visibility", "value"),
        ]

        best = None  # (score, dist_m, station_id, props)
        for feat in features[:10]:
            sid = _safe(feat, "properties", "stationIdentifier")
            if not sid:
                continue

            geom = feat.get("geometry") or {}
            coords = geom.get("coordinates") or None
            dist_m = None
            if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                st_lon, st_lat = coords[0], coords[1]
                dist_m = _haversine_m(lat, lon, st_lat, st_lon)

            latest_url = f"https://api.weather.gov/stations/{sid}/observations/latest"
            try:
                latest = _get_json(latest_url)
            except Exception:
                continue

            props = latest.get("properties") or {}
            if not props:
                continue

            # completeness score: count non-null values
            present = 0
            for k1, k2 in want_fields:
                v = _safe(props, k1, k2)
                if v is not None:
                    present += 1

            # freshness bonus: prefer newer obs
            ts = _parse_iso(props.get("timestamp"))
            age_min = None
            if ts is not None:
                age = datetime.now(timezone.utc) - ts.astimezone(timezone.utc)
                age_min = age.total_seconds() / 60.0

            score = present
            if age_min is not None:
                # small bonus if < 90 minutes old, penalty if very old
                if age_min <= 90:
                    score += 1
                elif age_min >= 240:
                    score -= 2

            # Prefer closer if scores tie
            tie_dist = dist_m if dist_m is not None else 9e18

            candidate = (score, tie_dist, sid, props)
            if best is None or score > best[0] or (score == best[0] and tie_dist < best[1]):
                best = candidate

        if not best:
            return None, None

        _, _, station_id, props = best
        return props, station_id

    except Exception:
        return None, None

@st.cache_data(ttl=120, show_spinner=False)
def get_location_temp_dew_f(lat: float, lon: float) -> Tuple[Optional[float], Optional[float]]:
    """
    Return latest temperature/dewpoint (degF) from the same NWS observation workflow
    used by the observations page.
    """
    temp_f, dew_f, _wind, _cond = get_location_glance(lat, lon)
    return temp_f, dew_f

@st.cache_data(ttl=120, show_spinner=False)
def get_location_wind_conditions(lat: float, lon: float) -> Tuple[str, str]:
    """
    Return compact wind (direction + speed) and current conditions text for a location.
    """
    _temp, _dew, wind_str, cond_str = get_location_glance(lat, lon)
    return wind_str, cond_str


@st.cache_data(ttl=120, show_spinner=False)
def get_location_glance(lat: float, lon: float) -> Tuple[Optional[float], Optional[float], str, str]:
    """
    Return temp/dew (degF) and compact wind/conditions from a single cached lookup.
    """
    obs, _ = _get_nws_latest_obs_near_point(lat, lon)
    if not obs:
        return None, None, "--", "--"

    temp_c = _safe(obs, "temperature", "value")
    dew_c = _safe(obs, "dewpoint", "value")
    temp_f = _c_to_f(temp_c)
    dew_f = _c_to_f(dew_c)

    wind_dir = _safe(obs, "windDirection", "value")
    wind_spd_ms = _safe(obs, "windSpeed", "value")
    wind_spd_mph = _ms_to_mph(wind_spd_ms)
    wd_card = _deg_to_compass(wind_dir)

    wind_str = "--"
    if wind_spd_mph is not None:
        if wind_dir is not None and wd_card is not None:
            wind_str = f"{wd_card} ({wind_dir:.0f} deg) {wind_spd_mph:.0f} mph"
        else:
            wind_str = f"{wind_spd_mph:.0f} mph"

    cond_str = (obs.get("textDescription") or "").strip() or "--"
    return temp_f, dew_f, wind_str, cond_str

def render_spc_mesoanalysis() -> None:
    sector_options = _get_spc_meso_sector_options()
    sector_ids = [sector_id for sector_id, _ in sector_options]
    sector_map = {sector_id: label for sector_id, label in sector_options}

    selected_sector = _get_query_param("sector", "19")
    if selected_sector not in sector_map:
        selected_sector = "19"

    selected_param = _get_query_param("parm", "pmsl").strip().lower() or "pmsl"
    parameter_options = _normalize_meso_param(selected_param)
    parameter_codes = [code for code, _ in parameter_options]
    parameter_labels = dict(parameter_options)

    controls = st.columns([1.4, 1.2, 1.6], gap="small")
    with controls[0]:
        selected_sector = st.selectbox(
            "SPC sector",
            options=sector_ids,
            index=sector_ids.index(selected_sector),
            format_func=lambda sector_id: sector_map.get(sector_id, sector_id),
            key="spc_meso_sector",
        )
    with controls[1]:
        selected_param = st.selectbox(
            "Field",
            options=parameter_codes,
            index=parameter_codes.index(selected_param),
            format_func=lambda code: parameter_labels.get(code, code),
            key="spc_meso_param",
        )
    with controls[2]:
        meso_url = _build_spc_meso_url(selected_sector, selected_param)
        _set_meso_query_params(selected_sector, selected_param)
        st.markdown("**Deep link**")
        st.caption(meso_url)

    components.iframe(meso_url, height=1000, scrolling=True)

def render():
    st.markdown(f" # Observations")
    render_spc_mesoanalysis()
    lat = float(st.session_state.lat)
    lon = float(st.session_state.lon)
    radar_id = _get_nearest_radar_id(lat, lon) or "KTLX"  # fallback for Oklahoma
#    Cache-bust once per minute so the gif actually updates in browsers/CDNs
    bust = int(time.time() // 60)
    st.markdown(f" # Radar for {st.session_state.city_key} ({radar_id})")
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown(f"**Base Reflectivity ({radar_id})**")
        st.image(
        f"https://radar.weather.gov/ridge/standard/{radar_id}_loop.gif?b={bust}",
        width='stretch',
    )

    with col2:
        st.markdown(f"**Base Velocity ({radar_id})**")
        st.image(
        f"https://radar.weather.gov/ridge/standard/base_velocity/{radar_id}_loop.gif?b={bust}",
        width='stretch',
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

    wd_card = _deg_to_compass(wind_dir)
    wind_str = "—"
    if wind_spd_mph is not None:
        if wind_dir is not None and wd_card is not None:
            wind_str = f"{wd_card} ({wind_dir:.0f}°) {wind_spd_mph:.0f} mph"
        else:
            wind_str = f"{wind_spd_mph:.0f} mph"

    gust_str = f"Gust {wind_gust_mph:.0f} mph" if wind_gust_mph is not None else None
    cond_str = desc or "—"

    st.markdown(f"# Latest near **{st.session_state.city_key}**")
    if station_id:
        st.markdown(f"NWS station: {station_id} • {obs_time if obs_time else ''}")
        st.caption("Note: Observations may be innacurate or incomplete")

    row = st.columns(5, gap="large")
    with row[0]:
        obs_small_card("Temp", _fmt_num(temp_f, "°F", 0))
    with row[1]:
        obs_small_card("Dewpoint", _fmt_num(dew_f, "°F", 0))
    with row[2]:
        obs_small_card("RH", _fmt_num(rh, "%", 0))
    with row[3]:
        obs_small_card("SLP", _fmt_num(slp_mb, " mb", 1))
    with row[4]:
        obs_small_card("Visibility", _fmt_num(vis_mi, " mi", 1))
    
    st.divider()

    c1, c2 = st.columns(2, gap="large")

    with c1:
        obs_card("💨 Wind", wind_str, gust_str)
    st.write("** Wind values are mostly innacurate for the time being **")
    with c2:
        obs_card("☁️ Conditions", cond_str)
    
    st.divider()
    render_satellite_panel()

   

    

    

    
