# utils/ui.py

from typing import Optional
import streamlit as st
from textwrap import dedent
import base64
import os
import json
import uuid
import html
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import streamlit.components.v1 as components

def apply_global_ui() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Montserrat:wght@600;700;800&display=swap');
        :root {
            --font-body: 'Inter', sans-serif;
            --font-display: 'Montserrat', sans-serif;
        }

        html, body, [data-testid="stAppViewContainer"] {
            font-family: var(--font-body);
            font-weight: 400;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
        }

        p, li, label, div[data-testid="stMarkdownContainer"] {
            font-family: var(--font-body);
            font-weight: 400;
        }

        /* Hero title: strong, clean, authoritative */
        h1,
        div[data-testid="stHeadingWithActionElements"] h1 {
            font-family: var(--font-body);
            font-weight: 800;
            font-size: clamp(2.05rem, 1.6rem + 1.65vw, 3.0rem);
            line-height: 1.16;
            letter-spacing: 0.2px;
            margin-top: 2.2rem;
            margin-bottom: 1.05rem;
        }

        /* Section headers */
        h2, h3,
        div[data-testid="stHeadingWithActionElements"] h2,
        div[data-testid="stHeadingWithActionElements"] h3,
        .section-header {
            font-family: var(--font-display);
            font-weight: 700;
            letter-spacing: 0.7px;
            line-height: 1.25;
            margin-top: 2.05rem;
            margin-bottom: 0.8rem;
        }

        h2, div[data-testid="stHeadingWithActionElements"] h2 {
            font-size: clamp(1.38rem, 1.2rem + 0.72vw, 2rem);
        }

        h3, div[data-testid="stHeadingWithActionElements"] h3 {
            font-size: clamp(1.12rem, 1.02rem + 0.46vw, 1.48rem);
        }

        /* Navigation tabs */
        div[data-baseweb="tab-list"] {
            justify-content: center;
            gap: 0.3rem;
            margin-top: 0.2rem;
            margin-bottom: 0.9rem;
        }

        button[data-baseweb="tab"] {
            font-family: var(--font-body);
            font-size: 1.05rem;
            font-weight: 600;
            letter-spacing: 0.45px;
            padding: 0.7rem 1.28rem;
            margin: 0 0.38rem;
        }

        /* Metric numbers / data */
        div[data-testid="stMetricValue"] {
            font-family: var(--font-body);
            font-weight: 700;
            letter-spacing: 0.2px;
        }

        /* increase spacing between major Streamlit blocks */
        [data-testid="stVerticalBlock"] > [data-testid="element-container"] {
            margin-bottom: 1.0rem;
        }

        [data-testid="stVerticalBlock"] > [data-testid="element-container"]:has(h2),
        [data-testid="stVerticalBlock"] > [data-testid="element-container"]:has(h3) {
            margin-top: 1.05rem;
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
    font-family: 'Inter', sans-serif;
    font-size: 25px;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    opacity: 0.75;
    font-weight: 600;
}

/* Big number styling */
div[data-testid="stMetricValue"] {
    font-size: 42px;
    font-weight: 800;
    color: #ff3b3b;
}

/* ========================================== */
/* Top-left temp/dewpoint glance panel        */
/* ========================================== */

.glance-panel-wrap{
  display: flex;
  justify-content: flex-start;
  margin-top: 0.15rem;
  margin-bottom: 0.2rem;
}

.glance-panel{
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.34rem;
  padding: 0.46rem 0.74rem;
  border-radius: 14px;
  background: linear-gradient(130deg, rgba(16, 20, 26, 0.95), rgba(79, 10, 10, 0.88));
  border: 1px solid rgba(255, 112, 67, 0.65);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.28), 0 10px 22px rgba(0, 0, 0, 0.35);
}

.glance-loc{
  font-family: var(--font-body);
  font-size: 0.80rem;
  line-height: 1;
  font-weight: 700;
  letter-spacing: 0.3px;
  text-transform: none;
  color: rgba(255,255,255,0.82);
}

.glance-time{
  font-family: var(--font-body);
  font-size: 0.84rem;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0.2px;
  color: rgba(255,255,255,0.92);
}

.glance-time.local{
  color: #ffd166; /* warm highlight for local time */
}

.glance-time.zulu{
  color: #8bd3ff; /* cool standardized tone for UTC/Zulu */
}

.glance-val{
  font-family: var(--font-body);
  font-size: 0.92rem;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.2px;
  color: #ffffff;
  display: block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.glance-time{
  display: block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.glance-val.temp{
  color: #ff8a65; /* warm temp convention */
}

.glance-val.dew{
  color: #74d7ff; /* cool moisture convention */
}

.glance-val.wind{
  color: #d7e9ff; /* neutral-cool wind tone */
}

.glance-val.cond{
  color: #d2ffd2; /* readable condition accent */
}

@media (max-width: 900px) {
  .glance-panel{
    max-width: 240px;
  }
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
  font-family: 'Montserrat', sans-serif;
  font-size: 22px;
  text-transform: uppercase;
  letter-spacing: 0.9px;
  opacity: .75;
  font-weight: 700;
  margin-bottom: 12px;
}

.obs-card-value{
  font-family: 'Inter', sans-serif;
  font-size: 42px;
  font-weight: 800;
  color: #ff3b3b;     /* match metric number color */
  line-height: 1.1;
}

.obs-card-sub{
  font-family: 'Inter', sans-serif;
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

@media (max-width: 900px) {
    .block-container {
        padding-left: 1.15rem;
        padding-right: 1.15rem;
        padding-top: 1rem;
    }
    button[data-baseweb="tab"] {
        font-size: 0.98rem;
        margin: 0 0.16rem;
        padding: 0.64rem 0.86rem;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 34px;
    }
    .obs-card-title {
        font-size: 18px;
    }
    .obs-card-value {
        font-size: 34px;
    }
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

@st.cache_data(ttl=3600, show_spinner=False)
def _timezone_for_lat_lon(lat: float, lon: float) -> str:
    try:
        r = requests.get(
            f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}",
            headers={
                "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
                "Accept": "application/geo+json, application/json",
            },
            timeout=20,
        )
        r.raise_for_status()
        tz_name = ((r.json() or {}).get("properties") or {}).get("timeZone")
        if isinstance(tz_name, str) and tz_name:
            return tz_name
    except Exception:
        pass
    return "UTC"

def render_temp_dew_glance(
    location: str,
    temp_f: Optional[float],
    dew_f: Optional[float],
    lat: float,
    lon: float,
) -> None:
    def fmt(v: Optional[float]) -> str:
        if v is None:
            return "--"
        return f"{int(round(v))}&deg;F"

    tz_name = _timezone_for_lat_lon(lat, lon)
    try:
        local_tz = ZoneInfo(tz_name)
    except Exception:
        local_tz = timezone.utc
        tz_name = "UTC"

    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(local_tz)
    local_initial = f"Local Time: {now_local:%H:%M:%S} {now_local:%Z}"
    zulu_initial = f"Zulu Time: {now_utc:%H:%M:%S} UTC"

    local_id = f"glance-local-{uuid.uuid4().hex}"
    zulu_id = f"glance-zulu-{uuid.uuid4().hex}"
    location_safe = html.escape(location)

    panel_html = f"""
<div class="glance-panel-wrap">
  <div class="glance-panel" aria-label="Current local observations">
    <span class="glance-loc">{location_safe}</span>
    <span class="glance-time local" id="{local_id}">{local_initial}</span>
    <span class="glance-time zulu" id="{zulu_id}">{zulu_initial}</span>
    <span class="glance-val temp">Temp: {fmt(temp_f)}</span>
    <span class="glance-val dew">Dew Point: {fmt(dew_f)}</span>
  </div>
</div>
"""
    st.markdown(dedent(panel_html), unsafe_allow_html=True)
    components.html(
        f"""
<script>
const localId = {json.dumps(local_id)};
const zuluId = {json.dumps(zulu_id)};
const tzName = {json.dumps(tz_name)};

function two(n) {{
  return String(n).padStart(2, '0');
}}

function formatLocal(now) {{
  const parts = new Intl.DateTimeFormat('en-US', {{
    timeZone: tzName,
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZoneName: 'short'
  }}).formatToParts(now);

  const hour = parts.find(p => p.type === 'hour')?.value ?? '00';
  const minute = parts.find(p => p.type === 'minute')?.value ?? '00';
  const second = parts.find(p => p.type === 'second')?.value ?? '00';
  const zone = parts.find(p => p.type === 'timeZoneName')?.value ?? 'UTC';
  return `Local Time: ${{hour}}:${{minute}}:${{second}} ${{zone}}`;
}}

function formatZulu(now) {{
  return `Zulu Time: ${{two(now.getUTCHours())}}:${{two(now.getUTCMinutes())}}:${{two(now.getUTCSeconds())}} UTC`;
}}

function updateClock() {{
  const localNode = parent.document.getElementById(localId);
  const zuluNode = parent.document.getElementById(zuluId);
  if (!localNode || !zuluNode) {{
    return;
  }}
  const now = new Date();
  localNode.textContent = formatLocal(now);
  zuluNode.textContent = formatZulu(now);
}}

updateClock();
setInterval(updateClock, 1000);
</script>
""",
        height=0,
        width=0,
    )

def render_wind_conditions_glance(wind_text: str, conditions_text: str) -> None:
    wind_safe = html.escape((wind_text or "--").strip() or "--")
    cond_safe = html.escape((conditions_text or "--").strip() or "--")
    panel_html = f"""
<div class="glance-panel-wrap">
  <div class="glance-panel" aria-label="Current wind and conditions">
    <span class="glance-val wind">Wind: {wind_safe}</span>
    <span class="glance-val cond">Current Conditions: {cond_safe}</span>
  </div>
</div>
"""
    st.markdown(dedent(panel_html), unsafe_allow_html=True)

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
