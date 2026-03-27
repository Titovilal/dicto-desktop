"""Unit tests for internationalization."""
from __future__ import annotations

import src.i18n as i18n
from src.i18n.translations import TRANSLATIONS, UI_LANGUAGES


class TestTranslation:

    def setup_method(self):
        i18n.set_language("es")

    def test_returns_translation(self):
        assert i18n.t("quit") == "Salir"

    def test_fallback_to_english(self):
        # If a key exists in en but not in current language, use en
        i18n.set_language("es")
        # All keys exist in es, so test with a hypothetical missing key
        # by temporarily removing it
        original = TRANSLATIONS["es"].pop("quit", None)
        try:
            assert i18n.t("quit") == "Quit"
        finally:
            if original:
                TRANSLATIONS["es"]["quit"] = original

    def test_returns_key_if_not_found(self):
        assert i18n.t("nonexistent_key_xyz") == "nonexistent_key_xyz"

    def test_set_language_changes_output(self):
        i18n.set_language("en")
        assert i18n.t("quit") == "Quit"
        i18n.set_language("de")
        assert i18n.t("quit") == "Beenden"

    def test_set_invalid_language_ignored(self):
        i18n.set_language("es")
        i18n.set_language("xx")  # invalid
        assert i18n.get_language() == "es"

    def test_get_language(self):
        i18n.set_language("fr")
        assert i18n.get_language() == "fr"


class TestTranslationCompleteness:
    """All languages should have the same keys as English."""

    def test_all_languages_have_same_keys(self):
        en_keys = set(TRANSLATIONS["en"].keys())
        for lang, lang_dict in TRANSLATIONS.items():
            if lang == "en":
                continue
            missing = en_keys - set(lang_dict.keys())
            assert not missing, f"Language '{lang}' missing keys: {missing}"

    def test_ui_languages_match_translations(self):
        for lang in UI_LANGUAGES:
            assert lang in TRANSLATIONS, f"UI language '{lang}' has no translations"
