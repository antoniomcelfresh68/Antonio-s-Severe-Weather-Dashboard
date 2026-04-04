from __future__ import annotations

from typing import Any

import streamlit as st

from utils.site_context import (
    AI_CURRENT_PAGE_KEY,
    AI_PAGE_CONTEXT_KEY,
    build_chat_prompt,
    build_merged_site_context,
    serialize_site_context,
)


BASE_SYSTEM_PROMPT = (
    "You are the AI assistant for Antonio's Severe Weather Dashboard. "
    "Answer using the structured dashboard context provided in separate system messages whenever it is available. "
    "That context includes full internal site state plus live external weather API summaries anchored to the selected dashboard location. "
    "Use current-page awareness as one field in the context, but do not limit your answer to the visible page. "
    "Do not guess about the user's location, hazards, radar, observations, forecasts, popup details, or loaded site state. "
    "If part of the dashboard context is unavailable, say what is unavailable and answer only from confirmed data and static site knowledge."
)


def init_ai_context_state() -> None:
    st.session_state.setdefault(AI_PAGE_CONTEXT_KEY, {})
    st.session_state.setdefault(AI_CURRENT_PAGE_KEY, "Home")


def set_current_ai_page(page_name: str) -> None:
    init_ai_context_state()
    st.session_state[AI_CURRENT_PAGE_KEY] = page_name


def update_page_ai_context(page_name: str, **context: Any) -> None:
    init_ai_context_state()
    page_context = dict(st.session_state[AI_PAGE_CONTEXT_KEY].get(page_name, {}))
    page_context.update({key: value for key, value in context.items()})
    st.session_state[AI_PAGE_CONTEXT_KEY][page_name] = page_context


def build_ai_context() -> str:
    init_ai_context_state()
    return serialize_site_context(build_merged_site_context())


def build_context_system_message() -> dict[str, str]:
    init_ai_context_state()
    prompt_messages = build_chat_prompt(build_merged_site_context(), "")
    return prompt_messages[1]
