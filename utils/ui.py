# utils/ui.py

from typing import Optional
import streamlit as st
from textwrap import dedent
import base64
import os

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
        header[data-testid="stHeader"] {
            display: block;
            background: rgba(7, 13, 22, 0.95);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        div[data-testid="stToolbar"] {
            background: transparent;
        }
        div[data-testid="stDecoration"] {
            background: rgba(7, 13, 22, 0.95);
        }
        [data-testid="stAppViewContainer"] > .main {padding-top: 3.2rem;}
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

def render_global_hero(
    image_path: str,
    title: str,
    location: str,
    version: str,
    logo_path: Optional[str] = None,
) -> None:

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    logo_html = ""
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_encoded = base64.b64encode(f.read()).decode("utf-8")
        logo_html = (
            f'<img class="hero-logo" src="data:image/png;base64,{logo_encoded}" '
            f'alt="{title} logo" />'
        )

    st.markdown(
        f"""
        <style>
        /* Paint the hero image behind upper page content, then fade it out */
        .block-container {{
            position: relative;
            isolation: isolate;
        }}

        .block-container::before {{
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            top: 0;
            height: 1050px;
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-position: center top;
            background-size: cover;
            background-repeat: no-repeat;
            opacity: 0.42;
            pointer-events: none;
            z-index: 0;
            -webkit-mask-image: linear-gradient(
                to bottom,
                rgba(0,0,0,0.95) 0%,
                rgba(0,0,0,0.75) 45%,
                rgba(0,0,0,0.28) 78%,
                rgba(0,0,0,0) 100%
            );
            mask-image: linear-gradient(
                to bottom,
                rgba(0,0,0,0.95) 0%,
                rgba(0,0,0,0.75) 45%,
                rgba(0,0,0,0.28) 78%,
                rgba(0,0,0,0) 100%
            );
        }}

        .block-container > * {{
            position: relative;
            z-index: 1;
        }}

        .hero-wrap {{
            position: relative;
            width: 100%;
            height: 320px;
            overflow: visible;
            background: transparent;
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

        .hero-logo {{
            display: block;
            margin: 0 auto 0.85rem auto;
            width: min(380px, 41vw) !important;
            max-width: none !important;
            height: auto;
            filter: drop-shadow(0 10px 30px rgba(0,0,0,0.45));
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
          <div class="hero-text">
            <div>
              {logo_html}
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
