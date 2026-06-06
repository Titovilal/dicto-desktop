"""Concrete colour palettes mapping every token to a hex value.

Two palettes: ``LIGHT`` and ``DARK``. The ``system`` theme resolves to one of
these at runtime by reading the Windows app theme (see ``manager.py``).

Each palette is validated at import time to cover every token, so a forgotten
colour fails loudly instead of rendering a transparent widget.
"""

from __future__ import annotations

from dicto.ui.theme.tokens import ALL_TOKENS, Token

Palette = dict[Token, str]

LIGHT: Palette = {
    Token.BG: "#f7f7f8",
    Token.BG_ELEVATED: "#ffffff",
    Token.BG_HOVER: "#ececef",
    Token.BG_SELECTED: "#e3e9ff",
    Token.TEXT: "#1a1a1e",
    Token.TEXT_MUTED: "#6b6b75",
    Token.TEXT_ON_ACCENT: "#ffffff",
    Token.ACCENT: "#4f46e5",
    Token.ACCENT_HOVER: "#4338ca",
    Token.BORDER: "#dcdce1",
    Token.STATUS_RECORDING: "#e5484d",
    Token.STATUS_PROCESSING: "#f5a623",
    Token.STATUS_SUCCESS: "#30a46c",
    Token.STATUS_ERROR: "#e5484d",
}

DARK: Palette = {
    Token.BG: "#16161a",
    Token.BG_ELEVATED: "#1f1f25",
    Token.BG_HOVER: "#2a2a32",
    Token.BG_SELECTED: "#2d3357",
    Token.TEXT: "#ededf2",
    Token.TEXT_MUTED: "#9a9aa6",
    Token.TEXT_ON_ACCENT: "#ffffff",
    Token.ACCENT: "#7c6cff",
    Token.ACCENT_HOVER: "#9183ff",
    Token.BORDER: "#2e2e36",
    Token.STATUS_RECORDING: "#ff6369",
    Token.STATUS_PROCESSING: "#ffb224",
    Token.STATUS_SUCCESS: "#3dd68c",
    Token.STATUS_ERROR: "#ff6369",
}

PALETTES: dict[str, Palette] = {"light": LIGHT, "dark": DARK}


def _validate() -> None:
    for name, palette in PALETTES.items():
        missing = [tok.value for tok in ALL_TOKENS if tok not in palette]
        if missing:
            raise ValueError(f"palette {name!r} is missing tokens: {missing}")


_validate()
