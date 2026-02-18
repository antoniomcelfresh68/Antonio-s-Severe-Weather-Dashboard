# utils/ui.py
import streamlit as st

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

        </style>
        """,
        unsafe_allow_html=True,
    )
