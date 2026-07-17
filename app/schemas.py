from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.prompts import Language


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8_000)
    session_id: str | None = Field(default=None, min_length=1, max_length=100)
    language: Language = "auto"
    model: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("message")
    @classmethod
    def message_must_have_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message cannot be blank")
        return value

    @field_validator("session_id")
    @classmethod
    def safe_session_id(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not all(char.isalnum() or char in "-_" for char in value):
            raise ValueError("session_id may contain only letters, numbers, '-' and '_'")
        return value


class StoredMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    session_id: str
    model: str
    language: Literal["bn", "en"]
    message: StoredMessage


class SessionResponse(BaseModel):
    session_id: str
    messages: list[StoredMessage]


class ModelsResponse(BaseModel):
    models: list[str]
    default: str

