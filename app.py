# app.py

import streamlit as st
from utils.config import APP_TITLE
from utils.state import init_state
from utils.spc import get_spc_location_percents_cached as get_spc_location_percents
import utils.home as home
from utils.observations import (
    render as render_observations,
    get_location_glance,
)
import utils.about as about
from utils.ui import (
    apply_global_ui,
    render_global_hero,
    render_temp_dew_glance,
    render_wind_conditions_glance,
)
from utils.statistics import render as render_statistics
from utils.location import render_location_controls, sync_location_from_widget_state
from utils.ticker import render_severe_ticker
from utils.gallery import render_gallery
from utils.nws_alerts import get_severe_alerts

st.set_page_config(page_title=APP_TITLE, page_icon="assets/tornado-cartoon-animation-clip-art-tornado.jpg", layout="wide", initial_sidebar_state="expanded")

init_state()
apply_global_ui()

if "simulate_outbreak_mode" not in st.session_state:
    st.session_state.simulate_outbreak_mode = False
if "simulate_outbreak_scenario" not in st.session_state:
    st.session_state.simulate_outbreak_scenario = "Static"
if "mock_alert_step" not in st.session_state:
    st.session_state.mock_alert_step = 0

if st.session_state.simulate_outbreak_mode:
    scenario_mode = "dynamic" if st.session_state.simulate_outbreak_scenario == "Dynamic" else "static"
    simulated_alerts = get_severe_alerts(source="mock", mode=scenario_mode)
    render_severe_ticker(alerts=simulated_alerts)
else:
    render_severe_ticker()

sync_location_from_widget_state()

top_left, top_center, top_right_spacer = st.columns([1.2, 3.6, 1.2], gap="large")

with top_left:
    temp_f, dew_f, wind_text, conditions_text = get_location_glance(
        float(st.session_state.lat),
        float(st.session_state.lon),
    )
    render_temp_dew_glance(
        st.session_state.city_key,
        temp_f,
        dew_f,
        float(st.session_state.lat),
        float(st.session_state.lon),
    )
    render_wind_conditions_glance(wind_text, conditions_text)

with top_center:
    render_global_hero(
        image_path="assets/banner.jpg",
        title=APP_TITLE,
        location=st.session_state.city_key,
        version="v3.0.3",
        logo_path="assets/logo.png",
    )

render_location_controls()

nav = st.radio(
    "Navigation",
    ["Home", "Observations", "Model Forecasts", "Statistics", "Photo Gallery", "About"],
    horizontal=True,
    key="nav",
)

if nav == "Home":
    def spc_img(url: str) -> str:
        return f"{url}?v=1"
    home.render(
        spc_img=spc_img,
        get_spc_location_percents=get_spc_location_percents,
    )

elif nav == "Observations":
    render_observations()

elif nav == "Model Forecasts":
    st.subheader("Model Forecasts")
    st.info("Coming soon: model data (HRRR, GFS) for your location.")

elif nav == "Statistics":
    render_statistics()

elif nav == "Photo Gallery":
    render_gallery()

elif nav == "About":
    about.render(
    )
