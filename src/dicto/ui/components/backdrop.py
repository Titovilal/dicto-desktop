"""Dimming backdrop for in-window modals.

A semi-transparent overlay shown over the main window while a modal is open: it
darkens what's behind, swallows clicks so the app underneath can't be used, and
emits ``clicked`` when pressed so the modal can close on an outside click.

The modals are frameless top-level dialogs (so they can centre over and float
above the window). The backdrop is therefore also a frameless, translucent
top-level window pinned exactly over the main window and stacked just below the
modal. This replaces ``QDialog.setModal(True)``, whose OS-level grab beeps when
you click outside instead of dismissing — matching the design's "modal inside
the main window" intent (dim + click-away to close).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class Backdrop(QWidget):
    """Translucent top-level dim pinned over ``anchor``; clicks emit ``clicked``."""

    clicked = Signal()

    def __init__(self, anchor: QWidget) -> None:
        super().__init__(None)
        self._anchor = anchor
        self.setObjectName("modalBackdrop")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.hide()

    def show_over(self) -> None:
        """Cover the anchor window and show, ready to sit below the modal."""
        self.setGeometry(self._anchor.frameGeometry())
        self.show()
        self.raise_()

    def paintEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 102))  # ~40% black
        painter.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        self.clicked.emit()
        event.accept()
