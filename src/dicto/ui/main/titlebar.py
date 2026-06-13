"""TitleBar — a custom window chrome bar for the frameless MainWindow.

Replaces the native OS title bar: an app icon + name on the left, a status dot
(``Listo`` / ``Grabando…`` / …) beside it, and minimise / maximise / close
controls on the right. The bar is the window's drag handle (double-click to
maximise) and forwards its button presses to the parent window.

Status is purely cosmetic here — ``set_status`` takes an ``AppState`` and paints
the dot with the matching ``STATUS_*`` token; ``app.py`` wires the orchestrator's
``stateChanged`` into it.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from dicto.core.state import AppState
from dicto.i18n import on_language_changed, t
from dicto.ui import icons
from dicto.ui.theme.manager import ThemeManager
from dicto.ui.theme.tokens import Token

_TITLEBAR_HEIGHT = 38

# Window-control glyphs (Unicode; render in the regular UI font).
_GLYPH_MIN = "—"  # — em dash
_GLYPH_MAX = "□"  # □ white square
_GLYPH_CLOSE = "✕"  # ✕ multiplication x

# AppState → the STATUS_* token used to paint the dot.
_STATUS_TOKEN = {
    AppState.IDLE: Token.STATUS_SUCCESS,
    AppState.RECORDING: Token.STATUS_RECORDING,
    AppState.PAUSED: Token.STATUS_PROCESSING,
    AppState.PROCESSING: Token.STATUS_PROCESSING,
    AppState.SUCCESS: Token.STATUS_SUCCESS,
    AppState.ERROR: Token.STATUS_ERROR,
}


class _Dot(QLabel):
    """A small filled circle whose colour tracks the app status."""

    _SIZE = 8

    def __init__(self, color: QColor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = color
        self.setFixedSize(self._SIZE, self._SIZE)

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802 — Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self._SIZE, self._SIZE)


class TitleBar(QFrame):
    """Custom chrome: icon + name + status dot, and window controls."""

    minimizeRequested = Signal()
    maximizeRequested = Signal()
    closeRequested = Signal()

    def __init__(self, theme: ThemeManager | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("titlebar")
        self.setFixedHeight(_TITLEBAR_HEIGHT)
        self._theme = theme

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(8)

        self._icon = QLabel()
        self._icon.setPixmap(icons.app_icon().pixmap(16, 16))
        layout.addWidget(self._icon)

        self._name = QLabel(t("app.name"))
        self._name.setObjectName("titleName")
        layout.addWidget(self._name)

        layout.addSpacing(6)
        self._dot = _Dot(self._status_color(AppState.IDLE))
        layout.addWidget(self._dot)
        self._status = QLabel(t("status.idle"))
        self._status.setProperty("dim", True)
        layout.addWidget(self._status)

        layout.addStretch(1)

        self._min_btn = self._control(_GLYPH_MIN, "min")
        self._max_btn = self._control(_GLYPH_MAX, "max")
        self._close_btn = self._control(_GLYPH_CLOSE, "close")
        self._min_btn.clicked.connect(self.minimizeRequested)
        self._max_btn.clicked.connect(self.maximizeRequested)
        self._close_btn.clicked.connect(self.closeRequested)
        for btn in (self._min_btn, self._max_btn, self._close_btn):
            layout.addWidget(btn)

        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    @staticmethod
    def _control(glyph: str, kind: str) -> QPushButton:
        btn = QPushButton(glyph)
        btn.setProperty("winctl", kind)
        btn.setFixedSize(46, _TITLEBAR_HEIGHT)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return btn

    def _status_color(self, state: AppState) -> QColor:
        token = _STATUS_TOKEN.get(state, Token.STATUS_SUCCESS)
        if self._theme is not None:
            return QColor(self._theme.color(token))
        return QColor("#34d399")

    # ── api ───────────────────────────────────────────────────────────────

    def set_status(self, state: AppState) -> None:
        """Paint the dot and label for the current app state."""
        self._dot.set_color(self._status_color(state))
        self._status.setText(t(f"status.{state.value}"))

    def retranslate(self) -> None:
        self._name.setText(t("app.name"))
        # The status label is driven by set_status; nothing else to refresh.

    # ── drag / double-click ─────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 — Qt override
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()  # native, snap-aware drag
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802 — Qt override
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximizeRequested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
