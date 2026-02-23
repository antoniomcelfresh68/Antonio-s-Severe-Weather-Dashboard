import os
import re
from html import escape
from typing import Dict, List

import streamlit as st
from streamlit_js_eval import streamlit_js_eval


GALLERY_DIR = "assets/gallery"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Example mapping format:
# {
#     "20250519_arnett_ok_tornado.jpg": "Arnett, OK - May 19, 2025",
# }
CAPTIONS: Dict[str, str] = {}


def _inject_gallery_css() -> None:
    st.markdown(
        """
        <style>
        .gallery-card {
            position: relative;
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.10);
            background: rgba(10, 12, 16, 0.72);
            box-shadow: 0 8px 22px rgba(0, 0, 0, 0.35), 0 0 20px rgba(192, 23, 33, 0.10);
            margin-bottom: 1rem;
            transition: transform 0.24s ease, box-shadow 0.24s ease, border-color 0.24s ease;
        }

        .gallery-card:hover {
            transform: translateY(-3px);
            border-color: rgba(255, 78, 78, 0.45);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.42), 0 0 22px rgba(255, 50, 50, 0.20);
        }

        .gallery-thumb-wrap {
            position: relative;
            overflow: hidden;
        }

        .gallery-thumb-wrap img {
            width: 100%;
            display: block;
            transition: transform 0.32s ease;
            border-radius: 0 !important;
        }

        .gallery-card:hover .gallery-thumb-wrap img {
            transform: scale(1.035);
        }

        .gallery-overlay {
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            padding: 0.55rem 0.7rem;
            background: linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(5,7,10,0.84) 60%, rgba(5,7,10,0.95) 100%);
            color: rgba(240, 240, 240, 0.93);
            font-size: 0.79rem;
            letter-spacing: 0.02em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .gallery-empty {
            border-radius: 14px;
            padding: 1rem 1.1rem;
            background: rgba(13, 15, 20, 0.72);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: rgba(225, 225, 225, 0.88);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def _list_gallery_images() -> List[str]:
    if not os.path.isdir(GALLERY_DIR):
        return []

    files = []
    for filename in os.listdir(GALLERY_DIR):
        ext = os.path.splitext(filename)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            files.append(filename)

    # Stable alphabetical sorting gives deterministic timeline-like ordering
    # when filenames include date prefixes such as YYYYMMDD.
    return sorted(files)


def _auto_caption(filename: str) -> str:
    stem = os.path.splitext(filename)[0]
    cleaned = re.sub(r"[_\-]+", " ", stem)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return filename
    return cleaned.title()


def _image_caption(filename: str) -> str:
    return CAPTIONS.get(filename, _auto_caption(filename))


def _grid_columns() -> int:
    width = streamlit_js_eval(js_expressions="window.innerWidth", key="gallery_window_width")
    if width is None:
        width = st.session_state.get("gallery_window_width_fallback", 1280)
    else:
        st.session_state["gallery_window_width_fallback"] = width

    if width >= 1500:
        return 4
    if width >= 980:
        return 3
    if width >= 620:
        return 2
    return 1


def render_gallery() -> None:
    _inject_gallery_css()
    st.markdown("# Photo Gallery")

    images = _list_gallery_images()
    if not images:
        st.markdown(
            '<div class="gallery-empty">No gallery images found in <code>assets/gallery/</code>.</div>',
            unsafe_allow_html=True,
        )
        return

    # Keep a responsive column count (desktop: 3-4, smaller screens: 1-2).
    n_cols = _grid_columns()
    columns = st.columns(n_cols, gap="medium")

    for idx, filename in enumerate(images):
        image_path = os.path.join(GALLERY_DIR, filename)
        caption = _image_caption(filename)
        col = columns[idx % n_cols]

        with col:
            st.markdown('<div class="gallery-card">', unsafe_allow_html=True)
            st.markdown('<div class="gallery-thumb-wrap">', unsafe_allow_html=True)
            st.image(image_path, use_container_width=True, output_format="auto")
            st.markdown(
                f'<div class="gallery-overlay">{escape(caption)}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
