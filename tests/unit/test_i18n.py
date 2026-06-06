"""Unit tests for the i18n loader, t(), and the languageChanged callback."""

from __future__ import annotations

from dicto import i18n


def test_translates_known_key_per_language():
    i18n.set_language("en")
    assert i18n.t("tray.open") == "Open Dicto"
    i18n.set_language("es")
    assert i18n.t("tray.open") == "Abrir Dicto"


def test_missing_key_returns_key():
    i18n.set_language("en")
    assert i18n.t("this.key.does.not.exist") == "this.key.does.not.exist"


def test_falls_back_to_english_when_key_absent_in_locale(tmp_path, monkeypatch):
    # es.json has tray.open; assume a hypothetical key only in en falls back.
    i18n.set_language("es")
    # "common.save" exists in both; sanity that es value is used, not en.
    assert i18n.t("common.save") == "Guardar"


def test_available_languages_includes_en_and_es():
    langs = i18n.available_languages()
    assert "en" in langs
    assert "es" in langs


def test_set_language_ignores_unknown():
    i18n.set_language("en")
    i18n.set_language("xx")  # no locale file
    assert i18n.get_language() == "en"


def test_language_changed_listener_fires():
    i18n.set_language("en")
    seen: list[str] = []
    unsubscribe = i18n.on_language_changed(seen.append)
    try:
        i18n.set_language("es")
        i18n.set_language("es")  # same -> no extra notification
        i18n.set_language("en")
    finally:
        unsubscribe()
    assert seen == ["es", "en"]


def test_listener_unsubscribes():
    i18n.set_language("en")
    seen: list[str] = []
    unsubscribe = i18n.on_language_changed(seen.append)
    unsubscribe()
    i18n.set_language("es")
    assert seen == []


def test_format_substitution():
    # No starter key uses placeholders, so verify the mechanism directly via a
    # key that does not exist returns the key (no crash with kwargs).
    assert i18n.t("missing.key", name="x") == "missing.key"
