"""Rounded-corner masking for frameless modal cards.

Qt does not clip a widget's children to its ``border-radius``, so an opaque
child (a nav column, a stacked panel) squares off the card's rounded bottom
corners. Masking the card with a rounded-rect region clips every child to the
radius at once. The mask region itself is not antialiased, but the card's own
QSS border is drawn inside the mask, so the visible edge stays smooth.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainterPath, QRegion
from PySide6.QtWidgets import QWidget


def apply_rounded_mask(widget: QWidget, radius: float) -> None:
    """Clip ``widget`` (and its children) to a rounded rectangle."""
    path = QPainterPath()
    path.addRoundedRect(QRectF(widget.rect()), radius, radius)
    widget.setMask(QRegion(path.toFillPolygon().toPolygon()))
