from __future__ import annotations

from html import escape
from typing import Dict, List

import streamlit as st

from utils.nws_alerts import get_cached_severe_alerts_payload


def _event_css_class(event: str) -> str:
    mapping = {
        "Tornado Warning": "twarn",
        "Severe Thunderstorm Warning": "swarn",
        "Tornado Watch": "twatch",
        "Severe Thunderstorm Watch": "swatch",
    }
    return mapping.get(event, "fallback")


def _calc_duration_seconds(items: List[Dict[str, str]]) -> int:
    total_chars = sum(len(str(it.get("display_text", ""))) for it in items)
    if total_chars <= 0:
        return 55
    # Auto speed with clamp for readability.
    return max(35, min(140, int(total_chars / 7)))


def render_severe_ticker() -> None:
    """Render severe-only nationwide ticker with color-coded alert pills."""
    alerts, had_error = get_cached_severe_alerts_payload()

    if had_error:
        fallback = [{
            "event": "Fallback",
            "display_text": "NWS alert feed temporarily unavailable. Please stand by.",
        }]
        items = fallback
        duration = 60
    elif not alerts:
        items = [{
            "event": "Fallback",
            "display_text": "No active Tornado/Severe Thunderstorm watches or warnings nationwide.",
        }]
        duration = 55
    else:
        items = alerts
        duration = _calc_duration_seconds(items)

    pills_html = "".join(
        f'<span class="severe-pill {_event_css_class(str(item.get("event", "")))}">{escape(str(item.get("display_text", "")))}</span>'
        for item in items
    )

    # Duplicate the same pill run twice and animate by half the total width.
    # This creates a seamless infinite marquee loop.
    html = f"""
    <style>
      /* Allow the full-bleed ticker to escape the centered block container. */
      .block-container {{
        overflow-x: visible !important;
      }}
      .severe-ticker-wrap {{
        width: 100vw;
        position: relative;
        left: 50%;
        transform: translateX(-50%);
        height: 82px;
        margin: 1.0rem 0 0.7rem 0;
        overflow: hidden;
        border-radius: 0;
        border: 1px solid rgba(255,255,255,0.16);
        background: rgba(7, 10, 15, 0.95);
        display: flex;
        align-items: center;
      }}
      .severe-ticker-track {{
        display: inline-flex;
        align-items: center;
        width: max-content;
        white-space: nowrap;
        will-change: transform;
        animation: severeTickerMarquee {duration}s linear infinite;
      }}
      .severe-ticker-run {{
        display: inline-flex;
        align-items: center;
      }}
      .severe-pill {{
        display: inline-flex;
        align-items: center;
        margin-right: 96px;
        padding: 14px 22px;
        border-radius: 999px;
        font-size: 1.7rem;
        font-weight: 800;
        line-height: 1;
      }}
      .severe-pill.twarn {{
        background: #d81818;
        color: #ffffff;
      }}
      .severe-pill.swarn {{
        background: #ff9f1a;
        color: #161616;
      }}
      .severe-pill.twatch {{
        background: #6e2db8;
        color: #ffffff;
      }}
      .severe-pill.swatch {{
        background: #ffd24a;
        color: #161616;
      }}
      .severe-pill.fallback {{
        background: rgba(255,255,255,0.12);
        color: #ffffff;
      }}
      @keyframes severeTickerMarquee {{
        from {{ transform: translateX(0); }}
        to {{ transform: translateX(-50%); }}
      }}
    </style>
    <div class="severe-ticker-wrap">
      <div class="severe-ticker-track">
        <div class="severe-ticker-run">{pills_html}</div>
        <div class="severe-ticker-run">{pills_html}</div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
