"""Unit tests for dictation cleanup (pure, headless)."""

from __future__ import annotations

from dicto.core.cleanup import (
    capitalize_sentences,
    clean_dictation,
    fix_whitespace,
    remove_fillers,
)


def test_empty_and_whitespace_return_empty():
    assert clean_dictation("") == ""
    assert clean_dictation("   \n  ") == ""


def test_removes_english_fillers():
    out = clean_dictation("um so I think uh this works", lang="en")
    assert "um" not in out.lower().split()
    assert "uh" not in out.lower().split()
    assert "think" in out.lower()
    assert "works" in out.lower()


def test_removes_spanish_fillers():
    out = clean_dictation("eh creo que o sea esto funciona", lang="es")
    assert "o sea" not in out.lower()
    # "eh" as a standalone filler is gone, content stays.
    assert "creo" in out.lower()
    assert "funciona" in out.lower()


def test_filler_removal_respects_word_boundaries():
    # "humo" contains "um" but must not be touched.
    assert "humo" in remove_fillers("el humo", lang="en")
    # "like" is intentionally NOT a filler (too often content), stays as-is.
    assert "likeness" in remove_fillers("likeness", lang="en")


def test_fix_whitespace_collapses_and_hugs_punctuation():
    assert fix_whitespace("hello   world") == "hello world"
    assert fix_whitespace("hello ,world") == "hello, world"
    assert fix_whitespace("a.b") == "a. b"
    assert fix_whitespace("wait..") == "wait."


def test_fix_whitespace_does_not_split_decimals():
    # No space inserted inside a number like 3.14.
    assert fix_whitespace("3.14") == "3.14"


def test_capitalize_sentences():
    assert capitalize_sentences("hello. there is more.") == "Hello. There is more."
    assert capitalize_sentences("¿qué tal? bien") == "¿qué tal? Bien"


def test_capitalize_handles_accents():
    assert capitalize_sentences("árbol") == "Árbol"


def test_clean_dictation_full_pass():
    raw = "um,  hello   world .this is uh a test"
    out = clean_dictation(raw, lang="en")
    assert out == "Hello world. This is a test"


def test_clean_dictation_can_skip_capitalization():
    out = clean_dictation("um hello world", lang="en", capitalize=False)
    assert out == "hello world"


def test_unknown_language_uses_common_fillers_only():
    # German not shipped: common hesitations still go, content preserved.
    out = clean_dictation("mmm das ist gut", lang="de")
    assert "mmm" not in out.lower()
    assert "das ist gut" in out.lower()
