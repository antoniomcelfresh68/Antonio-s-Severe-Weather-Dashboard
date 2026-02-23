import requests
import streamlit as st

from utils.config import CITY_PRESETS
from utils.state import set_location

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/json",
}


@st.cache_data(ttl=1800, show_spinner=False)
def nearest_city_label(lat: float, lon: float) -> str:
    """Resolve nearest city/town label via NWS points metadata."""
    try:
        r = requests.get(
            f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}",
            headers=HEADERS,
            timeout=20,
        )
        r.raise_for_status()
        props = (r.json() or {}).get("properties", {})
        rel = (props.get("relativeLocation") or {}).get("properties", {})
        city = rel.get("city")
        state = rel.get("state")
        if city and state:
            return f"{city}, {state}"
    except Exception:
        pass
    return f"{lat:.3f}, {lon:.3f}"


def render_location_controls() -> None:
    """Render shared location controls: preset list + device geolocation."""
    st.markdown("### Location")
    st.caption("Pick a preset severe-weather city for a broad U.S. picture, or use your device location.")

    select_col, device_col = st.columns([3, 1], gap="small")
    preset_keys = list(CITY_PRESETS.keys())
    default_city = st.session_state.city_key if st.session_state.city_key in preset_keys else "Norman, OK"
    default_idx = preset_keys.index(default_city)

    with select_col:
        selection = st.selectbox(
            "Preset City",
            options=preset_keys,
            index=default_idx,
            key="location_preset_select",
        )
    with device_col:
        use_device = st.button("Use Device", use_container_width=True, key="location_device_btn")

    if selection != st.session_state.city_key:
        lat, lon = CITY_PRESETS[selection]
        set_location(selection, lat, lon)
        st.rerun()

    if use_device:
        st.session_state.device_loc_nonce = st.session_state.get("device_loc_nonce", 0) + 1
        st.session_state.device_loc_pending = True

    if st.session_state.get("device_loc_pending", False):
        try:
            from streamlit_js_eval import get_geolocation
        except Exception as exc:
            st.error("Device geolocation dependency is unavailable.")
            st.exception(exc)
            st.session_state.device_loc_pending = False
            return

        nonce = st.session_state.get("device_loc_nonce", 0)
        geo = get_geolocation(component_key=f"device_geolocation_{nonce}")
        if isinstance(geo, dict) and isinstance(geo.get("coords"), dict):
            coords = geo["coords"]
            lat = coords.get("latitude")
            lon = coords.get("longitude")
            if lat is not None and lon is not None:
                label = nearest_city_label(float(lat), float(lon))
                set_location(label, float(lat), float(lon))
                st.session_state.device_loc_pending = False
                st.rerun()

        st.info("Waiting for device location permission in your browser...")

    st.caption(
        f"Current: {st.session_state.city_key} ({float(st.session_state.lat):.4f}, {float(st.session_state.lon):.4f})"
    )
