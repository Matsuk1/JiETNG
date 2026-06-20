from __future__ import annotations

from typing import Any, Mapping
from modules.zh_tw import to_traditional


SUPPORTED_LANGUAGES = ("ja", "en", "zh", "zh-tw")
DEFAULT_LANGUAGE = "en"
ALIASES = {
    "jp": "ja",
    "jpn": "ja",
    "ja-jp": "ja",
    "zh-cn": "zh",
    "zh-hans": "zh",
    "zh-hant": "zh-tw",
    "zh-hk": "zh-tw",
    "zh-mo": "zh-tw",
}


def normalize_language(language: Any, default: str = DEFAULT_LANGUAGE) -> str:
    default = default if default in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    code = str(language or "").strip().lower().replace("_", "-")
    code = ALIASES.get(code, code)
    if code not in SUPPORTED_LANGUAGES:
        code = code.split("-", 1)[0]
    return code if code in SUPPORTED_LANGUAGES else default


def get_user_language(user_id: str | None, default: str = DEFAULT_LANGUAGE) -> str:
    if not user_id:
        return normalize_language(default)

    from modules.user_db import get_user_field, user_exists

    language = get_user_field(user_id, "language", default) if user_exists(user_id) else default
    return normalize_language(language, default)


def select_text(
    text: Any,
    user_id: str | None = None,
    language: str | None = None,
    default_language: str = DEFAULT_LANGUAGE,
) -> str:
    if not isinstance(text, Mapping):
        return "" if text is None else str(text)

    lang = normalize_language(language, default_language) if language is not None else get_user_language(user_id, default_language)
    zh_fallback = ("zh",) if lang == "zh-tw" else ("zh-tw",) if lang == "zh" else ()
    for code in (lang, *zh_fallback, normalize_language(default_language), DEFAULT_LANGUAGE, "ja", "zh", "zh-tw"):
        value = text.get(code)
        if value is not None:
            value = str(value)
            return to_traditional(value) if lang == "zh-tw" and code == "zh" else value

    value = str(next((value for value in text.values() if value is not None), ""))
    return to_traditional(value) if lang == "zh-tw" else value
