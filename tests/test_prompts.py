from app.prompts import BANGLA_SYSTEM_PROMPT, ENGLISH_SYSTEM_PROMPT, contains_bangla, resolve_language, system_prompt


def test_detects_bangla() -> None:
    assert contains_bangla("কেমন আছেন?") is True
    assert contains_bangla("How are you?") is False


def test_resolves_auto_language() -> None:
    assert resolve_language("auto", "একটি উত্তর দিন") == "bn"
    assert resolve_language("auto", "Give me an answer") == "en"


def test_uses_explicit_prompt() -> None:
    assert system_prompt("bn", "hello") == BANGLA_SYSTEM_PROMPT
    assert system_prompt("en", "হ্যালো") == ENGLISH_SYSTEM_PROMPT

