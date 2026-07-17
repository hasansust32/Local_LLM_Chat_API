from __future__ import annotations

import os
from dataclasses import dataclass


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


def _positive_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: float
    max_context_messages: int


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Local LLM Chat"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        ollama_timeout_seconds=_positive_float("OLLAMA_TIMEOUT_SECONDS", 120.0),
        max_context_messages=_positive_int("MAX_CONTEXT_MESSAGES", 20),
    )

