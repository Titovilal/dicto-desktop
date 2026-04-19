"""
Main window for Dicto application.
Redesigned to match the dicto web component aesthetic.
"""

from __future__ import annotations

import logging
import os
import sys

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QCheckBox,
    QComboBox,
    QApplication,
    QTextEdit,
    QLineEdit,
    QScrollArea,
)
from PySide6.QtCore import Signal, Slot, Qt, QSize, QUrl, QTimer, QEvent
from PySide6.QtGui import (
    QIcon,
    QPainter,
    QColor,
    QPixmap,
    QDesktopServices,
    QMouseEvent,
)
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.controller import Controller

from src.utils.icons import get_icon_path
from src.i18n import t, set_language
from src.i18n.translations import UI_LANGUAGES
from src.ui.waveform import WaveformWidget
from src.ui.main_window_styles import (
    GLOBAL_STYLE,
    DOT_IDLE,
    DOT_RECORDING,
    DOT_PROCESSING,
    DOT_SUCCESS,
    DOT_EDITING,
    HEADER_BUTTON,
    HEADER_BUTTON_CLOSE,
    HEADER_BUTTON_ACTIVE,
    TAB_BUTTON,
    TAB_BUTTON_ACTIVE,
    TAB_BUTTON_DISABLED,
    CONTENT_TEXT,
    IDLE_TEXT,
    IDLE_TEXT_BOLD,
    RECORDING_LABEL,
    PROCESSING_LABEL,
    EDITING_LABEL,
    TIMER_RECORDING,
    TIMER_PROCESSING,
    TIMER_EDITING,
    RECORD_BUTTON_IDLE,
    RECORD_BUTTON_RECORDING,
    RECORD_BUTTON_PROCESSING,
    RECORD_BUTTON_EDITING,
    FOOTER_TEXT_BUTTON,
    FOOTER_TEXT_BUTTON_SUCCESS,
    SECTION_LABEL,
    FLAT_BUTTON,
    ACCENT_BUTTON,
    SEPARATOR,
    MUTED,
    BORDER,
    TEXT,
    TEXT_DIM,
    RED,
    BLUE,
)
from src.ui.icons import (
    SVG_SETTINGS,
    SVG_CLOSE,
    SVG_EXTERNAL,
    SVG_AUDIO_LINES,
    SVG_MODELS,
    SVG_SPEAKER,
    SVG_SPEAKER_OFF,
)

logger = logging.getLogger(__name__)


def _make_icon(svg_data: str, size: int, color: str) -> QIcon:
    """Create a QIcon from inline SVG data with a given color."""
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    scale = 2
    app = QApplication.instance()
    if app and isinstance(app, QApplication):
        screen = app.primaryScreen()
        if screen:
            scale = max(2, int(screen.devicePixelRatio()))

    colored = svg_data.replace("currentColor", color)
    renderer = QSvgRenderer(colored.encode())
    px = QPixmap(QSize(size * scale, size * scale))
    px.fill(QColor(0, 0, 0, 0))
    painter = QPainter(px)
    renderer.render(painter)
    painter.end()
    px.setDevicePixelRatio(scale)
    icon = QIcon()
    icon.addPixmap(px)
    return icon


class HotkeyButton(QPushButton):
    """A button that captures key combinations when clicked."""

    hotkey_changed = Signal(list, str)  # (modifiers, key)

    # Map Qt modifiers to config-style names
    _MOD_MAP = {
        Qt.KeyboardModifier.ControlModifier: "ctrl",
        Qt.KeyboardModifier.ShiftModifier: "shift",
        Qt.KeyboardModifier.AltModifier: "alt",
        Qt.KeyboardModifier.MetaModifier: "cmd",
    }

    # Map Qt keys to config-style names
    _KEY_MAP = {
        Qt.Key.Key_Space: "space",
        Qt.Key.Key_Return: "enter",
        Qt.Key.Key_Enter: "enter",
        Qt.Key.Key_Tab: "tab",
        Qt.Key.Key_Escape: "esc",
        Qt.Key.Key_Backspace: "backspace",
        Qt.Key.Key_Delete: "delete",
        Qt.Key.Key_Up: "up",
        Qt.Key.Key_Down: "down",
        Qt.Key.Key_Left: "left",
        Qt.Key.Key_Right: "right",
    }

    _MODIFIER_KEYS = {
        Qt.Key.Key_Control,
        Qt.Key.Key_Shift,
        Qt.Key.Key_Alt,
        Qt.Key.Key_Meta,
    }

    def __init__(self, modifiers: list[str], key: str, parent=None):
        super().__init__(parent)
        self._modifiers = modifiers
        self._key = key
        self._listening = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._update_display()
        self.clicked.connect(self._start_listening)

    @staticmethod
    def format_hotkey(modifiers: list[str], key: str) -> str:
        parts = [m.capitalize() for m in modifiers] + [key.capitalize()]
        return "+".join(parts)

    def _update_display(self):
        self.setText(self.format_hotkey(self._modifiers, self._key))

    def _start_listening(self):
        self._listening = True
        self.setText(t("press_combination"))
        self.setFocus()

    def keyPressEvent(self, event):
        if not self._listening:
            super().keyPressEvent(event)
            return

        qt_key = event.key()

        # Ignore lone modifier presses
        if qt_key in self._MODIFIER_KEYS:
            return

        # Escape cancels
        if qt_key == Qt.Key.Key_Escape:
            self._listening = False
            self._update_display()
            return

        # Build modifier list
        mods = event.modifiers()
        modifiers: list[str] = []
        for qt_mod, name in self._MOD_MAP.items():
            if mods & qt_mod:
                modifiers.append(name)

        # Determine key name
        if qt_key in self._KEY_MAP:
            key_name = self._KEY_MAP[qt_key]
        elif Qt.Key.Key_A <= qt_key <= Qt.Key.Key_Z:
            key_name = chr(qt_key).lower()
        elif Qt.Key.Key_0 <= qt_key <= Qt.Key.Key_9:
            key_name = chr(qt_key)
        else:
            key_name = event.text().lower().strip()
            if not key_name:
                return

        self._modifiers = modifiers
        self._key = key_name
        self._listening = False
        self._update_display()
        self.hotkey_changed.emit(modifiers, key_name)

    def focusOutEvent(self, event):
        if self._listening:
            self._listening = False
            self._update_display()
        super().focusOutEvent(event)


class MainWindow(QMainWindow):
    controller: Controller | None
    """Main application window matching the web component design."""

    LANGUAGES = {
        "auto": "Auto-detect (Not Recommended)",
        "es": "Español",
        "en": "English",
        "fr": "Français",
        "de": "Deutsch",
        "it": "Italiano",
        "pt": "Português",
        "zh": "中文",
        "ja": "日本語",
        "ko": "한국어",
    }

    def _get_format_instructions(self):
        instructions = {}
        for p in self._user_presets:
            instructions[f"preset_{p['id']}"] = p["instructions"]
        return instructions

    # Signals
    play_clicked = Signal()
    stop_clicked = Signal()
    cancel_clicked = Signal()
    copy_clicked = Signal()
    transform_requested = Signal(str, str, str)  # (format_id, text, instructions)
    persistent_overlay_changed = Signal(bool)
    recording_hotkey_changed = Signal(list, str)  # (modifiers, key)
    edit_hotkey_changed = Signal(list, str)  # (modifiers, key)
    input_device_changed = Signal(object)  # int or None
    include_system_audio_changed = Signal(bool)
    _test_audio_level = Signal(float)

    FULL_SIZE = (420, 370)

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings
        self.is_recording = False
        self.is_processing = False
        self.last_transcription = ""
        self._drag_pos = None
        self._elapsed_seconds = 0
        self._copied = False
        self._settings_open = False
        self._models_open = False
        self._format_cache: dict[str, str] = {}  # format_id -> transformed text
        self._transforming_format: str | None = None
        self._user_presets: list[dict] = []  # [{id, name, instructions}]
        self.controller = None  # set externally after init
        self._section_labels: dict[str, QLabel] = {}  # key -> section QLabel
        self._hotkey_labels: dict[str, QLabel] = {}  # key -> hotkey row QLabel
        self._audio_monitor = None  # AudioMonitor while test is active
        self._setup_ui()
        self._populate_input_devices()
        self._load_settings()

        # Elapsed timer
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._tick_elapsed)

        # Dot pulse timer
        self._dot_visible = True
        self._dot_pulse_timer = QTimer(self)
        self._dot_pulse_timer.timeout.connect(self._pulse_dot)

    def _setup_ui(self):
        self.setWindowTitle("Dicto")
        self.setFixedSize(468, 438)
        self.setStyleSheet(GLOBAL_STYLE)

        # Frameless window with transparent background for rounded corners
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))

        # Outer container (transparent) gives the shadow room to render
        outer = QWidget()
        outer.setStyleSheet("background: transparent;")
        self.setCentralWidget(outer)
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(24, 20, 24, 28)
        outer_layout.setSpacing(0)

        central_widget = QWidget()
        central_widget.setObjectName("centralCard")
        central_widget.setStyleSheet(
            f"QWidget#centralCard {{ background-color: {MUTED}; border: 1px solid {BORDER}; border-radius: 9px; }}"
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(48)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 110))
        central_widget.setGraphicsEffect(shadow)
        outer_layout.addWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._create_header(main_layout)
        self._create_tabs_bar(main_layout)

        # Content stack
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)

        self._create_idle_page()
        self._create_recording_page()
        self._create_done_page()
        self._create_settings_page()
        self._create_models_page()

        self._create_footer(main_layout)

        # Start on idle
        self.content_stack.setCurrentIndex(0)

    # ── Header ──────────────────────────────────────────────

    def _create_header(self, parent_layout):
        header = QWidget()
        header.setFixedHeight(44)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 12, 0)
        layout.setSpacing(8)

        # Status dot
        self.status_dot = QWidget()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet(DOT_IDLE)
        layout.addWidget(self.status_dot)

        # Title
        title = QLabel("dicto")
        title.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {TEXT}; letter-spacing: -0.5px;"
        )
        layout.addWidget(title)

        # Web button (next to title)
        web_btn = QPushButton()
        web_btn.setFixedSize(28, 28)
        web_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        web_btn.setIcon(_make_icon(SVG_EXTERNAL, 16, TEXT_DIM))
        web_btn.setIconSize(QSize(16, 16))
        web_btn.setStyleSheet(HEADER_BUTTON)
        web_btn.setToolTip(t("go_to_web"))
        web_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl(os.environ.get("DICTO_WEB_URL", "https://app.dicto.io"))
            )
        )
        setattr(web_btn, "_icon_normal", _make_icon(SVG_EXTERNAL, 16, TEXT_DIM))
        setattr(web_btn, "_icon_hover", _make_icon(SVG_EXTERNAL, 16, TEXT))
        web_btn.installEventFilter(self)
        layout.addWidget(web_btn)

        layout.addStretch()

        # Timer label (hidden by default)
        self.timer_label = QLabel("")
        self.timer_label.setStyleSheet(TIMER_RECORDING)
        self.timer_label.hide()
        layout.addWidget(self.timer_label)

        # Models button
        self.models_button = QPushButton()
        self.models_button.setFixedSize(28, 28)
        self.models_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.models_button.setIcon(_make_icon(SVG_MODELS, 16, TEXT_DIM))
        self.models_button.setIconSize(QSize(16, 16))
        self.models_button.setStyleSheet(HEADER_BUTTON)
        self.models_button.setToolTip(t("models"))
        self.models_button.clicked.connect(self._toggle_models)
        setattr(
            self.models_button, "_icon_normal", _make_icon(SVG_MODELS, 16, TEXT_DIM)
        )
        setattr(self.models_button, "_icon_hover", _make_icon(SVG_MODELS, 16, TEXT))
        self.models_button.installEventFilter(self)
        layout.addWidget(self.models_button)

        # Settings button
        self.settings_button = QPushButton()
        self.settings_button.setFixedSize(28, 28)
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.setIcon(_make_icon(SVG_SETTINGS, 16, TEXT_DIM))
        self.settings_button.setIconSize(QSize(16, 16))
        self.settings_button.setStyleSheet(HEADER_BUTTON)
        self.settings_button.setToolTip(t("settings"))
        self.settings_button.clicked.connect(self._toggle_settings)
        setattr(
            self.settings_button, "_icon_normal", _make_icon(SVG_SETTINGS, 16, TEXT_DIM)
        )
        setattr(self.settings_button, "_icon_hover", _make_icon(SVG_SETTINGS, 16, TEXT))
        self.settings_button.installEventFilter(self)
        layout.addWidget(self.settings_button)

        # Close button
        close_btn = QPushButton()
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setIcon(_make_icon(SVG_CLOSE, 16, TEXT_DIM))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setStyleSheet(HEADER_BUTTON_CLOSE)
        close_btn.setToolTip(t("close"))
        close_btn.clicked.connect(self.close)
        setattr(close_btn, "_icon_normal", _make_icon(SVG_CLOSE, 16, TEXT_DIM))
        setattr(close_btn, "_icon_hover", _make_icon(SVG_CLOSE, 16, RED))
        close_btn.installEventFilter(self)
        layout.addWidget(close_btn)

        parent_layout.addWidget(header)

        # Separator line
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {BORDER};")
        parent_layout.addWidget(sep)

    # ── Format Tabs ─────────────────────────────────────────

    def _create_tabs_bar(self, parent_layout):
        self.tabs_bar = QWidget()
        self.tabs_bar.setFixedHeight(38)

        layout = QHBoxLayout(self.tabs_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(6)

        self.format_tabs = []
        # Only "Original" tab by default; user presets are added via set_presets()
        raw_btn = QPushButton(t("tab_original"))
        raw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        raw_btn.setStyleSheet(TAB_BUTTON_ACTIVE)
        raw_btn.setEnabled(True)
        raw_btn.setProperty("format_id", "raw")
        raw_btn.clicked.connect(lambda checked, b=raw_btn: self._on_format_clicked(b))
        self.format_tabs.append(raw_btn)
        layout.addWidget(raw_btn)

        # Loading indicator for presets (removed automatically by _rebuild_format_tabs)
        loading_label = QLabel(t("presets_loading"))
        loading_label.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 12px; padding-left: 4px;"
        )
        self._presets_loading_label = loading_label
        layout.addWidget(loading_label)

        layout.addStretch()
        parent_layout.addWidget(self.tabs_bar)

        # Separator line
        self.tabs_sep = QWidget()
        self.tabs_sep.setFixedHeight(1)
        self.tabs_sep.setStyleSheet(f"background-color: {BORDER};")
        parent_layout.addWidget(self.tabs_sep)

        self._active_format = "raw"

    def _update_tabs_enabled(self, enabled: bool):
        for btn in self.format_tabs:
            fid = btn.property("format_id")
            is_original = fid == "raw"
            if fid == self._active_format:
                btn.setStyleSheet(TAB_BUTTON_ACTIVE)
                btn.setEnabled(True)
            elif enabled:
                btn.setStyleSheet(TAB_BUTTON)
                btn.setEnabled(True)
            else:
                btn.setStyleSheet(TAB_BUTTON_DISABLED)
                # Original tab is always clickable
                btn.setEnabled(is_original)

    def _on_format_clicked(self, btn):
        fid = btn.property("format_id")
        if fid == self._active_format:
            return
        self._active_format = fid
        self._update_tabs_enabled(True)

        if not self.last_transcription:
            return

        if fid == "raw":
            self.transcription_text.setText(self.last_transcription)
            self.copy_button.show()
            return

        # Check cache
        if fid in self._format_cache:
            self.transcription_text.setText(self._format_cache[fid])
            self.copy_button.show()
            return

        # Request transform
        self._transforming_format = fid
        self.transcription_text.setText("")
        self.processing_label.setText(t("transforming"))
        self.processing_label.show()
        self.copy_button.hide()
        self.cancel_button.show()
        self._dots_timer.start(400)

        instructions = self._get_format_instructions().get(fid, "")
        self.transform_requested.emit(fid, self.last_transcription, instructions)

    @Slot(str, str)
    def on_transform_completed(self, format_id: str, text: str):
        self._format_cache[format_id] = text
        self._transforming_format = None
        self._dots_timer.stop()
        self.cancel_button.hide()
        if self._active_format == format_id:
            self.processing_label.hide()
            self.transcription_text.setText(text)
            self.copy_button.show()

    @Slot(str, str)
    def on_transform_failed(self, format_id: str, error: str):
        self._transforming_format = None
        self._dots_timer.stop()
        self.cancel_button.hide()
        if self._active_format == format_id:
            self.processing_label.hide()
            self.transcription_text.setText(f"Error: {error}")
            self.copy_button.hide()

    @Slot(list)
    def set_presets(self, presets: list[dict]):
        """Update format tabs with user's favorite presets from the API."""
        self._user_presets = presets
        if self._presets_loading_label is not None:
            self._presets_loading_label.deleteLater()
            self._presets_loading_label = None
        self._rebuild_format_tabs()

    def _rebuild_format_tabs(self):
        """Rebuild format tabs: Original + default formats + user presets."""
        layout = self.tabs_bar.layout()

        # Remove old buttons
        for btn in self.format_tabs:
            layout.removeWidget(btn)
            btn.deleteLater()
        self.format_tabs.clear()
        self._format_cache.clear()

        # Build format list: Original + user presets
        formats: list[tuple[str, str]] = [("raw", t("tab_original"))]
        for p in self._user_presets:
            formats.append((f"preset_{p['id']}", p["name"]))

        has_text = bool(self.last_transcription)
        for idx, (fid, label) in enumerate(formats):
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            is_raw = fid == "raw"
            is_active = fid == self._active_format
            if is_active:
                btn.setStyleSheet(TAB_BUTTON_ACTIVE)
                btn.setEnabled(True)
            elif has_text or is_raw:
                btn.setStyleSheet(TAB_BUTTON if has_text else TAB_BUTTON_DISABLED)
                btn.setEnabled(has_text or is_raw)
            else:
                btn.setStyleSheet(TAB_BUTTON_DISABLED)
                btn.setEnabled(is_raw)
            btn.setProperty("format_id", fid)
            btn.clicked.connect(lambda checked, b=btn: self._on_format_clicked(b))
            self.format_tabs.append(btn)
            layout.insertWidget(idx, btn)

    # ── Idle Page ───────────────────────────────────────────

    def _create_idle_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(_make_icon(SVG_AUDIO_LINES, 40, TEXT_DIM).pixmap(40, 40))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(8)

        # Text
        text_widget = QWidget()
        text_layout = QHBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl1 = QLabel(t("press"))
        lbl1.setStyleSheet(IDLE_TEXT)
        text_layout.addWidget(lbl1)

        lbl2 = QLabel(t("record"))
        lbl2.setStyleSheet(IDLE_TEXT_BOLD)
        text_layout.addWidget(lbl2)

        lbl3 = QLabel(t("to_start"))
        lbl3.setStyleSheet(IDLE_TEXT)
        text_layout.addWidget(lbl3)

        layout.addWidget(text_widget)
        self.content_stack.addWidget(page)

    # ── Recording Page ──────────────────────────────────────

    def _create_recording_page(self):
        page = QWidget()
        page.setStyleSheet("")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 16, 20, 16)

        self.recording_label = QLabel(t("listening"))
        self.recording_label.setStyleSheet(RECORDING_LABEL)
        layout.addWidget(self.recording_label)

        # Animated dots timer
        self._dots_count = 0
        self._dots_timer = QTimer(self)
        self._dots_timer.timeout.connect(self._animate_dots)

        layout.addStretch()

        self.waveform = WaveformWidget(
            bar_count=18, bar_width=2, bar_gap=2, height=28, mode="live"
        )
        layout.addWidget(self.waveform, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        self.content_stack.addWidget(page)

    def _animate_dots(self):
        self._dots_count = (self._dots_count + 1) % 4
        dots = "." * self._dots_count + "\u00a0" * (3 - self._dots_count)
        if self.is_recording and getattr(self, "_is_editing", False):
            self.recording_label.setText(f"{t('listening')}{dots}")
        elif self.is_recording:
            self.recording_label.setText(f"{t('listening')}{dots}")
        elif self.is_processing and getattr(self, "_is_editing", False):
            self.processing_label.setText(f"{t('editing')}{dots}")
        elif self.is_processing:
            self.processing_label.setText(f"{t('processing')}{dots}")
        elif self._transforming_format is not None:
            self.processing_label.setText(f"{t('transforming')}{dots}")

    # ── Done Page ───────────────────────────────────────────

    def _create_done_page(self):
        page = QWidget()
        page.setStyleSheet("")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 16, 20, 16)

        # Processing label (shown before text arrives, at top)
        self.processing_label = QLabel(t("processing"))
        self.processing_label.setStyleSheet(PROCESSING_LABEL)
        self.processing_label.hide()
        layout.addWidget(self.processing_label)

        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setStyleSheet(CONTENT_TEXT)
        self.transcription_text.setFrameShape(QTextEdit.Shape.NoFrame)
        self.transcription_text.verticalScrollBar().setSingleStep(15)
        layout.addWidget(self.transcription_text)

        self.content_stack.addWidget(page)

    # ── Settings Page ───────────────────────────────────────

    def _add_checkbox(self, layout, label_key: str, callback) -> QCheckBox:
        """Create a checkbox, connect its signal, add to layout, and return it."""
        cb = QCheckBox(t(label_key))
        cb.stateChanged.connect(callback)
        layout.addWidget(cb)
        return cb

    def _add_combo(self, layout, items: dict, callback) -> QComboBox:
        """Create a combo box with items, connect its signal, add to layout, and return it."""
        combo = QComboBox()
        combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        setattr(combo, "wheelEvent", lambda e: e.ignore())
        for value, label in items.items():
            combo.addItem(label, value)
        combo.currentIndexChanged.connect(callback)
        layout.addWidget(combo)
        return combo

    def _add_section(self, layout, title_key: str):
        """Add a section separator + label to layout."""
        layout.addSpacing(12)
        layout.addWidget(self._make_separator())
        layout.addSpacing(12)
        label = self._section_label(t(title_key))
        self._section_labels[title_key] = label
        layout.addWidget(label)
        layout.addSpacing(6)

    def _add_hotkey_row(
        self, layout, label_key: str, modifiers: list[str], key: str, callback
    ) -> HotkeyButton:
        """Create a labeled hotkey button row."""
        row = QHBoxLayout()
        row.setSpacing(8)
        label = QLabel(t(label_key))
        label.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
        label.setFixedWidth(120)
        self._hotkey_labels[label_key] = label
        row.addWidget(label)

        btn = HotkeyButton(modifiers, key)
        btn.setFixedHeight(32)
        btn.setStyleSheet(FLAT_BUTTON)
        btn.hotkey_changed.connect(callback)
        row.addWidget(btn)
        layout.addLayout(row)
        return btn

    def _create_scroll_page(self):
        """Create a scrollable page and return (page, layout) for adding content."""
        page = QWidget()
        page.setStyleSheet("background-color: transparent;")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background-color: transparent; }
            QScrollBar:vertical { width: 6px; background-color: transparent; }
            QScrollBar::handle:vertical { background-color: rgba(255,255,255,0.15); border-radius: 3px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.verticalScrollBar().setSingleStep(15)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        scroll.setWidget(scroll_content)
        page_layout.addWidget(scroll)
        return page, layout

    def _create_settings_page(self):
        page, layout = self._create_scroll_page()

        # API Key (first — essential to get started)
        api_key_label = self._section_label(t("api_key"))
        self._section_labels["api_key"] = api_key_label
        layout.addWidget(api_key_label)
        layout.addSpacing(6)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-dicto-...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_key_input)
        layout.addSpacing(8)

        self.save_api_key_button = QPushButton(t("save_key"))
        self.save_api_key_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_api_key_button.setFixedHeight(32)
        self.save_api_key_button.setStyleSheet(ACCENT_BUTTON)
        self.save_api_key_button.clicked.connect(self._on_save_api_key)
        layout.addWidget(self.save_api_key_button)

        # Keyboard shortcuts
        self._add_section(layout, "keyboard_shortcuts")
        layout.addSpacing(2)
        rec_mods = (
            self.settings.hotkey_modifiers if self.settings else ["ctrl", "shift"]
        )
        rec_key = self.settings.hotkey_key if self.settings else "space"
        self.recording_hotkey_button = self._add_hotkey_row(
            layout,
            "hotkey_record",
            rec_mods,
            rec_key,
            self._on_recording_hotkey_changed,
        )
        layout.addSpacing(6)
        edit_mods = (
            self.settings.edit_hotkey_modifiers if self.settings else ["ctrl", "alt"]
        )
        edit_key = self.settings.edit_hotkey_key if self.settings else "space"
        self.edit_hotkey_button = self._add_hotkey_row(
            layout,
            "hotkey_edit_selection",
            edit_mods,
            edit_key,
            self._on_edit_hotkey_changed,
        )

        # Behavior (transcription + edit selection together)
        self._add_section(layout, "behavior")
        self.auto_paste_checkbox = self._add_checkbox(
            layout, "auto_paste_after_transcribe", self._on_auto_paste_changed
        )
        self.auto_enter_checkbox = self._add_checkbox(
            layout, "press_enter_after_paste", self._on_auto_enter_changed
        )

        # Edit selection
        self._add_section(layout, "edit_selection")
        self.edit_auto_paste_checkbox = self._add_checkbox(
            layout, "auto_paste_after_edit", self._on_edit_auto_paste_changed
        )
        self.edit_auto_enter_checkbox = self._add_checkbox(
            layout, "press_enter_after_paste", self._on_edit_auto_enter_changed
        )

        # Audio input
        self._add_section(layout, "audio_input")
        self.input_device_combo = QComboBox()
        self.input_device_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Prevent long device names from expanding the combo (and the whole page) beyond the window width.
        self.input_device_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.input_device_combo.setMinimumContentsLength(10)
        setattr(self.input_device_combo, "wheelEvent", lambda e: e.ignore())
        self.input_device_combo.currentIndexChanged.connect(
            self._on_input_device_changed
        )
        layout.addWidget(self.input_device_combo)
        layout.addSpacing(4)
        self.test_audio_button = QPushButton(t("test_audio"))
        self.test_audio_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_audio_button.setFixedHeight(32)
        self.test_audio_button.setStyleSheet(FLAT_BUTTON)
        self.test_audio_button.clicked.connect(self._on_test_audio_clicked)
        layout.addWidget(self.test_audio_button)
        layout.addSpacing(6)
        self.test_audio_waveform = WaveformWidget(
            bar_count=32, bar_width=2, bar_gap=2, height=28, mode="live"
        )
        self.test_audio_waveform.hide()
        layout.addWidget(self.test_audio_waveform)
        self._test_audio_level.connect(
            self.test_audio_waveform.set_level, Qt.ConnectionType.QueuedConnection
        )

        # Window (application + overlay merged)
        self._add_section(layout, "application")
        self.always_on_top_checkbox = self._add_checkbox(
            layout, "always_on_top", self._on_always_on_top_changed
        )
        self.persistent_overlay_checkbox = self._add_checkbox(
            layout, "persistent_overlay", self._on_persistent_overlay_changed
        )

        # UI Language (rarely changed)
        self._add_section(layout, "ui_language")
        self.ui_language_combo = self._add_combo(
            layout, UI_LANGUAGES, self._on_ui_language_changed
        )

        # Report error
        self._add_section(layout, "report_error")
        self._report_desc_label = QLabel(t("report_error_description"))
        self._report_desc_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
        self._report_desc_label.setWordWrap(True)
        layout.addWidget(self._report_desc_label)
        layout.addSpacing(8)
        self.send_report_button = QPushButton(t("send_report"))
        self.send_report_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_report_button.setFixedHeight(32)
        self.send_report_button.setStyleSheet(FLAT_BUTTON)
        self.send_report_button.clicked.connect(self._send_report)
        layout.addWidget(self.send_report_button)
        self.report_status_label = QLabel("")
        self.report_status_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        self.report_status_label.hide()
        layout.addWidget(self.report_status_label)

        layout.addStretch()
        self.content_stack.addWidget(page)

    def _create_models_page(self):
        page, layout = self._create_scroll_page()

        # Transcription model
        transcription_model_label = self._section_label(t("transcription_model"))
        self._section_labels["transcription_model"] = transcription_model_label
        layout.addWidget(transcription_model_label)
        layout.addSpacing(6)
        self.model_combo = self._add_combo(
            layout,
            {
                "v3-turbo": "Whisper V3 Turbo",
                "v3": f"Whisper V3 ({t('recommended')})",
                "gemini-3-flash-preview": "Gemini 3 Flash",
                "gemini-3.1-flash-lite-preview": "Gemini 3.1 Flash Lite",
            },
            self._on_model_changed,
        )

        # Transcription language
        self._add_section(layout, "transcription_language")
        self.language_combo = self._add_combo(
            layout, self.LANGUAGES, self._on_language_changed
        )

        # Transformation model
        self._add_section(layout, "transformation_model")
        self.transformation_model_combo = self._add_combo(
            layout,
            {
                "qwen/qwen3-32b": "Qwen 3 32B",
                "openai/gpt-oss-120b": f"GPT OSS 120B ({t('recommended')})",
                "openai/gpt-oss-20b": "GPT OSS 20B",
                "gemini-3-flash-preview": "Gemini 3 Flash",
                "gemini-3.1-flash-lite-preview": "Gemini 3.1 Flash Lite",
            },
            self._on_transformation_model_changed,
        )

        # Edition model
        self._add_section(layout, "edition_model")
        self.edition_model_combo = self._add_combo(
            layout,
            {
                "qwen/qwen3-32b": f"Qwen 3 32B ({t('recommended')})",
                "openai/gpt-oss-120b": "GPT OSS 120B",
                "openai/gpt-oss-20b": "GPT OSS 20B",
                "gemini-3-flash-preview": "Gemini 3 Flash",
                "gemini-3.1-flash-lite-preview": "Gemini 3.1 Flash Lite",
            },
            self._on_edition_model_changed,
        )

        layout.addStretch()
        self.content_stack.addWidget(page)

    # ── Footer ──────────────────────────────────────────────

    def _create_footer(self, parent_layout):
        # Separator line before footer
        self.footer_sep = QWidget()
        self.footer_sep.setFixedHeight(1)
        self.footer_sep.setStyleSheet(f"background-color: {BORDER};")
        parent_layout.addWidget(self.footer_sep)

        self.footer = QWidget()
        self.footer.setFixedHeight(50)

        layout = QHBoxLayout(self.footer)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(4)

        self.record_button = QPushButton(t("record"))
        self.record_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_button.setStyleSheet(RECORD_BUTTON_IDLE)
        self.record_button.clicked.connect(self._on_play_stop_clicked)
        layout.addWidget(self.record_button)

        self.copy_button = QPushButton(t("copy"))
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setStyleSheet(FOOTER_TEXT_BUTTON)
        self.copy_button.clicked.connect(self._on_copy_clicked)
        self.copy_button.hide()
        layout.addWidget(self.copy_button)

        self.cancel_button = QPushButton(t("cancel"))
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setStyleSheet(FOOTER_TEXT_BUTTON)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.cancel_button.hide()
        layout.addWidget(self.cancel_button)

        layout.addStretch()

        # Status label (for settings feedback, right-aligned)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.status_label)

        self.include_system_audio_checkbox = QPushButton()
        self.include_system_audio_checkbox.setCheckable(True)
        self.include_system_audio_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.include_system_audio_checkbox.setFixedSize(32, 32)
        self.include_system_audio_checkbox.setToolTip(t("include_system_audio"))
        self.include_system_audio_checkbox.setStyleSheet(HEADER_BUTTON)
        self.include_system_audio_checkbox.toggled.connect(
            self._on_include_system_audio_changed
        )
        self.include_system_audio_checkbox.toggled.connect(
            self._update_include_system_audio_icon
        )
        if sys.platform == "darwin":
            self.include_system_audio_checkbox.setEnabled(False)
            self.include_system_audio_checkbox.setToolTip(
                t("system_audio_unsupported")
            )
        self._update_include_system_audio_icon(False)
        layout.addWidget(self.include_system_audio_checkbox)

        parent_layout.addWidget(self.footer)

    # ── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setStyleSheet(SECTION_LABEL)
        return label

    @staticmethod
    def _make_separator() -> QWidget:
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(SEPARATOR)
        return sep

    def eventFilter(self, obj, event):
        if hasattr(obj, "_icon_hover"):
            if event.type() == QEvent.Type.Enter:
                obj.setIcon(getattr(obj, "_icon_hover"))
            elif event.type() == QEvent.Type.Leave:
                # Don't reset to dim if this button's panel is active
                if obj is self.models_button and self._models_open:
                    pass
                elif obj is self.settings_button and self._settings_open:
                    pass
                else:
                    obj.setIcon(getattr(obj, "_icon_normal"))
        return super().eventFilter(obj, event)

    def _format_elapsed(self) -> str:
        m = self._elapsed_seconds // 60
        s = self._elapsed_seconds % 60
        return f"{m:02d}:{s:02d}"

    def _tick_elapsed(self):
        self._elapsed_seconds += 1
        self.timer_label.setText(self._format_elapsed())

    def _pulse_dot(self):
        self._dot_visible = not self._dot_visible
        if self._dot_visible:
            if self.is_recording:
                self.status_dot.setStyleSheet(DOT_RECORDING)
            elif self.is_processing:
                self.status_dot.setStyleSheet(DOT_PROCESSING)
        else:
            self.status_dot.setStyleSheet(
                "background-color: transparent; border-radius: 4px;"
            )

    def _toggle_settings(self):
        if self._settings_open:
            self._close_panel()
        else:
            if self._models_open:
                self._close_panel()
            self._open_settings()

    def _toggle_models(self):
        if self._models_open:
            self._close_panel()
        else:
            if self._settings_open:
                self._close_panel()
            self._open_models()

    def _open_settings(self):
        self._settings_open = True
        self._prev_page = self.content_stack.currentIndex()
        self.content_stack.setCurrentIndex(3)  # settings page
        self.settings_button.setIcon(_make_icon(SVG_SETTINGS, 16, TEXT))
        self.settings_button.setStyleSheet(HEADER_BUTTON_ACTIVE)
        self.footer.hide()
        self.footer_sep.hide()
        self.tabs_bar.hide()
        self.tabs_sep.hide()

    def _open_models(self):
        self._models_open = True
        self._prev_page = self.content_stack.currentIndex()
        self.content_stack.setCurrentIndex(4)  # models page
        self.models_button.setIcon(_make_icon(SVG_MODELS, 16, TEXT))
        self.models_button.setStyleSheet(HEADER_BUTTON_ACTIVE)
        self.footer.hide()
        self.footer_sep.hide()
        self.tabs_bar.hide()
        self.tabs_sep.hide()

    def _send_report(self):
        import httpx
        from src.utils.logger import get_log_buffer

        self.send_report_button.setEnabled(False)
        self.report_status_label.hide()
        logs = "\n".join(get_log_buffer())

        try:
            api_key = self.settings.transcription_api_key if self.settings else ""
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            base_url = os.environ.get("DICTO_API_URL", "https://dicto.up.railway.app")
            response = httpx.post(
                f"{base_url}/api/report",
                headers=headers,
                json={"logs": logs, "source": "desktop_app"},
                timeout=15.0,
            )
            if response.status_code in (200, 201):
                self.report_status_label.setText(t("report_sent"))
                self.report_status_label.setStyleSheet("color: #4ade80; font-size: 11px;")
            else:
                self.report_status_label.setText(t("report_send_failed"))
                self.report_status_label.setStyleSheet(f"color: {RED}; font-size: 11px;")
        except Exception:
            self.report_status_label.setText(t("report_send_failed"))
            self.report_status_label.setStyleSheet(f"color: {RED}; font-size: 11px;")

        self.report_status_label.show()
        self.send_report_button.setEnabled(True)

    def _close_panel(self):
        self._settings_open = False
        self._models_open = False
        self.content_stack.setCurrentIndex(getattr(self, "_prev_page", 0))
        self.settings_button.setIcon(_make_icon(SVG_SETTINGS, 16, TEXT_DIM))
        self.settings_button.setStyleSheet(HEADER_BUTTON)
        self.models_button.setIcon(_make_icon(SVG_MODELS, 16, TEXT_DIM))
        self.models_button.setStyleSheet(HEADER_BUTTON)
        self.footer.show()
        self.footer_sep.show()
        self.tabs_bar.show()
        self.tabs_sep.show()

    # ── Load settings ───────────────────────────────────────

    def _populate_input_devices(self):
        """Populate input device combo with available microphones."""
        from src.services.recorder import list_input_devices

        self.input_device_combo.blockSignals(True)
        self.input_device_combo.clear()
        self.input_device_combo.addItem(t("system_default"), None)
        for dev in list_input_devices():
            suffix = f" ({t('default')})" if dev["is_default"] else ""
            self.input_device_combo.addItem(f"{dev['name']}{suffix}", dev["id"])
        self.input_device_combo.blockSignals(False)

    def _load_settings(self):
        if not self.settings:
            return

        current_device = self.settings.audio_input_device
        idx = self.input_device_combo.findData(current_device)
        if idx < 0:
            idx = 0
        self.input_device_combo.setCurrentIndex(idx)
        self.include_system_audio_checkbox.setChecked(
            self.settings.audio_include_system_audio
        )

        self.auto_paste_checkbox.setChecked(self.settings.auto_paste)
        self.auto_enter_checkbox.setChecked(self.settings.auto_enter)

        self.always_on_top_checkbox.setChecked(self.settings.always_on_top)
        self.persistent_overlay_checkbox.setChecked(self.settings.persistent_overlay)
        if self.settings.always_on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        current_language = self.settings.transcription_language
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        current_model = self.settings.transcription_model
        model_index = self.model_combo.findData(current_model)
        if model_index >= 0:
            self.model_combo.setCurrentIndex(model_index)

        current_transform_model = self.settings.transformation_model
        transform_index = self.transformation_model_combo.findData(
            current_transform_model
        )
        if transform_index >= 0:
            self.transformation_model_combo.setCurrentIndex(transform_index)

        current_edition_model = self.settings.edition_model
        edition_index = self.edition_model_combo.findData(current_edition_model)
        if edition_index >= 0:
            self.edition_model_combo.setCurrentIndex(edition_index)

        if self.settings.transcription_api_key:
            self.api_key_input.setText(self.settings.transcription_api_key)

        # Edit selection settings
        self.edit_auto_paste_checkbox.setChecked(self.settings.edit_auto_paste)
        self.edit_auto_enter_checkbox.setChecked(self.settings.edit_auto_enter)

        # UI Language
        ui_lang_index = self.ui_language_combo.findData(self.settings.ui_language)
        if ui_lang_index >= 0:
            self.ui_language_combo.setCurrentIndex(ui_lang_index)

    # ── Mouse dragging (frameless window) ───────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

    # ── Slots ───────────────────────────────────────────────

    @Slot()
    def _on_play_stop_clicked(self):
        if self.is_recording:
            self.stop_clicked.emit()
        else:
            self.play_clicked.emit()

    @Slot()
    def _on_cancel_clicked(self):
        self.cancel_clicked.emit()

    @Slot()
    def _on_copy_clicked(self):
        text_to_copy = self._get_current_text()
        if text_to_copy:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text_to_copy)
                self._copied = True
                self.copy_button.setText(t("copied"))
                self.copy_button.setStyleSheet(FOOTER_TEXT_BUTTON_SUCCESS)
                QTimer.singleShot(2000, self._reset_copy_button)
                logger.info("Last transcription copied to clipboard")
        self.copy_clicked.emit()

    def _get_current_text(self) -> str:
        """Return the text currently displayed (raw or transformed)."""
        if self._active_format == "raw":
            return self.last_transcription
        return self._format_cache.get(self._active_format, self.last_transcription)

    def _reset_copy_button(self):
        self._copied = False
        self.copy_button.setText(t("copy"))
        self.copy_button.setStyleSheet(FOOTER_TEXT_BUTTON)

    def _save_setting(self, attr: str, value):
        """Save a setting attribute and persist to disk."""
        if self.settings:
            setattr(self.settings, attr, value)
            self.settings.save()

    def _on_auto_paste_changed(self, state: int):
        self._save_setting("auto_paste", state == Qt.CheckState.Checked.value)

    def _on_auto_enter_changed(self, state: int):
        self._save_setting("auto_enter", state == Qt.CheckState.Checked.value)

    def _on_always_on_top_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()
        self._save_setting("always_on_top", checked)

    def _on_language_changed(self, index: int):
        self._save_setting(
            "transcription_language", self.language_combo.itemData(index)
        )

    def _on_persistent_overlay_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        self._save_setting("persistent_overlay", checked)
        self.persistent_overlay_changed.emit(checked)

    def sync_persistent_overlay_checkbox(self, checked: bool):
        """Update the checkbox without re-triggering the save/emit cycle."""
        self.persistent_overlay_checkbox.blockSignals(True)
        self.persistent_overlay_checkbox.setChecked(checked)
        self.persistent_overlay_checkbox.blockSignals(False)

    def _on_input_device_changed(self, index: int):
        device_id = self.input_device_combo.itemData(index)
        self._save_setting("audio_input_device", device_id)
        self.input_device_changed.emit(device_id)
        if self._audio_monitor and self._audio_monitor.is_running:
            self._stop_audio_monitor()
            self._start_audio_monitor()

    def _update_include_system_audio_icon(self, checked: bool):
        svg = SVG_SPEAKER if checked else SVG_SPEAKER_OFF
        color = TEXT if checked else TEXT_DIM
        self.include_system_audio_checkbox.setIcon(_make_icon(svg, 16, color))

    def _on_include_system_audio_changed(self, checked: bool):
        self._save_setting("audio_include_system_audio", checked)
        self.include_system_audio_changed.emit(checked)
        if self._audio_monitor and self._audio_monitor.is_running:
            self._stop_audio_monitor()
            self._start_audio_monitor()

    def _on_test_audio_clicked(self):
        if self._audio_monitor and self._audio_monitor.is_running:
            self._stop_audio_monitor()
        else:
            self._start_audio_monitor()

    def _start_audio_monitor(self):
        from src.services.recorder import AudioMonitor

        if self._audio_monitor and self._audio_monitor.is_running:
            return
        sample_rate = self.settings.audio_sample_rate if self.settings else 16000
        device = self.settings.audio_input_device if self.settings else None
        include_sys = (
            self.settings.audio_include_system_audio if self.settings else False
        )
        self._audio_monitor = AudioMonitor(
            sample_rate=sample_rate,
            input_device=device,
            include_system_audio=include_sys,
        )
        self._audio_monitor.set_level_callback(self._on_test_audio_level)
        self.test_audio_waveform.start()
        self.test_audio_waveform.show()
        if self._audio_monitor.start():
            self.test_audio_button.setText(t("test_audio_stop"))
        else:
            self._audio_monitor = None
            self.test_audio_waveform.stop()
            self.test_audio_waveform.hide()
            self.status_label.setText(t("test_audio_failed"))

    def _stop_audio_monitor(self):
        if self._audio_monitor:
            self._audio_monitor.stop()
            self._audio_monitor = None
        self.test_audio_button.setText(t("test_audio"))
        self.test_audio_waveform.stop()
        self.test_audio_waveform.hide()

    def _on_test_audio_level(self, level: float):
        self._test_audio_level.emit(level)

    def _on_edit_auto_paste_changed(self, state: int):
        self._save_setting("edit_auto_paste", state == Qt.CheckState.Checked.value)

    def _on_edit_auto_enter_changed(self, state: int):
        self._save_setting("edit_auto_enter", state == Qt.CheckState.Checked.value)

    @Slot(int)
    def _on_ui_language_changed(self, index: int):
        lang_code = self.ui_language_combo.itemData(index)
        if lang_code and self.settings:
            set_language(lang_code)
            self.settings.ui_language = lang_code
            self.settings.save()
            self._retranslate_ui()

    def _retranslate_ui(self):
        """Update all visible text after language change."""
        # Footer buttons
        self.record_button.setText(t("record"))
        self.copy_button.setText(t("copy"))
        self.cancel_button.setText(t("cancel"))

        # Settings page checkboxes
        self.auto_paste_checkbox.setText(t("auto_paste_after_transcribe"))
        self.auto_enter_checkbox.setText(t("press_enter_after_paste"))
        self.always_on_top_checkbox.setText(t("always_on_top"))
        self.persistent_overlay_checkbox.setText(t("persistent_overlay"))
        self.edit_auto_paste_checkbox.setText(t("auto_paste_after_edit"))
        self.edit_auto_enter_checkbox.setText(t("press_enter_after_paste"))
        self.save_api_key_button.setText(t("save_key"))
        if sys.platform == "darwin":
            self.include_system_audio_checkbox.setToolTip(
                t("system_audio_unsupported")
            )
        else:
            self.include_system_audio_checkbox.setToolTip(t("include_system_audio"))
        if self._audio_monitor and self._audio_monitor.is_running:
            self.test_audio_button.setText(t("test_audio_stop"))
        else:
            self.test_audio_button.setText(t("test_audio"))

        # Toolbar tooltips
        self.settings_button.setToolTip(t("settings"))
        self.models_button.setToolTip(t("models"))
        self.send_report_button.setText(t("send_report"))
        self._report_desc_label.setText(t("report_error_description"))

        # Section labels
        for key, label in self._section_labels.items():
            label.setText(t(key).upper())

        # Hotkey row labels
        for key, label in self._hotkey_labels.items():
            label.setText(t(key))

        # Format tabs (default tab labels are translated)
        self._rebuild_format_tabs()

    def _on_model_changed(self, index: int):
        self._save_setting("transcription_model", self.model_combo.itemData(index))

    def _on_transformation_model_changed(self, index: int):
        value = self.transformation_model_combo.itemData(index)
        self._save_setting("transformation_model", value)
        if self.controller and self.controller.transcriber:
            self.controller.transcriber.transformation_model = value

    def _on_edition_model_changed(self, index: int):
        value = self.edition_model_combo.itemData(index)
        self._save_setting("edition_model", value)
        if self.controller and self.controller.transcriber:
            self.controller.transcriber.edition_model = value

    @Slot(list, str)
    def _on_recording_hotkey_changed(self, modifiers: list[str], key: str):
        if self.settings:
            self.settings.hotkey_modifiers = modifiers
            self.settings.hotkey_key = key
            self.settings.save()
        self.recording_hotkey_changed.emit(modifiers, key)

    @Slot(list, str)
    def _on_edit_hotkey_changed(self, modifiers: list[str], key: str):
        if self.settings:
            self.settings.edit_hotkey_modifiers = modifiers
            self.settings.edit_hotkey_key = key
            self.settings.save()
        self.edit_hotkey_changed.emit(modifiers, key)

    @Slot()
    def _on_save_api_key(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.status_label.setText(t("api_key_empty"))
            return
        if not api_key.startswith("sk-dicto-"):
            self.status_label.setText(t("api_key_invalid"))
            return
        if self.settings:
            self.settings.transcription_api_key = api_key
            self.settings.save()
            self.status_label.setText(t("api_key_saved"))
            logger.info("Dicto API key saved")

    # ── State updates ───────────────────────────────────────

    @Slot(str)
    def update_status(self, status: str):
        self.status_label.setText(status.capitalize())

    @Slot()
    def set_recording_state(self):
        self.is_recording = True
        self.is_processing = False
        self._is_editing = False

        # If settings are open, don't switch the view — just remember the target page
        if self._settings_open or self._models_open:
            self._prev_page = 1  # recording page
        else:
            self.content_stack.setCurrentIndex(1)  # recording page
        self.recording_label.setText(t("listening"))
        self.recording_label.setStyleSheet(RECORDING_LABEL)
        self.record_button.setText(t("stop"))
        self.record_button.setStyleSheet(RECORD_BUTTON_RECORDING)
        self.copy_button.hide()
        self.cancel_button.show()
        self.status_label.setText("")

        # Status dot
        self.status_dot.setStyleSheet(DOT_RECORDING)
        self._dot_pulse_timer.start(500)

        # Timer
        self._elapsed_seconds = 0
        self.timer_label.setText("00:00")
        self.timer_label.setStyleSheet(TIMER_RECORDING)
        self.timer_label.show()
        self._elapsed_timer.start(1000)

        # Waveform
        self.waveform.color = RED
        self.waveform.start()

        # Dots animation
        self._dots_timer.start(400)

        # Tabs
        self._update_tabs_enabled(False)

    @Slot()
    def set_idle_state(self):
        self.is_recording = False
        self.is_processing = False
        self._is_editing = False

        # If settings are open, don't switch the view — just remember the target page
        if self._settings_open or self._models_open:
            self._prev_page = 2 if self.last_transcription else 0
        else:
            if self.last_transcription:
                self.content_stack.setCurrentIndex(2)  # done page
            else:
                self.content_stack.setCurrentIndex(0)  # idle page

        self.record_button.setText(t("record"))
        self.record_button.setStyleSheet(RECORD_BUTTON_IDLE)
        self.processing_label.hide()
        self.cancel_button.hide()
        self.status_label.setText("")

        # Stop timers
        self._elapsed_timer.stop()
        self._dot_pulse_timer.stop()
        self._dots_timer.stop()
        self.timer_label.hide()
        self.waveform.stop()

        # Status dot
        self.status_dot.setStyleSheet(DOT_IDLE)

        # Tabs
        if self.last_transcription:
            self._update_tabs_enabled(True)
        else:
            self.copy_button.hide()
            self._update_tabs_enabled(False)

    @Slot()
    def set_processing_state(self):
        self.is_recording = False
        self.is_processing = True

        # If settings are open, don't switch the view — just remember the target page
        if self._settings_open or self._models_open:
            self._prev_page = 2  # done page
        else:
            self.content_stack.setCurrentIndex(2)  # done page
        self.transcription_text.clear()
        self.processing_label.setText(t("processing"))
        self.processing_label.setStyleSheet(PROCESSING_LABEL)
        self.processing_label.show()
        self.record_button.setText(t("processing_ellipsis"))
        self.record_button.setStyleSheet(RECORD_BUTTON_PROCESSING)
        self.copy_button.hide()
        self.cancel_button.show()

        # Stop recording animations
        self.waveform.stop()

        # Timer continues but changes color
        self._elapsed_seconds = 0
        self.timer_label.setText("00:00")
        self.timer_label.setStyleSheet(TIMER_PROCESSING)
        self.timer_label.show()
        self._elapsed_timer.start(1000)

        # Dot
        self.status_dot.setStyleSheet(DOT_PROCESSING)
        self._dot_pulse_timer.start(500)

    @Slot()
    def set_editing_state(self):
        """Show editing state (recording voice instructions for edit)."""
        self.is_recording = True
        self.is_processing = False
        self._is_editing = True

        if self._settings_open or self._models_open:
            self._prev_page = 1
        else:
            self.content_stack.setCurrentIndex(1)  # recording page
        self.recording_label.setText(t("listening"))
        self.recording_label.setStyleSheet(EDITING_LABEL)
        self.record_button.setText(t("stop"))
        self.record_button.setStyleSheet(RECORD_BUTTON_EDITING)
        self.copy_button.hide()
        self.cancel_button.show()
        self.status_label.setText("")

        # Status dot
        self.status_dot.setStyleSheet(DOT_EDITING)
        self._dot_pulse_timer.start(500)

        # Timer
        self._elapsed_seconds = 0
        self.timer_label.setText("00:00")
        self.timer_label.setStyleSheet(TIMER_EDITING)
        self.timer_label.show()
        self._elapsed_timer.start(1000)

        # Waveform in blue
        self.waveform.color = BLUE
        self.waveform.start()

        # Dots animation
        self._dots_timer.start(400)

        # Tabs
        self._update_tabs_enabled(False)

    @Slot()
    def set_editing_processing_state(self):
        """Show processing state during edit flow (blue instead of amber)."""
        self.is_recording = False
        self.is_processing = True
        self._is_editing = True

        if self._settings_open or self._models_open:
            self._prev_page = 2
        else:
            self.content_stack.setCurrentIndex(2)
        self.transcription_text.clear()
        self.processing_label.show()
        self.processing_label.setText(t("editing"))
        self.processing_label.setStyleSheet(EDITING_LABEL)
        self.record_button.setText(t("processing_ellipsis"))
        self.record_button.setStyleSheet(RECORD_BUTTON_EDITING)
        self.copy_button.hide()
        self.cancel_button.show()

        # Stop recording animations
        self.waveform.stop()
        self.waveform.color = RED  # Reset color for next recording

        # Timer
        self._elapsed_seconds = 0
        self.timer_label.setText("00:00")
        self.timer_label.setStyleSheet(TIMER_EDITING)
        self.timer_label.show()
        self._elapsed_timer.start(1000)

        # Dot
        self.status_dot.setStyleSheet(DOT_EDITING)
        self._dot_pulse_timer.start(500)

        # Dots animation
        self._dots_timer.start(400)

        # Tabs
        self._update_tabs_enabled(False)

    @Slot(str)
    def update_transcription(self, text: str):
        self.last_transcription = text
        self.is_processing = False
        self._format_cache.clear()
        self._transforming_format = None

        # If settings are open, don't switch the view — just remember the target page
        if self._settings_open or self._models_open:
            self._prev_page = 2  # done page
        else:
            self.content_stack.setCurrentIndex(2)
        self.processing_label.hide()
        self.transcription_text.setText(text)

        # Button states
        self.record_button.setText(t("record"))
        self.record_button.setStyleSheet(RECORD_BUTTON_IDLE)
        self.cancel_button.hide()
        self.copy_button.setText(t("copy"))
        self.copy_button.setStyleSheet(FOOTER_TEXT_BUTTON)
        self.copy_button.show()

        # Stop timers
        self._elapsed_timer.stop()
        self._dot_pulse_timer.stop()
        self._dots_timer.stop()
        self.timer_label.hide()

        # Dot
        self.status_dot.setStyleSheet(DOT_SUCCESS)

        # Tabs
        self._active_format = "raw"
        self._update_tabs_enabled(True)

    @Slot()
    def show_settings_tab(self):
        self._open_settings()
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if self._audio_monitor and self._audio_monitor.is_running:
            self._stop_audio_monitor()
        event.ignore()
        self.hide()
        logger.info("Main window hidden to tray")
