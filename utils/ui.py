# utils/ui.py

import streamlit as st
from textwrap import dedent

def apply_global_ui() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
}
        /* gradient background */
        html, body, [data-testid="stAppViewContainer"] {
            height: 100%;
            background: linear-gradient(
    180deg,
    #0B0D12 0%,
    #1A1218 40%,
    #5A0E13 70%,
    #841617 100%
);

        }

        /* make main content area transparent so gradient shows */
        [data-testid="stAppViewContainer"] > .main {
            background: transparent;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        /* ---------- Center Tabs ---------- */

div[data-baseweb="tab-list"] {
    justify-content: center;
}

/* ---------- Make Tabs Bigger ---------- */

button[data-baseweb="tab"] {
    font-size: 1.15rem;
    padding: 0.75rem 1.5rem;
    margin: 0 0.75rem;
    font-weight: 600;
}

/* Active tab underline stronger */

button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom: 3px solid #841617;
}
/* ============================= */
/* Tornado Counter Metric Card  */
/* ============================= */

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #111317, #1c1416);
    padding: 10px;
    border-radius: 30px;
    border: 5px solid rgba(255, 100, 0, 0.15);
    box-shadow: 0 0 30px rgba(255, 0, 0, 0.08);
    transition: all 0.4s ease;
}

div[data-testid="stMetric"]:hover {
    border: 1px solid rgba(255, 60, 60, 0.6);
    box-shadow: 0 0 40px rgba(255, 0, 0, 0.18);
}

/* Label styling */
div[data-testid="stMetricLabel"] {
    font-size: 25px;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    opacity: 0.75;
}

/* Big number styling */
div[data-testid="stMetricValue"] {
    font-size: 42px;
    font-weight: 800;
    color: #ff3b3b;
}
/* ============================= */
/* Observations detail cards     */
/* ============================= */

.obs-card{
  border-radius: 30px;                 /* match your metric radius */
  padding: 22px 26px;
  background: linear-gradient(145deg, #111317, #1c1416);  /* match stMetric */
  border: 5px solid rgba(255, 100, 0, 0.15);             /* match stMetric */
  box-shadow: 0 0 30px rgba(255, 0, 0, 0.08);            /* match stMetric */
  transition: all 0.4s ease;
  min-height: 140px;
}

.obs-card:hover{
  border: 1px solid rgba(255, 60, 60, 0.6);
  box-shadow: 0 0 40px rgba(255, 0, 0, 0.18);
}

.obs-card-title{
  font-size: 22px;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  opacity: .75;
  font-weight: 600;
  margin-bottom: 12px;
}

.obs-card-value{
  font-size: 42px;
  font-weight: 800;
  color: #ff3b3b;     /* match metric number color */
  line-height: 1.1;
}

.obs-card-sub{
  margin-top: 10px;
  opacity: .80;
  font-size: 18px;
  font-weight: 600;
}
/* Small observation cards (top row: Temp/Dew/RH/SLP/Vis) */
.obs-card.small{
  min-height: 90px;
  padding: 18px 22px;
}
.obs-card.small .obs-card-title{
  font-size: 16px;
  margin-bottom: 10px;
}
.obs-card.small .obs-card-value{
  font-size: 34px;
}


        </style>
        """,
        unsafe_allow_html=True,
    )

def obs_card(title: str, value: str, subtitle: str | None = None) -> None:
    html = f"""
<div class="obs-card">
  <div class="obs-card-title">{title}</div>
  <div class="obs-card-value">{value}</div>
  {f'<div class="obs-card-sub">{subtitle}</div>' if subtitle else ''}
</div>
"""
    st.markdown(dedent(html), unsafe_allow_html=True)

def obs_small_card(title: str, value: str) -> None:
    html = f"""
<div class="obs-card small">
  <div class="obs-card-title">{title}</div>
  <div class="obs-card-value">{value}</div>
</div>
"""
    st.markdown(dedent(html), unsafe_allow_html=True)

