"""Internationalisation: ``t()`` lookups + a hot language switch.

Translations live as JSON files under ``i18n/locales/<lang>.json``. The current
language is process-global. Changing it (``set_language``) notifies subscribers
through a Qt-free callback list so widgets can refresh in place — the app layer
bridges this to a Qt ``languageChanged`` signal.

Keys never appear literally in the UI; widgets call ``t("some.key")``. A missing
key falls back to English, then to the key itself, so nothing renders blank.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from dicto.config.defaults import DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)

_LOCALES_DIR = Path(__file__).parent / "locales"
_FALLBACK_LANG = "en"

_current_language = DEFAULT_LANGUAGE
_listeners: list[Callable[[str], None]] = []


@lru_cache(maxsize=None)
def _load_locale(lang: str) -> dict[str, str]:
    """Load and cache a locale's flat key->string map. Missing file -> {}."""
    path = _LOCALES_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — a broken locale must not crash the UI
        logger.warning("failed to load locale %s", lang, exc_info=True)
        return {}


def available_languages() -> list[str]:
    """Language codes that have a locale file, sorted."""
    return sorted(p.stem for p in _LOCALES_DIR.glob("*.json"))


def get_language() -> str:
    return _current_language


def set_language(lang: str) -> None:
    """Switch the active language and notify listeners (hot reload)."""
    global _current_language
    if lang == _current_language:
        return
    if not (_LOCALES_DIR / f"{lang}.json").exists():
        logger.warning("no locale for %r, keeping %r", lang, _current_language)
        return
    _current_language = lang
    for listener in list(_listeners):
        try:
            listener(lang)
        except Exception:  # noqa: BLE001 — one bad listener must not break the rest
            logger.exception("language listener failed")


def on_language_changed(listener: Callable[[str], None]) -> Callable[[], None]:
    """Subscribe to language changes; returns an unsubscribe callable."""
    _listeners.append(listener)

    def unsubscribe() -> None:
        try:
            _listeners.remove(listener)
        except ValueError:
            pass

    return unsubscribe


def t(key: str, /, **kwargs: object) -> str:
    """Translate ``key`` for the current language.

    Falls back to English then to ``key``. ``kwargs`` are substituted into
    ``{placeholder}`` tokens; a formatting error returns the raw string.
    """
    result = _load_locale(_current_language).get(key)
    if result is None:
        result = _load_locale(_FALLBACK_LANG).get(key)
    if result is None:
        return key
    if kwargs:
        try:
            return result.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return result
    return result
