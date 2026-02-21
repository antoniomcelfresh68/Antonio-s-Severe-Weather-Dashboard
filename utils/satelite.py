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
}

GOES_PRODUCTS: Dict[str, str] = {
    "GeoColor": "GEOCOLOR",
    "Clean IR (B13)": "CLEANIR",
    "Water Vapor (WV)": "WV",
}

@st.cache_data(ttl=60)
def _latest_url(sat_label: str, sector_label: str, product_label: str) -> str:
    sat = GOES_SATS[sat_label]
    sector = GOES_SECTORS[sector_label]
    product = GOES_PRODUCTS[product_label]
    return f"{GOES_BASE}/{sat}/ABI/{sector}/{product}/latest.jpg"

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
        st.image(url, use_container_width=True)
        st.caption(f"{sat_choice} • {sector_choice} • {product_choice}")
    else:
        st.warning("Satellite endpoint didn’t respond. Hit Refresh or switch product/sector.")