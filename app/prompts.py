from __future__ import annotations

from typing import Literal

Language = Literal["auto", "bn", "en"]

BANGLA_SYSTEM_PROMPT = """আপনি একজন সহায়ক, নির্ভুল ও বন্ধুসুলভ AI সহকারী।
ব্যবহারকারী বাংলায় লিখলে স্বাভাবিক বাংলায় উত্তর দিন। প্রয়োজন হলে প্রচলিত ইংরেজি
technical term ব্যবহার করুন। তথ্য নিশ্চিত না হলে তা স্পষ্টভাবে বলুন এবং উত্তর সংক্ষিপ্ত রাখুন।"""

ENGLISH_SYSTEM_PROMPT = """You are a helpful, accurate, and friendly AI assistant.
Reply in clear English. If the user mixes Bangla and English, follow the user's dominant
language. Be concise, and clearly say when you are uncertain."""

BILINGUAL_SYSTEM_PROMPT = """You are a helpful, accurate, and friendly bilingual assistant.
Reply in Bangla when the user writes in Bangla and in English when the user writes in
English. For mixed input, follow the user's dominant language. Keep technical terms clear,
be concise, and explicitly state uncertainty."""


def contains_bangla(text: str) -> bool:
    return any("\u0980" <= char <= "\u09ff" for char in text)


def resolve_language(language: Language, latest_message: str) -> Literal["bn", "en"]:
    if language == "auto":
        return "bn" if contains_bangla(latest_message) else "en"
    return language


def system_prompt(language: Language, latest_message: str) -> str:
    if language == "auto":
        return BILINGUAL_SYSTEM_PROMPT
    return BANGLA_SYSTEM_PROMPT if language == "bn" else ENGLISH_SYSTEM_PROMPT

