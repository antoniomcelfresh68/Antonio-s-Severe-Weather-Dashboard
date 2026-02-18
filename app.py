import streamlit as st
from utils.config import APP_TITLE
from utils.state import init_state
from utils.sidebar import location_sidebar
from utils.ui import apply_global_ui
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.spc import get_spc_point_summary
from utils.spc import get_spc_location_percents
from utils.config import CITY_PRESETS
from utils.state import set_location
from datetime import datetime
import streamlit as st
from utils.tornado_warning_counter import fetch_tor_warning_count_ytd

def spc_img(url: str) -> str:
    # cache-bust so it refreshes on reruns without you changing code
    return f"{url}?v=1"

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

## Initialize the session state to ensure all necessary variables are set before rendering the app. This function will set default values for the city and its coordinates if they are not already present in the session state.
apply_global_ui()  # Apply global UI customizations to hide Streamlit's default chrome and adjust spacing.
init_state()

st.markdown(
    f"""
    <h1 style='text-align: center; margin-bottom: 0.2em;'>
        {APP_TITLE}
    </h1>
    """,
    unsafe_allow_html=True
)
st.markdown(
    f"""
    <div style='text-align: center; color: #BBBBBB; font-size: 0.95rem;'>
        Current Location: {st.session_state.city_key}
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <div style='text-align: center; color: #888888; font-size: 0.85rem;'>
        Developed by Antonio McElfresh | GitHub: <a href="https://github.com/antoniomcelfresh68/Antonio-s-Severe-Weather-Dashboard" target="_blank">View on GitHub</a> | LinkedIn: <a href="https://www.linkedin.com/in/antonio-mcelfresh-632462309/" target="_blank">View Profile</a>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <div style='text-align: center; color: #666666; font-size: 0.8rem; margin-top: 0.3rem;'>
        v2.1.1
    </div>
    """,
    unsafe_allow_html=True
)



# =========================
# NATIONAL STATS BAR
# =========================

st.markdown("---")

col1, col2, col3 = st.columns([2, 1, 1])

year = datetime.utcnow().year

@st.cache_data(ttl=900)
def tor_count_cached(y):
    return fetch_tor_warning_count_ytd(year=y)

tor_count = tor_count_cached(year)

with col1:
    st.metric(
        label=f"U.S. Tornado Warning Counter (YTD {year})",
        value=tor_count
    )

with col2:
    st.empty()  # placeholder for future stat

with col3:
    st.empty()  # placeholder for future stat






tab_home, tab_observations, tab_models, tab_about = st.tabs(["Home", "Observations", "Model Forecasts", "About"])



with tab_home:
    st.subheader("SPC Outlooks (Day 1–7)")


    st.divider()

    # --- Images like v1.5 ---
    # Layout: Day 1-3 top row, Day 4-7 bottom row
    r1 = st.columns(3, gap="large")
    with r1[0]:
        st.markdown("**Day 1 Categorical**")
        st.image(spc_img("https://www.spc.noaa.gov/products/outlook/day1otlk.gif"), use_container_width=True)
    with r1[1]:
        st.markdown("**Day 2 Categorical**")
        st.image(spc_img("https://www.spc.noaa.gov/products/outlook/day2otlk.gif"), use_container_width=True)
    with r1[2]:
        st.markdown("**Day 3 Categorical**")
        st.image(spc_img("https://www.spc.noaa.gov/products/outlook/day3otlk.gif"), use_container_width=True)

    st.divider()

    r2 = st.columns(4, gap="large")
    with r2[0]:
        st.markdown("**Day 4 Probability**")
        st.image(spc_img("https://www.spc.noaa.gov/products/exper/day4-8/day4prob.gif"), use_container_width=True)
    with r2[1]:
        st.markdown("**Day 5 Probability**")
        st.image(spc_img("https://www.spc.noaa.gov/products/exper/day4-8/day5prob.gif"), use_container_width=True)
    with r2[2]:
        st.markdown("**Day 6 Probability**")
        st.image(spc_img("https://www.spc.noaa.gov/products/exper/day4-8/day6prob.gif"), use_container_width=True)
    with r2[3]:
        st.markdown("**Day 7 Probability**")
        st.image(spc_img("https://www.spc.noaa.gov/products/exper/day4-8/day7prob.gif"), use_container_width=True)

    st.caption("Images are official SPC products. Day 4–8 is the experimental/probabilistic suite (we’re showing Day 4–7).")

    # --------------------
    # Top-left location selector
    # --------------------
    preset_keys = list(CITY_PRESETS.keys())
    options = ["My Location"] + preset_keys
    # Default selection = current preset city (if it exists)
    default_option = st.session_state.city_key if st.session_state.city_key in preset_keys else preset_keys[0]
    default_index = options.index(default_option)
    left, _ = st.columns([1, 3], gap="large")

    nums = get_spc_location_percents(float(st.session_state.lat), float(st.session_state.lon))




    with left:
        selection = st.selectbox("Location", options, index=default_index)
    if selection == "My Location":
        st.info("Device location will be added soon. For now, pick a preset location.")
    else:
        # Only update if changed (prevents rerun loops)
        if selection != st.session_state.city_key:
            lat, lon = CITY_PRESETS[selection]
            set_location(selection, lat, lon)
            st.rerun()

    # --- SPC % at your location ---
    nums = get_spc_location_percents(
        float(st.session_state.lat),
        float(st.session_state.lon)
    )

    def fmt(x):
        return "0%" if x is None else f"{int(x)}%"

    st.markdown("### SPC % at your location")

    # Day 1
    r1 = st.columns(3)
    r1[0].metric("D1 TOR", fmt(nums.get("d1_tor")))
    r1[1].metric("D1 WIND", fmt(nums.get("d1_wind")))
    r1[2].metric("D1 HAIL", fmt(nums.get("d1_hail")))

    # Day 2
    r2 = st.columns(3)
    r2[0].metric("D2 TOR", fmt(nums.get("d2_tor")))
    r2[1].metric("D2 WIND", fmt(nums.get("d2_wind")))
    r2[2].metric("D2 HAIL", fmt(nums.get("d2_hail")))

    # Day 3 (probabilistic only)
    r3 = st.columns(3)
    r3[0].metric("D3 PROB", fmt(nums.get("d3_prob")))
    r3[1].empty()
    r3[2].empty()
with tab_observations:
    st.subheader("Observations")
    st.info("Coming soon: radar, satellite, and surface obs for your location.")
with tab_models:
    st.subheader("Model Forecasts")
    st.info("Coming soon: model data (HRRR, GFS) for your location.")
with tab_about:
    st.subheader("About This App")
    st.markdown(
        """
        This dashboard provides a comprehensive view of severe weather risks based on the latest SPC outlooks. It combines official SPC products with location-specific hazard percentages to help you stay informed about potential tornado, wind, and hail threats in your area.

        **Data Sources**:
        - All data is sourced from the [NOAA Storm Prediction Center](https://www.spc.noaa.gov/), ensuring you get accurate and up-to-date information.

        **Features**:
        - View official SPC outlook images for Days 1–7.
        - Get specific tornado, wind, and hail probabilities for your location.
        - Easily switch between preset cities to check different areas.

        **Developer**: Antonio McElfresh
        - GitHub: [View on GitHub](https://github.com/antoniomcelfresh/severe-dashboard-v2)
        - LinkedIn: [View Profile](https://www.linkedin.com/in/antonio-mcelfresh-632462309/)
        **Version**: 2.0.0
        """
    )