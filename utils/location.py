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


def _apply_selected_preset() -> None:
    """Apply preset selection atomically via widget callback."""
    selection = st.session_state.get("location_preset_select")
    if selection not in CITY_PRESETS:
        return
    if selection == st.session_state.city_key:
        return
    lat, lon = CITY_PRESETS[selection]
    set_location(selection, lat, lon)


def sync_location_from_widget_state() -> None:
    """
    Sync session location from widget state early in a run so upstream fetches use one location.
    """
    if "location_preset_select" not in st.session_state:
        return
    _apply_selected_preset()


def render_location_controls() -> None:
    """Render shared location controls: preset list + device geolocation."""
    st.markdown("### Location")

    st.markdown(
        """
        <style>
        button[data-testid="stBaseButton-primary"] {
            border: 2px solid #ff2b2b !important;
            box-shadow: 0 0 7px rgba(255, 43, 43, 0.72), 0 0 18px rgba(255, 20, 20, 0.48) !important;
        }
        button[data-testid="stBaseButton-primary"]:hover {
            border-color: #ff4a4a !important;
            box-shadow: 0 0 10px rgba(255, 74, 74, 0.82), 0 0 22px rgba(255, 35, 35, 0.54) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    controls_col, _right_spacer = st.columns([2.1, 1.9], gap="small")
    preset_keys = list(CITY_PRESETS.keys())
    default_city = st.session_state.city_key if st.session_state.city_key in preset_keys else "Norman, OK"
    default_idx = preset_keys.index(default_city)

    with controls_col:
        preset_col, device_col = st.columns([1.25, 1], gap="small")
        with preset_col:
            st.selectbox(
                "Preset City",
                options=preset_keys,
                index=default_idx,
                key="location_preset_select",
                on_change=_apply_selected_preset,
            )
        with device_col:
            st.markdown("<div style='height: 1.78rem;'></div>", unsafe_allow_html=True)
            use_device = st.button(
                "Use location Device",
                use_container_width=True,
                key="location_device_btn",
                type="primary",
            )

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
                new_lat = float(lat)
                new_lon = float(lon)
                label = nearest_city_label(new_lat, new_lon)
                set_location(label, new_lat, new_lon)
                st.session_state.device_loc_pending = False
                st.rerun()

        st.info("Waiting for device location permission in your browser...")

    st.caption(
        f"Current: {st.session_state.city_key} ({float(st.session_state.lat):.4f}, {float(st.session_state.lon):.4f})"
    )
