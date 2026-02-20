from datetime import datetime
import streamlit as st
from utils.home import svr_count_cached, tor_count_cached
from utils.tornado_warning_counter import fetch_tor_warning_count_ytd
from utils.severe_thunderstorm_warning_counter import fetch_svr_warning_count_ytd


def render():
    year = datetime.utcnow().year
    tor_count = tor_count_cached(year)
    svr_count = svr_count_cached(year)
    st.markdown("---")
    c1, c2 = st.columns(2, gap="large")
    c1.metric(f"Tornado Warnings (YTD {year})", tor_count)
    c2.metric(f"Severe TSTM Warnings (YTD {year})", svr_count)
    st.markdown("---")

   
    