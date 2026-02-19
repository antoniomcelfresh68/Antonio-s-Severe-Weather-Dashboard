# app.py

import streamlit as st
from utils.config import APP_TITLE
from utils.state import init_state
from utils.sidebar import location_sidebar
from utils.ui import apply_global_ui
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.spc import get_spc_point_summary
from utils.spc import get_spc_location_percents_cached as get_spc_location_percents
from utils.config import CITY_PRESETS
from utils.state import set_location
from datetime import datetime
import streamlit as st
from utils.tornado_warning_counter import fetch_tor_warning_count_ytd
from utils.severe_thunderstorm_warning_counter import fetch_svr_warning_count_ytd
import utils.home as home
from utils.observations import render as render_observations
import utils.about as about

apply_global_ui()  
init_state()

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

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
        v2.2.2
    </div>
    """,
    unsafe_allow_html=True
)

nav = st.radio(
    "",
    ["Home", "Observations", "Model Forecasts", "About"],
    horizontal=True,
    key="nav",
)

if nav == "Home":
    def spc_img(url: str) -> str:
        return f"{url}?v=1"
    home.render(
        spc_img=spc_img,
        CITY_PRESETS=CITY_PRESETS,
        set_location=set_location,
        get_spc_location_percents=get_spc_location_percents,
    )

elif nav == "Observations":
    render_observations(
        CITY_PRESETS=CITY_PRESETS,
        set_location=set_location,
    )

elif nav == "Model Forecasts":
    st.subheader("Model Forecasts")
    st.info("Coming soon: model data (HRRR, GFS) for your location.")

elif nav == "About":
    about.render(
    )
