"""
Internationalization module for Dicto.
Provides translations for UI strings in 5 languages: en, es, de, fr, pt.
"""

from src.i18n.translations import TRANSLATIONS

_current_language = "es"


def set_language(lang: str) -> None:
    """Set the current UI language."""
    global _current_language
    if lang in TRANSLATIONS:
        _current_language = lang


def get_language() -> str:
    """Get the current UI language."""
    return _current_language


def t(key: str) -> str:
    """Translate a key to the current language. Falls back to English, then returns the key."""
    lang_dict = TRANSLATIONS.get(_current_language, {})
    result = lang_dict.get(key)
    if result is not None:
        return result
    # Fallback to English
    result = TRANSLATIONS.get("en", {}).get(key)
    if result is not None:
        return result
    return key
