# app.py

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
import logging
import time

import streamlit as st
from utils.config import APP_TITLE
from utils.state import init_state
from utils.spc import (
    get_spc_location_percents_cached as get_spc_location_percents,
    get_spc_location_percents_with_status,
)
from utils.observations import (
    get_location_glance,
)
from utils.assistant import render_assistant_launcher, render_assistant_modal
from utils.ai_context import set_current_ai_page, update_page_ai_context
from utils.ui import (
    apply_global_ui,
    build_spc_day1_summary_glance_panel,
    build_statistics_glance_panel,
    build_temp_dew_glance_panel,
    mount_glance_clock,
    render_data_status,
    render_disclaimer_footer,
    render_global_hero,
    render_info_box_stack,
    render_nav_cards,
    summarize_freshness,
)
from utils.location import render_location_controls, sync_location_from_widget_state
from utils.ticker import render_severe_ticker
from utils.nws_alerts import get_severe_alerts
from utils.home import get_warning_counts_bundle


LOGGER = logging.getLogger(__name__)
PAGE_RENDER_START = time.perf_counter()


def _load_top_of_page_data(lat: float, lon: float, year: int) -> tuple[
    dict,
    dict,
    dict,
]:
    start_time = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as executor:
        glance_future = executor.submit(get_location_glance, lat, lon)
        counts_future = executor.submit(get_warning_counts_bundle, year)
        spc_future = executor.submit(get_spc_location_percents_with_status, lat, lon)

    try:
        temp_f, dew_f, wind_text, conditions_text = glance_future.result()
        observation_bundle = {
            "temp_f": temp_f,
            "dew_f": dew_f,
            "wind_text": wind_text,
            "conditions_text": conditions_text,
            "status": {
                "status": "live" if temp_f is not None or dew_f is not None else "unavailable",
                "checked_at": datetime.now(UTC).isoformat(),
                "summary": "Nearby observation snapshot." if temp_f is not None or dew_f is not None else "Nearby observations are unavailable right now.",
            },
        }
    except Exception:
        observation_bundle = {
            "temp_f": None,
            "dew_f": None,
            "wind_text": "--",
            "conditions_text": "--",
            "status": {
                "status": "unavailable",
                "checked_at": datetime.now(UTC).isoformat(),
                "summary": "Nearby observations are unavailable right now.",
            },
        }

    try:
        counts, counts_status = counts_future.result()
    except Exception:
        counts = {"tornado": "Unavailable", "severe": "Unavailable"}
        counts_status = {"status": "unavailable", "summary": "Warning-count services are unavailable right now."}

    try:
        spc_summary, spc_status = spc_future.result()
    except Exception:
        spc_summary, spc_status = {}, {"status": "unavailable", "summary": "SPC point summary is unavailable right now."}

    LOGGER.info("home_top_data_loaded latency_ms=%.1f", (time.perf_counter() - start_time) * 1000)
    return observation_bundle, {"counts": counts, "status": counts_status}, {"summary": spc_summary, "status": spc_status}

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

top_left, top_center, top_right = st.columns([1.2, 3.6, 1.2], gap="large")

current_year = datetime.now(UTC).year
lat = float(st.session_state.lat)
lon = float(st.session_state.lon)
observation_bundle, counts_bundle, spc_bundle = _load_top_of_page_data(
    lat,
    lon,
    current_year,
)
temp_f = observation_bundle["temp_f"]
dew_f = observation_bundle["dew_f"]
_wind_text = observation_bundle["wind_text"]
_conditions_text = observation_bundle["conditions_text"]
tor_count = counts_bundle["counts"]["tornado"]
svr_count = counts_bundle["counts"]["severe"]
day1_summary = spc_bundle["summary"]

update_page_ai_context(
    "Home",
    spc_summary={
        "day1_category": day1_summary.get("day1_cat"),
        "day1_tornado_percent": day1_summary.get("d1_tor"),
        "day1_wind_percent": day1_summary.get("d1_wind"),
        "day1_hail_percent": day1_summary.get("d1_hail"),
    },
    local_hazard_percentages={
        "tornado_percent": day1_summary.get("d1_tor"),
        "wind_percent": day1_summary.get("d1_wind"),
        "hail_percent": day1_summary.get("d1_hail"),
    },
    latest_observation={
        "temperature_f": temp_f,
        "dewpoint_f": dew_f,
        "wind": _wind_text,
        "conditions": _conditions_text,
    },
)

with top_left:
    temp_panel_html, local_id, zulu_id, tz_name = build_temp_dew_glance_panel(
        st.session_state.city_key,
        temp_f,
        dew_f,
        lat,
        lon,
        footer_note=summarize_freshness(observation_bundle.get("status"), fallback="Observation freshness unavailable."),
    )
    stats_panel_html = build_statistics_glance_panel(
        current_year,
        tor_count,
        svr_count,
        footer_note=summarize_freshness(counts_bundle.get("status"), fallback="Warning-count freshness unavailable."),
    )
    day1_panel_html = build_spc_day1_summary_glance_panel(
        st.session_state.city_key,
        day1_summary.get("d1_tor"),
        day1_summary.get("d1_wind"),
        day1_summary.get("d1_hail"),
        footer_note=summarize_freshness(spc_bundle.get("status"), fallback="SPC freshness unavailable."),
    )
    render_info_box_stack([
        temp_panel_html,
        stats_panel_html,
        day1_panel_html,
    ])
    mount_glance_clock(local_id, zulu_id, tz_name)
    render_data_status(observation_bundle.get("status"), label="Observations")
    render_data_status(counts_bundle.get("status"), label="Warning counts")
    render_data_status(spc_bundle.get("status"), label="SPC point summary")

with top_center:
    render_global_hero(
        image_path="assets/banner.jpg",
        title=APP_TITLE,
        location=st.session_state.city_key,
        version="v4.2.3",
        logo_path="assets/logo.png",
    )

with top_right:
    render_assistant_launcher()

render_location_controls()

nav = render_nav_cards(
    [
        "Home",
        "Observations",
        (f"Forecast for {st.session_state.city_key}", "Forecast"),
        "Photo Gallery",
        "About",
    ],
    key="nav",
)

if nav == "Home":
    set_current_ai_page("Home")
    import utils.home as home

    home.render(get_spc_location_percents=get_spc_location_percents)

elif nav == "Observations":
    set_current_ai_page("Observations")
    from utils.observations import render as render_observations

    render_observations()

elif nav == "Forecast":
    set_current_ai_page("Forecast")
    from utils.forecast import render as render_forecast

    render_forecast()

elif nav == "Photo Gallery":
    set_current_ai_page("Photo Gallery")
    from utils.gallery import render_gallery

    render_gallery()

elif nav == "About":
    set_current_ai_page("About")
    import utils.about as about

    about.render(
    )

render_assistant_modal()
render_disclaimer_footer()
LOGGER.info(
    "page_render_complete page=%s location=%s latency_ms=%.1f",
    nav,
    st.session_state.city_key,
    (time.perf_counter() - PAGE_RENDER_START) * 1000,
)
