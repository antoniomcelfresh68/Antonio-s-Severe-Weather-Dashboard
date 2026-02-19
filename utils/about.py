# utils/about.py

import streamlit as st

def render():
    st.subheader("About This Dashboard")

    st.markdown("""
    ## Overview

    This Severe Weather Dashboard is a modular Streamlit application designed 
    for real-time operational awareness of severe weather conditions.

    The objective of this project is to consolidate official NOAA / NWS data 
    into a clean, fast, and structured interface optimized for severe weather monitoring.

    ---

    ## Features

    - SPC Day 1–7 outlook visualization
    - Location-based SPC probability extraction
    - National Tornado & Severe Thunderstorm Warning counters (YTD)
    - Live NWS surface observations
    - Auto-detected nearest NWS radar (reflectivity + velocity)
    - Conditional page rendering for improved performance

    ---

    ## Technical Architecture

    - Built with Streamlit
    - Modular `utils/` page structure
    - Cached NOAA/NWS API responses
    - Optimized navigation (no redundant rerenders)
    - Radar served via NWS RIDGE products

    ---

    ## Project Purpose

    This dashboard serves as:
    - A meteorology portfolio application
    - A real-time severe weather situational awareness tool
    - A demonstration of API integration and modular app design

    ---

    ## Roadmap

    - Model Forecast page (HRRR / GFS)
    - Interactive radar
    - Device geolocation support
    - Mesonet integration
    """)

    st.markdown("---")
    st.caption(
        "This dashboard is for educational and informational purposes only. "
        "Always rely on official NOAA/NWS products for operational decisions."
    )
