"""
Feature 5 — Language Detection & Bilingual Prompt Building

Uses langdetect to detect Hindi vs English (and falls back gracefully).
Prompt templates use {lang_code} and {lang_name} as variables so adding
new languages (Marathi, Telugu, etc.) only requires adding a mapping entry.
"""
from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# ── Language Mapping ───────────────────────────────────────────────────────────

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "mr": "Marathi (मराठी)",   # future
    "te": "Telugu (తెలుగు)",   # future
    "ta": "Tamil (தமிழ்)",     # future
    "bn": "Bengali (বাংলা)",   # future
    "gu": "Gujarati (ગુજરાતી)", # future
    "kn": "Kannada (ಕನ್ನಡ)",   # future
}

DEFAULT_LANG = "en"


def detect_language(text: str) -> str:
    """
    Detect language of input text.
    Returns ISO 639-1 code. Falls back to 'en' on any error.
    """
    try:
        from langdetect import detect, LangDetectException
        code = detect(text)
        # langdetect can return variants like 'zh-cn'; normalise to base code
        base_code = code.split("-")[0]
        supported = base_code if base_code in SUPPORTED_LANGUAGES else DEFAULT_LANG
        logger.debug("Detected language: %s (raw: %s)", supported, code)
        return supported
    except Exception as exc:
        logger.warning("Language detection failed: %s — defaulting to 'en'", exc)
        return DEFAULT_LANG


def get_lang_name(lang_code: str) -> str:
    return SUPPORTED_LANGUAGES.get(lang_code, "English")


def build_response_instruction(lang_code: str) -> str:
    """
    Returns a prompt snippet instructing Claude to respond in the detected language.
    This snippet is injected into every prompt template.
    """
    lang_name = get_lang_name(lang_code)
    if lang_code == "en":
        return "Respond in English."
    return (
        f"The user's input appears to be in {lang_name} (language code: {lang_code}). "
        f"Provide your explanation in {lang_name}. "
        f"Keep JSON field keys in English (they are machine-readable), but the 'explanation' "
        f"and 'matched_red_flags' values should be in {lang_name}."
    )
