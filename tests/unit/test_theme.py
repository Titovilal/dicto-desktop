"""Unit tests for the Qt-free theme resolution and QSS building."""

from __future__ import annotations

import pytest

from dicto.ui.theme import manager
from dicto.ui.theme.palettes import DARK, LIGHT, PALETTES
from dicto.ui.theme.tokens import ALL_TOKENS, Token


def test_every_palette_covers_every_token():
    for name, palette in PALETTES.items():
        for token in ALL_TOKENS:
            assert token in palette, f"{name} missing {token}"


def test_light_and_dark_differ():
    assert LIGHT[Token.BG] != DARK[Token.BG]
    assert LIGHT[Token.TEXT] != DARK[Token.TEXT]


def test_resolve_theme_explicit():
    assert manager.resolve_theme("light") == "light"
    assert manager.resolve_theme("dark") == "dark"


def test_resolve_theme_unknown_defaults_light():
    assert manager.resolve_theme("banana") == "light"


def test_resolve_theme_system(monkeypatch):
    monkeypatch.setattr(manager, "detect_system_theme", lambda: "dark")
    assert manager.resolve_theme("system") == "dark"
    monkeypatch.setattr(manager, "detect_system_theme", lambda: "light")
    assert manager.resolve_theme("system") == "light"


def test_resolve_palette_returns_correct_map(monkeypatch):
    assert manager.resolve_palette("dark") is DARK
    assert manager.resolve_palette("light") is LIGHT


def test_build_qss_contains_resolved_colors():
    qss = manager.build_qss(DARK)
    assert DARK[Token.BG] in qss
    assert DARK[Token.ACCENT] in qss
    # No raw token names should leak into the stylesheet.
    assert "color.bg" not in qss


def test_detect_system_theme_returns_valid_value():
    # On CI/non-Windows it falls back to "light"; on Windows it reads the reg.
    assert manager.detect_system_theme() in ("light", "dark")
