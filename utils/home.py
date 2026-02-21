# util/home.py

import streamlit as st
from utils.tornado_warning_counter import fetch_tor_warning_count_ytd
from utils.severe_thunderstorm_warning_counter import fetch_svr_warning_count_ytd

@st.cache_data(ttl=900)
def tor_count_cached(y):
    return fetch_tor_warning_count_ytd(year=y)

@st.cache_data(ttl=900)
def svr_count_cached(y):
    return fetch_svr_warning_count_ytd(year=y)

def render(
    spc_img,
    CITY_PRESETS,
    set_location,
    get_spc_location_percents,
):
    
    st.markdown(" # SPC Convective Outlooks")
    

    # --- Images like v1.5 ---
    # Layout: Day 1-3 top row, Day 4-7 bottom row
    row1 = st.columns(3, gap="small")
    with row1[0]:
        st.markdown("**Day 1 Categorical**")
        st.image(spc_img("https://www.spc.noaa.gov/products/outlook/day1otlk.gif"), use_container_width=True)
    with row1[1]:
        st.markdown("**Day 2 Categorical**")
        st.image(spc_img("https://www.spc.noaa.gov/products/outlook/day2otlk.gif"), use_container_width=True)
    with row1[2]:
        st.markdown("**Day 3 Categorical**")
        st.image(spc_img("https://www.spc.noaa.gov/products/outlook/day3otlk.gif"), use_container_width=True)

    st.divider()

    row2 = st.columns(4, gap="small")
    with row2[0]:
        st.markdown("**Day 4 Probability**")
        st.image(spc_img("https://www.spc.noaa.gov/products/exper/day4-8/day4prob.gif"), use_container_width=True)
    with row2[1]:
        st.markdown("**Day 5 Probability**")
        st.image(spc_img("https://www.spc.noaa.gov/products/exper/day4-8/day5prob.gif"), use_container_width=True)
    with row2[2]:
        st.markdown("**Day 6 Probability**")
        st.image(spc_img("https://www.spc.noaa.gov/products/exper/day4-8/day6prob.gif"), use_container_width=True)
    with row2[3]:
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
    
    def _on_home_location_change():
        sel = st.session_state.home_location_select
        if sel == "My Location":
            return
        lat, lon = CITY_PRESETS[sel]
        set_location(sel, lat, lon)

    left, _ = st.columns([1, 3], gap="large")
    with left:
        st.selectbox(
            "Location",
            options,
            index=default_index,
            key="home_location_select",
            on_change=_on_home_location_change,
    )

    if st.session_state.home_location_select == "My Location":
        st.info("Device location will be added soon. For now, pick a preset location.")


    # --- SPC % at your location ---
    nums = get_spc_location_percents(
        float(st.session_state.lat),
        float(st.session_state.lon)
    )

    def fmt(x):
        return "0%" if x is None else f"{int(x)}%"

    st.markdown(f"# SPC % for {st.session_state.city_key}")

    # Day 1
    m1 = st.columns(3)
    m1[0].metric("D1 TOR", fmt(nums.get("d1_tor")))
    m1[1].metric("D1 WIND", fmt(nums.get("d1_wind")))
    m1[2].metric("D1 HAIL", fmt(nums.get("d1_hail")))

    # Day 2
    m2 = st.columns(3)
    m2[0].metric("D2 TOR", fmt(nums.get("d2_tor")))
    m2[1].metric("D2 WIND", fmt(nums.get("d2_wind")))
    m2[2].metric("D2 HAIL", fmt(nums.get("d2_hail")))

    # Day 3 (probabilistic only)
    m3 = st.columns(3)
    m3[0].metric("D3 PROB", fmt(nums.get("d3_prob")))
    m3[1].empty()
    m3[2].empty()
