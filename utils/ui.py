# utils/ui.py

from typing import Optional
import streamlit as st
from textwrap import dedent
import base64

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
            max-width: 1350px;          /* controls fixed page width */
            margin: 0 auto;             /* centers the app */
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
            img {
        max-width: 100% !important;
        height: auto !important;
    }

iframe {
    width: 100% !important;
    max-width: 100% !important;
    border: none !important;
    overflow: hidden !important;
}
.block-container {
    overflow-x: hidden;
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
/* Fade bottom of hero image */
.hero-wrap img {
    -webkit-mask-image: linear-gradient(
        to bottom,
        rgba(0,0,0,1) 0%,
        rgba(0,0,0,1) 75%,
        rgba(0,0,0,0) 100%
    );
    mask-image: linear-gradient(
        to bottom,
        rgba(0,0,0,1) 0%,
        rgba(0,0,0,1) 75%,
        rgba(0,0,0,0) 100%
    );
}


        </style>
        """,
        unsafe_allow_html=True,
    )

def obs_card(title: str, value: str, subtitle: Optional[str] = None) -> None:
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

def render_global_hero(image_path: str, title: str, location: str, version: str) -> None:
    import base64
    import streamlit as st

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    st.markdown(
        f"""
        <style>
        .hero-wrap {{
            position: relative;
            width: 100%;
            height: 320px;
            border-radius: 22px;
            overflow: hidden;
            box-shadow: 0 0 60px rgba(0,0,0,0.35);
        }}

        /* NOTE: fade/mask lives in apply_global_ui() now */
        .hero-wrap img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
        }}

        .hero-overlay {{
            position: absolute;
            inset: 0;
            background:
              radial-gradient(ellipse at center, rgba(0,0,0,0.10), rgba(0,0,0,0.60)),
              linear-gradient(180deg, rgba(0,0,0,0.10) 0%, rgba(0,0,0,0.45) 60%, rgba(132,22,23,0.30) 100%);
        }}

        .hero-text {{
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 0 1.5rem;
            z-index: 5;
            color: rgba(255,255,255,0.95);
        }}

        .hero-text h1 {{
            margin: 0;
            font-size: 3.0rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            text-shadow: 0 8px 30px rgba(0,0,0,0.55);
        }}

        .hero-text .loc {{
            margin-top: 0.7rem;
            font-size: 1.0rem;
            opacity: 0.92;
        }}

        .hero-text .links {{
            margin-top: 0.35rem;
            font-size: 0.88rem;
            opacity: 0.85;
        }}

        .hero-text .links a {{
            color: rgba(255,255,255,0.92);
            text-decoration: underline;
        }}

        .hero-text .links a:hover {{
            color: rgba(255,255,255,1.0);
        }}

        .hero-text .ver {{
            margin-top: 0.25rem;
            font-size: 0.82rem;
            opacity: 0.70;
        }}
        </style>

        <div class="hero-wrap">
          <img src="data:image/jpeg;base64,{encoded}" />
          <div class="hero-overlay"></div>
          <div class="hero-text">
            <div>
              <h1>{title}</h1>
              <div class="loc">Current Location: {location}</div>
              <div class="links">
                Developed by Antonio McElfresh |
                GitHub: <a href="https://github.com/antoniomcelfresh68/Antonio-s-Severe-Weather-Dashboard" target="_blank">View on GitHub</a> |
                LinkedIn: <a href="https://www.linkedin.com/in/antonio-mcelfresh-632462309/" target="_blank">View Profile</a>
              </div>
              <div class="ver">{version}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
