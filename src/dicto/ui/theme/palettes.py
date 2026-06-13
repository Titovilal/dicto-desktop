"""Concrete colour palettes mapping every token to a hex value.

Values come straight from the design hand-off (``Dicto - Entrega/codigo/
screens/theme.css``): a zinc scale, dark by default plus a light variant.
The ``system`` theme resolves to one of these at runtime by reading the
Windows app theme (see ``manager.py``).

Each palette is validated at import time to cover every token, so a forgotten
colour fails loudly instead of rendering a transparent widget.
"""

from __future__ import annotations

from dicto.ui.theme.tokens import ALL_TOKENS, Token

Palette = dict[Token, str]

DARK: Palette = {
    Token.BG: "#09090b",  # zinc-950
    Token.BG_PANEL: "#131316",
    Token.BG_ELEVATED: "#18181b",  # zinc-900
    Token.BG_HOVER: "#1f1f23",
    Token.BG_SELECTED: "#18181b",
    Token.TEXT: "#f4f4f5",  # zinc-100
    Token.TEXT_MUTED: "#a1a1aa",  # zinc-400
    Token.TEXT_DIM: "#71717a",  # zinc-500
    Token.TEXT_ON_ACCENT: "#18181b",
    Token.ACCENT: "#d4d4d8",  # zinc-300
    Token.ACCENT_HOVER: "#e4e4e7",
    Token.BORDER: "#27272a",  # zinc-800
    Token.BORDER_SOFT: "#1c1c20",
    Token.BLUE: "#60a5fa",
    Token.KBD_BG: "#27272a",
    Token.STATUS_RECORDING: "#ef4444",
    Token.STATUS_RECORDING_HOVER: "#dc2626",
    Token.STATUS_PROCESSING: "#fbbf24",
    Token.STATUS_SUCCESS: "#34d399",
    Token.STATUS_ERROR: "#ef4444",
}

LIGHT: Palette = {
    Token.BG: "#ffffff",
    Token.BG_PANEL: "#fafafa",
    Token.BG_ELEVATED: "#f4f4f5",  # zinc-100
    Token.BG_HOVER: "#f4f4f5",
    Token.BG_SELECTED: "#f4f4f5",
    Token.TEXT: "#18181b",  # zinc-900
    Token.TEXT_MUTED: "#52525b",  # zinc-600
    Token.TEXT_DIM: "#71717a",  # zinc-500
    Token.TEXT_ON_ACCENT: "#fafafa",
    Token.ACCENT: "#18181b",  # dark button on light
    Token.ACCENT_HOVER: "#27272a",
    Token.BORDER: "#e4e4e7",  # zinc-200
    Token.BORDER_SOFT: "#ececee",
    Token.BLUE: "#2563eb",
    Token.KBD_BG: "#ffffff",
    Token.STATUS_RECORDING: "#ef4444",
    Token.STATUS_RECORDING_HOVER: "#dc2626",
    Token.STATUS_PROCESSING: "#d97706",
    Token.STATUS_SUCCESS: "#059669",
    Token.STATUS_ERROR: "#ef4444",
}

PALETTES: dict[str, Palette] = {"light": LIGHT, "dark": DARK}


def _validate() -> None:
    for name, palette in PALETTES.items():
        missing = [tok.value for tok in ALL_TOKENS if tok not in palette]
        if missing:
            raise ValueError(f"palette {name!r} is missing tokens: {missing}")


_validate()
