# utils/satellite.py

from __future__ import annotations
from typing import Dict
import requests
import streamlit as st

GOES_BASE = "https://cdn.star.nesdis.noaa.gov"

GOES_SATS: Dict[str, str] = {
    "GOES-East (16)": "GOES16",
    "GOES-West (18)": "GOES18",
}

GOES_SECTORS: Dict[str, str] = {
    "CONUS": "CONUS",
    "Full Disk": "FD",
    "Mesoscale 1 (M1)": "M1",
    "Mesoscale 2 (M2)": "M2",
}

GOES_PRODUCTS: Dict[str, str] = {
    "GeoColor": "GEOCOLOR",
    "Air Mass RGB": "AIRMASS",
    "Clean IR (B13)": "CLEANIR",
    "Water Vapor (WV)": "WV",
    "Blue Visible (B01)": "BAND01",
    "Red Visible (B02)": "BAND02",
    "Veggie Near-IR (B03)": "BAND03",
    "Cirrus (B04)": "BAND04",
    "Snow/Ice (B05)": "BAND05",
    "Cloud Particle Size (B06)": "BAND06",
    "Shortwave Window (B07)": "BAND07",
    "Upper-Level WV (B08)": "BAND08",
    "Mid-Level WV (B09)": "BAND09",
    "Low-Level WV (B10)": "BAND10",
    "Cloud-Top Phase (B11)": "BAND11",
    "Ozone (B12)": "BAND12",
    "IR Window (B13)": "BAND13",
    "IR Longwave (B14)": "BAND14",
    "Dirty IR Window (B15)": "BAND15",
    "CO2 Longwave IR (B16)": "BAND16",
    "Day Cloud Phase RGB": "DAYCLOUDPHASE",
    "Nighttime Microphysics RGB": "NTMIC",
    "Dust RGB": "DUST",
    "SO2 RGB": "SO2",
    "Fire Temperature RGB": "FIRETEMP",
}

@st.cache_data(ttl=60)
def _latest_url(sat_label: str, sector_label: str, product_label: str) -> str:
    sat = GOES_SATS[sat_label]
    sector = GOES_SECTORS[sector_label]
    product = GOES_PRODUCTS[product_label]
    return f"{GOES_BASE}/{sat}/ABI/{sector}/{product}/latest.jpg"

@st.cache_data(ttl=60)
def _url_ok(url: str, timeout: int = 10) -> bool:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
    except requests.RequestException:
        return False

def render_satellite_panel() -> None:
    st.subheader("Satellite (GOES)")

    c1, c2, c3 = st.columns(3)
    with c1:
        sat_choice = st.selectbox("Satellite", list(GOES_SATS.keys()), index=0)
    with c2:
        sector_choice = st.selectbox("Sector", list(GOES_SECTORS.keys()), index=0)
    with c3:
        product_choice = st.selectbox("Product", list(GOES_PRODUCTS.keys()), index=0)

    refresh = st.button("Refresh satellite")
    if refresh:
        st.cache_data.clear()

    url = _latest_url(sat_choice, sector_choice, product_choice)

    if _url_ok(url):
        st.image(url, width='stretch')
        st.caption(f"{sat_choice} • {sector_choice} • {product_choice}")
    else:
        st.warning("Satellite endpoint didn’t respond. Hit Refresh or switch product/sector.")
