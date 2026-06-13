"""Settings modal — the third zone, shown INSIDE the main window (never a
separate window in the taskbar).

Styled per the design hand-off: 720×600 card with a left nav and a content
pane of field rows (label + sub on the left, control on the right). For now it
ships the panels whose backends already exist:

- Recording: hotkey (read-only pill), capture mode, microphone + live test,
  system audio (WASAPI), overlay position.
- Appearance: theme (light/dark/system) and language, applied live.

Account, output, privacy and the rest of Phase 6 land as more panels here.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dicto.config.settings import Settings
from dicto.i18n import on_language_changed, set_language, t
from dicto.ui.components.backdrop import Backdrop
from dicto.ui.components.rounded import apply_rounded_mask
from dicto.ui.settings.audio import MicTestPanel
from dicto.ui.theme.manager import ThemeManager

_OVERLAY_POSITIONS = ("top-left", "top-right", "bottom-left", "bottom-right", "center")
_THEMES = ("light", "dark", "system")
_LANGUAGES = ("es", "en")


def _field_row(parent_layout: QVBoxLayout, control: QWidget) -> tuple[QLabel, QLabel]:
    """Add a design-system field row; returns (label, sub) for retranslate."""
    row = QHBoxLayout()
    row.setSpacing(16)
    left = QVBoxLayout()
    left.setSpacing(2)
    label = QLabel()
    label.setProperty("fieldLabel", True)
    sub = QLabel()
    sub.setProperty("dim", True)
    # Long explanations wrap instead of forcing the row past the modal edge.
    sub.setWordWrap(True)
    left.addWidget(label)
    left.addWidget(sub)
    row.addLayout(left, 1)
    row.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)
    parent_layout.addLayout(row)
    rule = QFrame()
    rule.setProperty("fieldRule", True)
    rule.setFixedHeight(1)
    parent_layout.addWidget(rule)
    return label, sub


class SettingsModal(QDialog):
    """Frameless modal dialog with nav + stacked panels."""

    def __init__(
        self,
        theme: ThemeManager,
        settings: Settings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._settings = settings
        self._drag_offset: QPoint | None = None

        self.setObjectName("settingsModal")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        # Translucent so the card's rounded corners read as real transparency
        # on all four sides; the fill/border/radius live on the inner card.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(720, 600)

        # Dim the window behind us and close on an outside click. (A real
        # QDialog modal grab beeps on outside clicks instead of dismissing.)
        self._backdrop = Backdrop(parent) if parent is not None else None
        if self._backdrop is not None:
            self._backdrop.clicked.connect(self.close)

        # Outer layout holds a single rounded card; the dialog itself is clear.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("modalCard")
        outer.addWidget(card)
        self._card = card

        root = QVBoxLayout(card)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── header: title + close ────────────────────────────────────────
        head = QFrame()
        head.setObjectName("modalHead")
        head.setFixedHeight(56)
        head_l = QHBoxLayout(head)
        head_l.setContentsMargins(22, 0, 14, 0)
        self._title = QLabel()
        self._title.setProperty("heading", True)
        head_l.addWidget(self._title)
        head_l.addStretch(1)
        close_btn = QPushButton("✕")
        close_btn.setProperty("iconBtn", True)
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        head_l.addWidget(close_btn)
        root.addWidget(head)

        # ── body: nav + stacked panels ───────────────────────────────────
        body = QHBoxLayout()
        body.setSpacing(0)

        nav = QFrame()
        nav.setObjectName("modalNav")
        nav.setFixedWidth(188)
        nav_l = QVBoxLayout(nav)
        nav_l.setContentsMargins(10, 12, 10, 12)
        nav_l.setSpacing(2)
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: list[QPushButton] = []
        for index in range(2):  # recording, appearance
            btn = QPushButton()
            btn.setProperty("mnav", True)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.toggled.connect(
                lambda on, i=index: on and self._stack.setCurrentIndex(i)
            )
            self._nav_group.addButton(btn)
            nav_l.addWidget(btn)
            self._nav_buttons.append(btn)
        nav_l.addStretch(1)
        body.addWidget(nav)

        self._stack = QStackedWidget()
        # Named so the QSS can round its bottom-right corner to the card's
        # radius — its opaque background would otherwise square it off.
        self._stack.setObjectName("modalStack")
        self._stack.addWidget(self._build_recording_panel())
        self._stack.addWidget(self._build_appearance_panel())
        body.addWidget(self._stack, 1)
        root.addLayout(body, 1)

        self._nav_buttons[0].setChecked(True)
        self.retranslate()
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    # ── panels ───────────────────────────────────────────────────────────

    @staticmethod
    def _panel() -> tuple[QWidget, QVBoxLayout]:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(13)
        return panel, layout

    def _build_recording_panel(self) -> QWidget:
        panel, layout = self._panel()

        self._rec_title = QLabel()
        self._rec_title.setProperty("settingsTitle", True)
        self._rec_sub = QLabel()
        self._rec_sub.setProperty("dim", True)
        layout.addWidget(self._rec_title)
        layout.addWidget(self._rec_sub)
        layout.addSpacing(8)

        # Hotkey (read-only for now; rebinding lands with the hotkey panel).
        hotkey_pill = QLabel(
            " + ".join(
                part.capitalize()
                for part in (*self._settings.hotkey.modifiers, self._settings.hotkey.key)
            )
        )
        hotkey_pill.setObjectName("kbdPill")
        self._f_hotkey = _field_row(layout, hotkey_pill)

        # Capture mode: hold / toggle.
        self._mode_combo = QComboBox()
        self._mode_combo.addItem("", "hold")
        self._mode_combo.addItem("", "toggle")
        idx = self._mode_combo.findData(self._settings.behavior.recording_mode)
        self._mode_combo.setCurrentIndex(max(0, idx))
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self._f_mode = _field_row(layout, self._mode_combo)

        # Microphone + live test (existing panel).
        self._mic_panel = MicTestPanel(self._theme, self._settings)
        self._mic_panel.setFixedWidth(300)
        # The field row already says "Micrófono"; the panel's inner label dupes it.
        self._mic_panel._device_label.hide()
        self._f_mic = _field_row(layout, self._mic_panel)

        # System audio (WASAPI loopback).
        self._sysaudio = QPushButton()
        self._sysaudio.setCheckable(True)
        self._sysaudio.setProperty("chip", True)
        self._sysaudio.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sysaudio.setChecked(self._settings.audio.include_system_audio)
        self._sysaudio.toggled.connect(self._on_sysaudio_toggled)
        self._f_sysaudio = _field_row(layout, self._sysaudio)

        # Overlay position.
        self._pos_combo = QComboBox()
        for pos in _OVERLAY_POSITIONS:
            self._pos_combo.addItem("", pos)
        idx = self._pos_combo.findData(self._settings.overlay.position)
        self._pos_combo.setCurrentIndex(max(0, idx))
        self._pos_combo.currentIndexChanged.connect(self._on_position_changed)
        self._f_pos = _field_row(layout, self._pos_combo)

        layout.addStretch(1)
        return panel

    def _build_appearance_panel(self) -> QWidget:
        panel, layout = self._panel()

        self._app_title = QLabel()
        self._app_title.setProperty("settingsTitle", True)
        self._app_sub = QLabel()
        self._app_sub.setProperty("dim", True)
        layout.addWidget(self._app_title)
        layout.addWidget(self._app_sub)
        layout.addSpacing(8)

        self._theme_combo = QComboBox()
        for name in _THEMES:
            self._theme_combo.addItem("", name)
        idx = self._theme_combo.findData(self._settings.appearance.theme)
        self._theme_combo.setCurrentIndex(max(0, idx))
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self._f_theme = _field_row(layout, self._theme_combo)

        self._lang_combo = QComboBox()
        self._lang_combo.addItem("Español", "es")
        self._lang_combo.addItem("English", "en")
        idx = self._lang_combo.findData(self._settings.appearance.language)
        self._lang_combo.setCurrentIndex(max(0, idx))
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        self._f_lang = _field_row(layout, self._lang_combo)

        layout.addStretch(1)
        return panel

    # ── handlers (apply live + persist) ──────────────────────────────────

    def _on_mode_changed(self, _i: int) -> None:
        self._settings.behavior.recording_mode = self._mode_combo.currentData()
        self._settings.save()

    def _on_sysaudio_toggled(self, on: bool) -> None:
        self._settings.audio.include_system_audio = on
        self._settings.save()
        self.retranslate()

    def _on_position_changed(self, _i: int) -> None:
        self._settings.overlay.position = self._pos_combo.currentData()
        # Forget any dragged position so the new anchor takes effect.
        self._settings.overlay.x = None
        self._settings.overlay.y = None
        self._settings.save()

    def _on_theme_changed(self, _i: int) -> None:
        choice = self._theme_combo.currentData()
        self._settings.appearance.theme = choice
        self._settings.save()
        self._theme.set_theme(choice)

    def _on_language_changed(self, _i: int) -> None:
        choice = self._lang_combo.currentData()
        self._settings.appearance.language = choice
        self._settings.save()
        set_language(choice)

    # ── i18n ─────────────────────────────────────────────────────────────

    def retranslate(self) -> None:
        self.setWindowTitle(t("settings.title"))
        self._title.setText(t("settings.title"))
        self._nav_buttons[0].setText(t("settings.recording"))
        self._nav_buttons[1].setText(t("settings.appearance"))

        self._rec_title.setText(t("settings.recording"))
        self._rec_sub.setText(t("settings.recording.sub"))
        self._set_field(self._f_hotkey, "settings.hotkey")
        self._set_field(self._f_mode, "settings.capture_mode")
        self._mode_combo.setItemText(0, t("settings.capture_mode.hold"))
        self._mode_combo.setItemText(1, t("settings.capture_mode.toggle"))
        self._set_field(self._f_mic, "settings.microphone")
        self._set_field(self._f_sysaudio, "settings.system_audio")
        self._sysaudio.setText(t("common.on") if self._sysaudio.isChecked() else t("common.off"))
        self._set_field(self._f_pos, "settings.overlay_position")
        for i, pos in enumerate(_OVERLAY_POSITIONS):
            self._pos_combo.setItemText(i, t(f"settings.overlay_position.{pos}"))

        self._app_title.setText(t("settings.appearance"))
        self._app_sub.setText(t("settings.appearance.sub"))
        self._set_field(self._f_theme, "settings.theme")
        for i, name in enumerate(_THEMES):
            self._theme_combo.setItemText(i, t(f"settings.theme.{name}"))
        self._set_field(self._f_lang, "settings.language")

    @staticmethod
    def _set_field(field: tuple[QLabel, QLabel], key: str) -> None:
        label, sub = field
        label.setText(t(key))
        sub.setText(t(f"{key}.sub"))

    # ── dragging (frameless) ─────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 56:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    # ── lifecycle ────────────────────────────────────────────────────────

    def showEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        super().showEvent(event)
        # Clip the card so opaque panes follow the card's rounded corners.
        apply_rounded_mask(self._card, 16)

    def closeEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        self._mic_panel.stop_test()
        if self._backdrop is not None:
            self._backdrop.hide()
        super().closeEvent(event)

    def open_centered(self) -> None:
        """Show centred over the parent window, dimming it behind."""
        parent = self.parentWidget()
        if self._backdrop is not None:
            self._backdrop.show_over()
        if parent is not None:
            geo = parent.frameGeometry()
            self.move(
                geo.x() + (geo.width() - self.width()) // 2,
                geo.y() + (geo.height() - self.height()) // 2,
            )
        self.show()
        self.raise_()
        self.activateWindow()
