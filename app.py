# app.py

import streamlit as st
from utils.config import APP_TITLE
from utils.state import init_state
from utils.spc import get_spc_location_percents_cached as get_spc_location_percents
from utils.config import CITY_PRESETS
from utils.state import set_location
import utils.home as home
from utils.observations import render as render_observations
import utils.about as about
from utils.ui import apply_global_ui, render_global_hero
from utils.statistics import render as render_statistics

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

init_state()
apply_global_ui()
render_global_hero(
    image_path="assets/banner.jpg",
    title=APP_TITLE,
    location=st.session_state.city_key,
    version="v2.3.4",
)

nav = st.radio(
    "",
    ["Home", "Observations", "Model Forecasts", "Statistics", "About"],
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

elif nav == "Statistics":
    render_statistics()

elif nav == "About":
    about.render(
    )
