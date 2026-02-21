"""
Language helpers for API request parsing and normalization.
"""
from __future__ import annotations

from typing import Iterable

SUPPORTED_LANGUAGES: tuple[str, ...] = ("uz", "en", "ru")
DEFAULT_LANGUAGE = "uz"


def _extract_language_code(value: str) -> str:
    raw = value.strip().lower()
    primary = raw.split(",")[0].split(";")[0].strip()
    return primary.split("-")[0].split("_")[0].strip()


def normalize_language(value: str | None, allowed: Iterable[str] = SUPPORTED_LANGUAGES) -> str:
    """
    Normalize an incoming language code.
    Falls back to DEFAULT_LANGUAGE when value is missing or unsupported.
    """
    if not value:
        return DEFAULT_LANGUAGE
    code = _extract_language_code(value)
    return code if code in allowed else DEFAULT_LANGUAGE


def is_supported_language(value: str | None) -> bool:
    """Check whether the provided language code is supported."""
    if not value:
        return False
    return _extract_language_code(value) in SUPPORTED_LANGUAGES
