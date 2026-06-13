"""Bundled fonts — register Hanken Grotesk with Qt at startup.

The app ships its own copy of Hanken Grotesk (OFL, see ``fonts/OFL.txt``) so the
UI looks identical on every machine instead of falling back to whatever sans the
OS happens to have. ``load_bundled_fonts`` registers the variable font with the
running ``QApplication`` and returns the family name the QSS should use; it is a
no-op (returning ``None``) if the file is missing or Qt rejects it, so a packaging
slip degrades to the system font rather than crashing startup.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_FONTS_DIR = Path(__file__).parent / "fonts"
_HANKEN = _FONTS_DIR / "HankenGrotesk-Variable.ttf"


def load_bundled_fonts() -> str | None:
    """Register Hanken Grotesk; return its family name, or ``None`` on failure.

    Must be called after a ``QApplication`` exists. The variable font carries the
    full weight axis, so a single file covers regular/medium/semibold/bold.
    """
    from PySide6.QtGui import QFontDatabase  # noqa: PLC0415 — needs a QApplication

    if not _HANKEN.is_file():
        logger.warning("bundled font missing: %s", _HANKEN)
        return None

    font_id = QFontDatabase.addApplicationFont(str(_HANKEN))
    if font_id == -1:
        logger.warning("Qt rejected bundled font: %s", _HANKEN)
        return None

    families = QFontDatabase.applicationFontFamilies(font_id)
    if not families:
        logger.warning("bundled font loaded but exposed no family: %s", _HANKEN)
        return None

    family = families[0]
    logger.info("registered bundled font: %s", family)
    return family
