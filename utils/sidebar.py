import streamlit as st
from utils.config import CITY_PRESETS
from utils.state import set_location

def location_sidebar() -> None:
    ## Create a sidebar in the Streamlit app for selecting a city from predefined presets. When a city is selected, the session state is updated with the corresponding latitude and longitude.

    st.sidebar.header("Select Location")
    
    preset_keys = list(CITY_PRESETS.keys())

    current_key = st.session_state.city_key
    default_index = preset_keys.index(current_key) if current_key in preset_keys else 0

    city_key = st.sidebar.selectbox("Choose a city:", options=preset_keys, index=default_index)

    preset_lat, preset_lon = CITY_PRESETS[city_key]

    st.sidebar.caption("Manually adjust coordinates if needed:")
    lat = st.sidebar.number_input("Latitude", value=float(st.session_state.lat), format="%.4f")
    lon = st.sidebar.number_input("Longitude", value=float(st.session_state.lon), format="%.4f")

    c1, c2 = st.sidebar.columns(2)

    if c1.button("Use preset coordinates"):
        set_location(city_key, preset_lat, preset_lon)
        st.rerun()
    if c2.button("Apply manual coordinates"):
        set_location(city_key, lat, lon)
        st.rerun()

    st.sidebar.divider()
    st.sidebar.write(f"Current selection: {city_key} (Lat: {lat:.4f}, Lon: {lon:.4f})")
    st.sidebar.write(f"({st.session_state.lat:.4f}, {st.session_state.lon:.4f})")
    
