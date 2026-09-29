"""Shared LLM client — uses Groq for fast inference."""

from __future__ import annotations

import os

from langchain_groq import ChatGroq


def get_chat_model() -> ChatGroq:
    """Return a ChatGroq instance using GROQ_API_KEY from the environment."""
    return ChatGroq(
        model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0.2,
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        max_tokens=4096,
    )
