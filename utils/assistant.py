import html

import streamlit as st


QUESTION_KEY = "weather_assistant_question"
STATUS_KEY = "weather_assistant_status"
MESSAGE_KEY = "weather_assistant_message"


def _inject_assistant_css() -> None:
    st.markdown(
        """
        <style>
        .assistant-shell {
            position: relative;
            overflow: hidden;
            margin-top: 1.55rem;
            padding: 1.35rem 1.35rem 1.2rem;
            border-radius: 28px;
            border: 1px solid rgba(255, 176, 132, 0.18);
            background:
                radial-gradient(circle at top left, rgba(255, 165, 92, 0.15), transparent 34%),
                radial-gradient(circle at 100% 0%, rgba(129, 45, 45, 0.18), transparent 32%),
                linear-gradient(180deg, rgba(18, 23, 33, 0.96), rgba(12, 15, 23, 0.95));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.04),
                0 18px 34px rgba(0, 0, 0, 0.2);
        }

        .assistant-shell::before {
            content: "";
            position: absolute;
            inset: -15% auto auto -4%;
            width: 220px;
            height: 220px;
            border-radius: 999px;
            background: rgba(255, 146, 79, 0.08);
            filter: blur(18px);
            pointer-events: none;
        }

        .assistant-kicker {
            position: relative;
            z-index: 1;
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.62rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 183, 131, 0.22);
            background: rgba(255, 152, 94, 0.08);
            color: rgba(255, 226, 207, 0.78);
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .assistant-title {
            position: relative;
            z-index: 1;
            margin: 0.72rem 0 0.2rem;
            font-size: clamp(1.35rem, 1.2rem + 0.6vw, 1.9rem);
            font-weight: 800;
            color: rgba(255, 247, 242, 0.97);
            letter-spacing: 0.01em;
        }

        .assistant-subtitle {
            position: relative;
            z-index: 1;
            max-width: 760px;
            margin: 0 0 1rem;
            color: rgba(255, 232, 221, 0.72);
            font-size: 0.96rem;
            line-height: 1.5;
        }

        div[data-testid="stHorizontalBlock"]:has(.assistant-form-anchor) {
            gap: 0.75rem;
            align-items: end;
        }

        .assistant-form-anchor {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.assistant-shell-anchor) > [data-testid="element-container"] {
            margin-bottom: 0.6rem;
        }

        .assistant-shell-anchor {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.assistant-shell-anchor) div[data-testid="stTextInput"] label {
            color: rgba(255, 236, 227, 0.78);
            font-size: 0.84rem;
            font-weight: 600;
        }

        div[data-testid="stVerticalBlock"]:has(.assistant-shell-anchor) div[data-testid="stTextInput"] input {
            min-height: 3rem;
            border-radius: 16px;
            border: 1px solid rgba(255, 178, 134, 0.18);
            background: rgba(11, 15, 22, 0.82);
            color: rgba(255, 246, 241, 0.95);
        }

        div[data-testid="stVerticalBlock"]:has(.assistant-shell-anchor) div[data-testid="stTextInput"] input:focus {
            border-color: rgba(255, 180, 136, 0.38);
            box-shadow: 0 0 0 0.15rem rgba(255, 119, 56, 0.12);
        }

        div.stButton > button:has(+ .assistant-form-anchor),
        div[data-testid="stFormSubmitButton"] > button {
            min-height: 3rem;
            border-radius: 16px;
            border: 1px solid rgba(255, 189, 139, 0.34) !important;
            background:
                radial-gradient(circle at top left, rgba(255, 196, 125, 0.28), transparent 38%),
                linear-gradient(160deg, rgba(120, 27, 23, 0.98), rgba(178, 41, 35, 0.97)) !important;
            color: #fff9f4 !important;
            font-weight: 700;
            box-shadow:
                inset 0 1px 0 rgba(255, 248, 234, 0.12),
                0 14px 26px rgba(78, 10, 10, 0.24) !important;
        }

        div.stButton > button:has(+ .assistant-form-anchor):hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: rgba(255, 205, 161, 0.48) !important;
            background:
                radial-gradient(circle at top left, rgba(255, 211, 146, 0.34), transparent 38%),
                linear-gradient(160deg, rgba(138, 31, 26, 1), rgba(194, 46, 38, 0.98)) !important;
        }

        .assistant-response-box {
            position: relative;
            z-index: 1;
            margin-top: 0.2rem;
            padding: 1rem 1.05rem;
            border-radius: 20px;
            border: 1px solid rgba(255, 176, 132, 0.14);
            background:
                linear-gradient(180deg, rgba(16, 20, 29, 0.96), rgba(10, 13, 20, 0.94));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.03),
                0 10px 18px rgba(0, 0, 0, 0.12);
        }

        .assistant-response-label {
            margin: 0 0 0.42rem;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(255, 226, 212, 0.54);
        }

        .assistant-response-question {
            margin: 0 0 0.5rem;
            color: rgba(255, 229, 217, 0.65);
            font-size: 0.82rem;
            line-height: 1.45;
        }

        .assistant-response-text {
            margin: 0;
            color: rgba(255, 244, 238, 0.9);
            font-size: 0.95rem;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_assistant_state() -> None:
    st.session_state.setdefault(QUESTION_KEY, "")
    st.session_state.setdefault(STATUS_KEY, "idle")
    st.session_state.setdefault(
        MESSAGE_KEY,
        "AI responses will appear here once backend integration is added. For now, this panel previews the assistant experience and interaction flow.",
    )


def _build_placeholder_response(question: str) -> str:
    return (
        "Backend integration is not connected yet, but this is where a weather-focused answer about the setup, hazards, "
        "or today's forecast meaning will appear."
    )


def render_assistant() -> None:
    _inject_assistant_css()
    _init_assistant_state()

    st.markdown('<div class="assistant-shell-anchor"></div>', unsafe_allow_html=True)
    st.markdown('<div class="assistant-shell">', unsafe_allow_html=True)
    st.markdown('<div class="assistant-kicker">Phase One</div>', unsafe_allow_html=True)
    st.markdown('<div class="assistant-title">Weather Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="assistant-subtitle">Ask about the setup, hazards, or what today\'s weather means.</div>',
        unsafe_allow_html=True,
    )

    with st.form("weather_assistant_form", clear_on_submit=False):
        prompt_col, action_col = st.columns([5.2, 1.1], gap="small")
        with prompt_col:
            st.text_input(
                "Your question",
                key=QUESTION_KEY,
                placeholder="Example: What should I pay attention to in today's severe weather setup?",
            )
        with action_col:
            submit = st.form_submit_button("Ask", use_container_width=True)
            st.markdown('<div class="assistant-form-anchor"></div>', unsafe_allow_html=True)

    if submit:
        question = st.session_state.get(QUESTION_KEY, "").strip()
        if not question:
            st.session_state[STATUS_KEY] = "empty"
            st.session_state[MESSAGE_KEY] = "Enter a question to preview how the Weather Assistant response area will behave."
        else:
            st.session_state[STATUS_KEY] = "ready"
            st.session_state[MESSAGE_KEY] = _build_placeholder_response(question)

    status = st.session_state.get(STATUS_KEY, "idle")
    if status == "empty":
        st.info("Enter a weather question to preview the assistant flow.")

    question_text = st.session_state.get(QUESTION_KEY, "").strip()
    response_text = html.escape(st.session_state.get(MESSAGE_KEY, ""))

    question_markup = ""
    if status == "ready" and question_text:
        question_markup = (
            f'<div class="assistant-response-question">Latest prompt: {html.escape(question_text)}</div>'
        )

    st.markdown(
        (
            '<div class="assistant-response-box">'
            '<div class="assistant-response-label">Assistant Response</div>'
            f"{question_markup}"
            f'<p class="assistant-response-text">{response_text}</p>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
