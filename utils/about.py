import streamlit as st


def render() -> None:
    st.subheader("About This Dashboard")

    st.markdown(
        """
## Version

Antonio's Severe Weather Dashboard v3 is a modular Streamlit application
built for severe-weather situational awareness across the United States.

## Overview

The app consolidates official NOAA/NWS and SPC products into a single,
fast interface with shared location state and cached API workflows.

---

## Features

- Nationwide severe ticker with exact-event filtering:
  - Tornado Warning
  - Severe Thunderstorm Warning
  - Tornado Watch
  - Severe Thunderstorm Watch
- SPC Day 1-3 categorical and Day 4-7 probabilistic outlook imagery
- Location-based SPC hazard percentages
- Preset severe-weather city selection with optional device geolocation
- Nearest radar auto-selection via NWS points API
- Latest nearby NWS observations from the most complete station

---

## Technical Architecture

- Built with Streamlit
- Modular `utils/` architecture
- Cached NOAA/NWS API responses to reduce request load
- Conditional page rendering for performance
- Radar loops served from NWS RIDGE products
- Ticker marquee implemented with CSS animation and seamless looping

---

## Project Purpose

- Meteorology portfolio application
- Real-time severe weather situational awareness tool
- Demonstration of operational API integration and modular app design

---

## Roadmap

- Model Forecast page replacement
- Expanded statistics and historical summaries
- Additional observation layers
- Deployment hardening and release tooling
"""
    )

    st.markdown("---")
    st.caption(
        "This dashboard is for educational and informational purposes only. "
        "Use official NOAA/NWS products and local emergency management guidance for life-safety decisions."
    )
