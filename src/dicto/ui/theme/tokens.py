"""Semantic theme tokens.

Widgets reference *meaning* (``color.bg``, ``color.accent``) never raw hex.
A palette (see ``palettes.py``) maps each token to a concrete colour for a
given theme. This indirection is what lets theme switch live and keeps colour
out of widget code entirely.

``Token`` is a plain string enum so it can be used directly as a dict key and
printed in QSS templates.
"""

from __future__ import annotations

import enum


class Token(str, enum.Enum):
    # Surfaces
    BG = "color.bg"  # window background
    BG_ELEVATED = "color.bg.elevated"  # cards, panels, popups
    BG_HOVER = "color.bg.hover"
    BG_SELECTED = "color.bg.selected"

    # Text
    TEXT = "color.text"  # primary text
    TEXT_MUTED = "color.text.muted"  # secondary/labels
    TEXT_ON_ACCENT = "color.text.on_accent"  # text over accent fills

    # Accent / brand
    ACCENT = "color.accent"
    ACCENT_HOVER = "color.accent.hover"

    # Borders & separators
    BORDER = "color.border"

    # Status colours (tray icon, toasts)
    STATUS_RECORDING = "color.status.recording"
    STATUS_PROCESSING = "color.status.processing"
    STATUS_SUCCESS = "color.status.success"
    STATUS_ERROR = "color.status.error"


# Every palette must define a colour for every token; enforced in palettes.py.
ALL_TOKENS: tuple[Token, ...] = tuple(Token)
