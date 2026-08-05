"""Language registration, locale normalization, and translation fallback."""

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from modules.zh_tw import to_traditional


TextTransform = Callable[[str], str]
DEFAULT_LANGUAGE = "en"


@dataclass(frozen=True, slots=True)
class Language:
    aliases: tuple[str, ...] = ()
    fallbacks: tuple[str, ...] = ()
    transforms: Mapping[str, TextTransform] = field(default_factory=dict)


LANGUAGES: dict[str, Language] = {
    "en": Language(aliases=("en-us", "en-gb")),
    "ja": Language(aliases=("jp", "jpn", "ja-jp")),
    "zh": Language(aliases=("zh-cn", "zh-hans"), fallbacks=("zh-tw",)),
    "zh-tw": Language(
        aliases=("zh-hant", "zh-hk", "zh-mo"),
        fallbacks=("zh",),
        transforms={"zh": to_traditional, "*": to_traditional},
    ),
}
SUPPORTED_LANGUAGES = tuple(LANGUAGES)


def _clean_code(language: Any) -> str:
    return str(language or "").strip().lower().replace("_", "-")


def _resolve_registered_language(code: str) -> str | None:
    candidate = code
    while candidate:
        if candidate in LANGUAGES:
            return candidate
        for language, definition in LANGUAGES.items():
            if candidate in definition.aliases:
                return language
        candidate = candidate.rpartition("-")[0]
    return None


def register_language(
    code: str,
    *,
    aliases=(),
    fallbacks=(),
    transforms: Mapping[str, TextTransform] | None = None,
):
    """Register a language without changing normalization or selection code."""
    global SUPPORTED_LANGUAGES
    code = _clean_code(code)
    if not code:
        raise ValueError("Language code must not be empty")
    LANGUAGES[code] = Language(
        aliases=tuple(_clean_code(alias) for alias in aliases),
        fallbacks=tuple(_clean_code(item) for item in fallbacks),
        transforms=dict(transforms or {}),
    )
    SUPPORTED_LANGUAGES = tuple(LANGUAGES)
    return code


def normalize_language(language: Any, default=DEFAULT_LANGUAGE) -> str:
    normalized_default = (
        _resolve_registered_language(_clean_code(default)) or DEFAULT_LANGUAGE
    )
    return _resolve_registered_language(_clean_code(language)) or normalized_default


def get_user_language(user_id: str | None, default=DEFAULT_LANGUAGE) -> str:
    if not user_id:
        return normalize_language(default)

    from modules.user_db import get_user_field, user_exists

    language = (
        get_user_field(user_id, "language", default)
        if user_exists(user_id)
        else default
    )
    return normalize_language(language, default)


def _fallback_chain(language: str, default_language: str):
    candidates = (
        language,
        *LANGUAGES[language].fallbacks,
        normalize_language(default_language),
        DEFAULT_LANGUAGE,
        *LANGUAGES,
    )
    resolved = (_resolve_registered_language(code) for code in candidates)
    yield from dict.fromkeys(code for code in resolved if code)


def _transform(value: str, target_language: str, source_language: str):
    transforms = LANGUAGES[target_language].transforms
    transform = transforms.get(source_language) or transforms.get("*")
    return transform(value) if transform else value


def select_text(
    text: Any,
    user_id: str | None = None,
    language: str | None = None,
    default_language=DEFAULT_LANGUAGE,
) -> str:
    if not isinstance(text, Mapping):
        return "" if text is None else str(text)

    target = (
        normalize_language(language, default_language)
        if language is not None
        else get_user_language(user_id, default_language)
    )
    for source in _fallback_chain(target, default_language):
        if text.get(source) is not None:
            return _transform(str(text[source]), target, source)

    source, value = next(
        ((str(code), value) for code, value in text.items() if value is not None),
        (target, ""),
    )
    return _transform(str(value), target, source)
