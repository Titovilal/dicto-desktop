"""Dimming backdrop for in-window modals.

A semi-transparent overlay shown over the main window while a modal is open: it
darkens what's behind, swallows clicks so the app underneath can't be used, and
emits ``clicked`` when pressed so the modal can close on an outside click.

The backdrop is a *child* of the main window that fills its client area. Making
it a child (rather than a translucent top-level window) means it composites
reliably over the window on Windows — a separate top-level dim window does not
stack predictably between the main window and the frameless modal dialog, so it
was rendering behind the window and the dim never showed. The modal itself stays
a frameless top-level dialog floating above. This replaces
``QDialog.setModal(True)``, whose OS-level grab beeps when you click outside
instead of dismissing — matching the design's "modal inside the main window"
intent (dim + click-away to close).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class Backdrop(QWidget):
    """Translucent child dim filling ``anchor``'s client area; clicks emit ``clicked``."""

    clicked = Signal()

    def __init__(self, anchor: QWidget) -> None:
        super().__init__(anchor)
        self._anchor = anchor
        self.setObjectName("modalBackdrop")
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.hide()

    def show_over(self) -> None:
        """Cover the anchor's client area and show, ready to sit below the modal."""
        self.setGeometry(self._anchor.rect())
        self.show()
        self.raise_()

    def paintEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 102))  # ~40% black
        painter.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        self.clicked.emit()
        event.accept()
