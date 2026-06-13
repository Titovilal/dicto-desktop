"""Semantic theme tokens.

Widgets reference *meaning* (``color.bg``, ``color.accent``) never raw hex.
A palette (see ``palettes.py``) maps each token to a concrete colour for a
given theme. This indirection is what lets theme switch live and keeps colour
out of widget code entirely.

The token set mirrors the design-system variables in the design hand-off
(``theme.css``): surfaces (bg / panel / muted / hover), borders (normal /
soft), a three-step text scale (text / mid / dim) and a neutral "primary"
accent (zinc) plus the red/amber/green/blue functional colours.

``Token`` is a plain string enum so it can be used directly as a dict key and
printed in QSS templates.
"""

from __future__ import annotations

import enum


class Token(str, enum.Enum):
    # Surfaces (design-system: --bg / --panel / --muted / --panel-2)
    BG = "color.bg"  # window body
    BG_PANEL = "color.bg.panel"  # rail, titlebar, footers — sits next to bg
    BG_ELEVATED = "color.bg.elevated"  # cards / raised (--muted)
    BG_HOVER = "color.bg.hover"  # hover / pressed (--panel-2)
    BG_SELECTED = "color.bg.selected"  # selected list rows (= --muted)

    # Text scale (--text / --text-mid / --text-dim)
    TEXT = "color.text"  # primary text
    TEXT_MUTED = "color.text.muted"  # secondary (--text-mid)
    TEXT_DIM = "color.text.dim"  # tertiary, metadata (--text-dim)
    TEXT_ON_ACCENT = "color.text.on_accent"  # text over accent fills (--primary-fg)

    # Accent / brand (--primary: zinc, dark-on-light / light-on-dark)
    ACCENT = "color.accent"
    ACCENT_HOVER = "color.accent.hover"

    # Borders & separators
    BORDER = "color.border"
    BORDER_SOFT = "color.border.soft"

    # Functional colours
    BLUE = "color.blue"  # info accents (system-audio badge, citations)
    KBD_BG = "color.kbd.bg"  # keyboard-shortcut pills

    # Status colours (tray icon, overlay, toasts)
    STATUS_RECORDING = "color.status.recording"  # --red
    STATUS_RECORDING_HOVER = "color.status.recording.hover"  # --red-hover
    STATUS_PROCESSING = "color.status.processing"  # --amber
    STATUS_SUCCESS = "color.status.success"  # --green
    STATUS_ERROR = "color.status.error"


# Every palette must define a colour for every token; enforced in palettes.py.
ALL_TOKENS: tuple[Token, ...] = tuple(Token)
