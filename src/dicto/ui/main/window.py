"""MainWindow — rail (left) + library list + detail view, per the design.

Layout follows the design hand-off: a 58px icon rail (record / library /
dictionary / settings / avatar), a fixed-width library column and the detail
pane filling the rest. The rail only emits intent signals; ``app.py`` wires
them. (The settings and dictionary modals — Phase 6 — will hang off the same
signals.)
"""

from __future__ import annotations

import sys

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dicto.config.settings import Settings
from dicto.i18n import on_language_changed, t
from dicto.services.api.library import LibraryService
from dicto.services.api.transform import TransformService
from dicto.services.clipboard import Clipboard
from dicto.ui import icons
from dicto.core.state import AppState
from dicto.ui.main.chat_view import ChatView
from dicto.ui.main.detail_view import DetailView
from dicto.ui.main.library_view import LibraryView
from dicto.ui.main.titlebar import TitleBar
from dicto.ui.theme.manager import ThemeManager
from dicto.ui.theme.tokens import Token

_LIBRARY_WIDTH = 344
_RAIL_WIDTH = 58


class MainWindow(QMainWindow):
    recordRequested = Signal()
    dictionaryRequested = Signal()
    settingsRequested = Signal()

    def __init__(
        self,
        library: LibraryService | None = None,
        clipboard: Clipboard | None = None,
        theme: ThemeManager | None = None,
        transform: TransformService | None = None,
        settings: Settings | None = None,
    ) -> None:
        super().__init__()
        self.setWindowIcon(icons.app_icon())
        self.resize(1100, 680)
        # Frameless: the native chrome is replaced by our custom TitleBar.
        # Mouse tracking lets us pick up edge-resize hovers without a press.
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setMouseTracking(True)

        self._library = library or LibraryService()
        self._theme = theme
        self._transform = transform or TransformService()

        self._library_view = LibraryView(self._library, theme)
        self._detail_view = DetailView(
            self._library, clipboard, theme, self._transform, settings
        )
        self._chat_view = ChatView(self._library, self._transform, settings)

        # Detail and chat share the right pane; the detail's Ask tab flips here.
        self._detail_stack = QStackedWidget()
        self._detail_stack.addWidget(self._detail_view)
        self._detail_stack.addWidget(self._chat_view)

        rail = self._build_rail()

        library_pane = QFrame()
        library_pane.setObjectName("libraryPane")
        library_pane.setFixedWidth(_LIBRARY_WIDTH)
        lib_layout = QVBoxLayout(library_pane)
        lib_layout.setContentsMargins(0, 0, 0, 0)
        lib_layout.addWidget(self._library_view)

        body_widget = QWidget()
        body = QHBoxLayout(body_widget)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(rail)
        body.addWidget(library_pane)
        body.addWidget(self._detail_stack, 1)

        # Custom chrome (frameless) sits above the body.
        self._titlebar = TitleBar(theme)
        self._titlebar.minimizeRequested.connect(self.showMinimized)
        self._titlebar.maximizeRequested.connect(self._toggle_maximized)
        self._titlebar.closeRequested.connect(self.close)

        central = QWidget()
        shell = QVBoxLayout(central)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        shell.addWidget(self._titlebar)
        shell.addWidget(body_widget, 1)
        self.setCentralWidget(central)

        # Library selection drives both panes and snaps back to the detail view.
        self._library_view.transcriptSelected.connect(self._on_transcript_selected)
        self._library_view.emptied.connect(self._detail_view.show_empty)
        self._library_view.emptied.connect(self._chat_view.show_empty)
        self._detail_view.saved.connect(lambda _id: self._library_view.refresh())
        self._detail_view.statusMessage.connect(self._show_status)
        self._chat_view.statusMessage.connect(self._show_status)
        # The detail view's Ask tab opens the chat for the same transcript.
        self._detail_view.askRequested.connect(self._open_chat)
        # The library emitted its initial selection while building, before these
        # connections existed — re-emit so the detail pane starts populated.
        self._library_view.refresh()

        self.retranslate()
        self._refresh_icons()
        if theme is not None:
            theme.themeChanged.connect(lambda _e: self._refresh_icons())
        self._unsub_lang = on_language_changed(lambda _lang: self.retranslate())

    # ── rail ─────────────────────────────────────────────────────────────

    def _build_rail(self) -> QFrame:
        rail = QFrame()
        rail.setObjectName("rail")
        rail.setFixedWidth(_RAIL_WIDTH)
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(0, 12, 0, 14)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._record_btn = QPushButton()
        self._record_btn.setObjectName("railRecord")
        self._record_btn.setFixedSize(40, 40)
        self._record_btn.setIconSize(QSize(20, 20))
        self._record_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._record_btn.clicked.connect(self.recordRequested)
        layout.addWidget(self._record_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(4)

        self._lib_btn = self._rail_button("list")
        self._lib_btn.setCheckable(True)
        self._lib_btn.setChecked(True)
        layout.addWidget(self._lib_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        self._dict_btn = self._rail_button("book")
        self._dict_btn.clicked.connect(self.dictionaryRequested)
        layout.addWidget(self._dict_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch(1)

        self._settings_btn = self._rail_button("settings_small")
        self._settings_btn.clicked.connect(self.settingsRequested)
        layout.addWidget(self._settings_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        self._avatar = QLabel()
        self._avatar.setObjectName("avatar")
        self._avatar.setFixedSize(30, 30)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignHCenter)

        return rail

    @staticmethod
    def _rail_button(glyph: str) -> QPushButton:
        btn = QPushButton()
        btn.setProperty("rail", True)
        btn.setProperty("glyph", glyph)
        btn.setFixedSize(42, 42)
        btn.setIconSize(QSize(20, 20))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _refresh_icons(self) -> None:
        if self._theme is None:
            return
        self._record_btn.setIcon(icons.svg_icon("mic", "#ffffff", 20))
        for btn in (self._lib_btn, self._dict_btn, self._settings_btn):
            color = self._theme.color(Token.TEXT if btn.isChecked() else Token.TEXT_DIM)
            btn.setIcon(icons.svg_icon(btn.property("glyph"), color, 20))

    # ── api ──────────────────────────────────────────────────────────────

    def refresh_library(self) -> None:
        """Reload the library list (called after a transcript is auto-saved)."""
        self._library_view.refresh()

    def _on_transcript_selected(self, transcript_id: str) -> None:
        # Load both panes; show the detail view (chat is opened explicitly).
        self._detail_view.load(transcript_id)
        self._chat_view.load(transcript_id)
        self._detail_stack.setCurrentWidget(self._detail_view)

    def _open_chat(self, transcript_id: str) -> None:
        self._chat_view.load(transcript_id)
        self._detail_stack.setCurrentWidget(self._chat_view)

    def _show_status(self, message: str) -> None:
        self.statusBar().showMessage(message, 3000)

    def _toggle_maximized(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def set_status(self, state: AppState) -> None:
        """Reflect the app's recording state in the title-bar status dot."""
        self._titlebar.set_status(state)

    def retranslate(self) -> None:
        self.setWindowTitle(t("window.title"))
        self._record_btn.setToolTip(t("overlay.record"))
        self._lib_btn.setToolTip(t("window.library"))
        self._dict_btn.setToolTip(t("rail.dictionary"))
        self._settings_btn.setToolTip(t("tray.settings"))
        self._avatar.setText(t("rail.avatar"))

    # ── frameless resize ─────────────────────────────────────────────────

    # Width of the invisible edge gutter that resizes the window. Handled in
    # nativeEvent (WM_NCHITTEST) so it works even though child widgets cover
    # the client area — the only reliable approach for a frameless window.
    _RESIZE_BORDER = 6

    def nativeEvent(self, event_type, message):  # noqa: N802 — Qt override
        if sys.platform != "win32" or event_type != "windows_generic_MSG":
            return super().nativeEvent(event_type, message)

        msg = ctypes.wintypes.MSG.from_address(int(message))
        if msg.message != 0x0084:  # WM_NCHITTEST
            return super().nativeEvent(event_type, message)
        if self.isMaximized():
            return super().nativeEvent(event_type, message)

        # lParam packs the screen-space cursor as (y << 16 | x), 16-bit signed.
        x = ctypes.c_short(msg.lParam & 0xFFFF).value
        y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
        # Compute edges from the window's frame geometry in screen space.
        geo = self.frameGeometry()
        b = self._RESIZE_BORDER
        left = x <= geo.left() + b
        right = x >= geo.right() - b
        top = y <= geo.top() + b
        bottom = y >= geo.bottom() - b

        hit = {
            (True, False, True, False): 13,   # HTTOPLEFT
            (False, True, True, False): 14,   # HTTOPRIGHT
            (True, False, False, True): 16,   # HTBOTTOMLEFT
            (False, True, False, True): 17,   # HTBOTTOMRIGHT
            (True, False, False, False): 10,  # HTLEFT
            (False, True, False, False): 11,  # HTRIGHT
            (False, False, True, False): 12,  # HTTOP
            (False, False, False, True): 15,  # HTBOTTOM
        }.get((left, right, top, bottom))
        if hit is not None:
            return True, hit
        return super().nativeEvent(event_type, message)

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt override
        # Closing hides to tray rather than quitting; the tray is the anchor.
        event.ignore()
        self.hide()
