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
from PySide6.QtCore import Signal, Slot, Qt, QSize, QUrl, QTimer, QEvent, QThread
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
    HEADER_BUTTON,
    HEADER_BUTTON_CLOSE,
    HEADER_BUTTON_ACTIVE,
    TAB_BUTTON,
    TAB_BUTTON_ACTIVE,
    TAB_BUTTON_DISABLED,
    CONTENT_TEXT,
    LOG_VIEW,
    IDLE_TEXT,
    IDLE_TEXT_BOLD,
    RECORDING_LABEL,
    PROCESSING_LABEL,
    TIMER_RECORDING,
    TIMER_PROCESSING,
    RECORD_BUTTON_IDLE,
    RECORD_BUTTON_RECORDING,
    RECORD_BUTTON_PROCESSING,
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
)
from src.ui.icons import (
    SVG_SETTINGS,
    SVG_CLOSE,
    SVG_EXTERNAL,
    SVG_AUDIO_LINES,
    SVG_MODELS,
    SVG_SPEAKER,
    SVG_SPEAKER_OFF,
    SVG_PIN,
    SVG_OPENAI,
    SVG_GOOGLEGEMINI,
    SVG_QWEN,
    SVG_RECORD,
    SVG_STOP,
    SVG_RESET,
    SVG_LOADER,
)

logger = logging.getLogger(__name__)


_icon_cache: dict[tuple[str, int, str], QIcon] = {}  # (svg_data, size, color) -> QIcon
_ICON_CACHE_MAX = 64  # bound icon cache to avoid unbounded pixmap memory


def _make_icon(svg_data: str, size: int, color: str) -> QIcon:
    """Create a QIcon from inline SVG data with a given color (cached, max 64 entries)."""
    key = (svg_data, size, color)
    cached = _icon_cache.get(key)
    if cached is not None:
        return cached

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

    # Evict oldest entry if cache is full (simple FIFO — icons are small & stable)
    if len(_icon_cache) >= _ICON_CACHE_MAX:
        _icon_cache.pop(next(iter(_icon_cache)))
    _icon_cache[key] = icon
    return icon


# Maps model key prefixes/substrings to their provider SVG icon
_MODEL_PROVIDER_SVG: list[tuple[str, str]] = []


def _get_provider_svg_for_model(model_key: str) -> str | None:
    """Return the provider SVG string for a given model key, or None."""
    # Lazy-build the list on first call so SVG constants are already resolved
    global _MODEL_PROVIDER_SVG
    if not _MODEL_PROVIDER_SVG:
        _MODEL_PROVIDER_SVG = [
            ("gemini", SVG_GOOGLEGEMINI),
            ("qwen", SVG_QWEN),
            # OpenAI / Whisper models
            ("openai", SVG_OPENAI),
            ("v3-turbo", SVG_OPENAI),
            ("v3", SVG_OPENAI),
            ("gpt", SVG_OPENAI),
        ]
    key_lower = model_key.lower()
    for prefix, svg in _MODEL_PROVIDER_SVG:
        if prefix in key_lower:
            return svg
    return None


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
        self._format_cache: dict[str, str] = {}  # format_id -> transformed text (LRU, max 30)
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

        # Loader spin timer
        self._loader_angle = 0
        self._loader_timer = QTimer(self)
        self._loader_timer.setInterval(30)  # ~33 fps
        self._loader_timer.timeout.connect(self._spin_loader)

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

        # Title (clickable — goes back to main page)
        title = QPushButton("dicto")
        title.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {TEXT}; letter-spacing: -0.5px;"
            "border: none; background: transparent; padding: 0;"
        )
        title.setCursor(Qt.CursorShape.PointingHandCursor)
        title.clicked.connect(self._close_panel)
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

        # Pin (always on top) button
        self.always_on_top_button = QPushButton()
        self.always_on_top_button.setCheckable(True)
        self.always_on_top_button.setFixedSize(28, 28)
        self.always_on_top_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.always_on_top_button.setIconSize(QSize(16, 16))
        self.always_on_top_button.setStyleSheet(HEADER_BUTTON)
        self.always_on_top_button.setToolTip(t("always_on_top"))
        self.always_on_top_button.toggled.connect(self._on_always_on_top_toggle)
        self._update_always_on_top_icon(False)
        layout.addWidget(self.always_on_top_button)

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
        self.tabs_bar.setFixedHeight(42)
        self.tabs_bar.setStyleSheet("QWidget { border: none; }")

        layout = QHBoxLayout(self.tabs_bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(2)

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
        # Bounded LRU cache: evict oldest entry when limit is reached
        if format_id not in self._format_cache and len(self._format_cache) >= 30:
            self._format_cache.pop(next(iter(self._format_cache)))
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
        if self.is_recording:
            self.recording_label.setText(f"{t('listening')}{dots}")
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

    def _add_combo(self, layout, items: dict, callback, with_provider_icons: bool = False) -> QComboBox:
        """Create a combo box with items, connect its signal, add to layout, and return it.

        If ``with_provider_icons`` is True, a small provider logo is shown next to
        each item using the model key to detect the provider automatically.
        """
        combo = QComboBox()
        combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        setattr(combo, "wheelEvent", lambda e: e.ignore())
        for value, label in items.items():
            if with_provider_icons:
                provider_svg = _get_provider_svg_for_model(value)
                if provider_svg:
                    # Simple Icons SVGs don't use currentColor — inject fill directly
                    colored_svg = provider_svg.replace("<svg ", f'<svg fill="{TEXT}" ', 1)
                    icon = _make_icon(colored_svg, 14, TEXT)
                    combo.addItem(icon, label, value)
                    continue
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

        # Behavior
        self._add_section(layout, "behavior")
        self.auto_paste_checkbox = self._add_checkbox(
            layout, "auto_paste_after_transcribe", self._on_auto_paste_changed
        )
        self.auto_enter_checkbox = self._add_checkbox(
            layout, "press_enter_after_paste", self._on_auto_enter_changed
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

        # Live preview of the console logs that will be sent with the report
        self.report_log_view = QTextEdit()
        self.report_log_view.setReadOnly(True)
        self.report_log_view.setStyleSheet(LOG_VIEW)
        self.report_log_view.setFrameShape(QTextEdit.Shape.NoFrame)
        self.report_log_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.report_log_view.setFixedHeight(160)
        self.report_log_view.verticalScrollBar().setSingleStep(15)
        layout.addWidget(self.report_log_view)
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

        # Updates
        self._create_updates_section(layout)

        layout.addStretch()
        self.content_stack.addWidget(page)

    def _create_updates_section(self, layout):
        """Build the "Updates" settings section: current version + update button."""
        from src.version import get_version

        self._add_section(layout, "updates")

        self.current_version_label = QLabel(
            t("current_version", version=get_version())
        )
        self.current_version_label.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 12px;"
        )
        layout.addWidget(self.current_version_label)
        layout.addSpacing(8)

        self.check_updates_button = QPushButton(t("check_for_updates"))
        self.check_updates_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_updates_button.setFixedHeight(32)
        self.check_updates_button.setStyleSheet(FLAT_BUTTON)
        self.check_updates_button.clicked.connect(self._on_check_updates)
        layout.addWidget(self.check_updates_button)

        # Action button shown after a check finds an update (install or open page).
        self.update_action_button = QPushButton("")
        self.update_action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_action_button.setFixedHeight(32)
        self.update_action_button.setStyleSheet(ACCENT_BUTTON)
        self.update_action_button.clicked.connect(self._on_update_action)
        self.update_action_button.hide()
        layout.addSpacing(6)
        layout.addWidget(self.update_action_button)

        self.update_status_label = QLabel("")
        self.update_status_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        self.update_status_label.hide()
        layout.addWidget(self.update_status_label)

        # Holds the latest UpdateInfo between check and install.
        self._pending_update = None

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
            with_provider_icons=True,
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
            with_provider_icons=True,
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
        self.record_button.setFixedSize(90, 36)
        self.record_button.setIconSize(QSize(16, 16))
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

        self.include_system_audio_checkbox = QPushButton(t("system_audio_short"))
        self.include_system_audio_checkbox.setCheckable(True)
        self.include_system_audio_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.include_system_audio_checkbox.setFixedHeight(32)
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

    def _spin_loader(self):
        """Rotate the loader icon on the record button by 12° per tick (~400ms/rev)."""
        from PySide6.QtSvg import QSvgRenderer

        self._loader_angle = (self._loader_angle + 12) % 360
        size = 16
        scale = 2
        app = QApplication.instance()
        if app and isinstance(app, QApplication):
            screen = app.primaryScreen()
            if screen:
                scale = max(2, int(screen.devicePixelRatio()))

        colored = SVG_LOADER.replace("currentColor", "#18181b")
        renderer = QSvgRenderer(colored.encode())
        px = QPixmap(QSize(size * scale, size * scale))
        px.fill(QColor(0, 0, 0, 0))
        # Draw rotated
        painter = QPainter(px)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.translate(size * scale / 2, size * scale / 2)
        painter.rotate(self._loader_angle)
        painter.translate(-size * scale / 2, -size * scale / 2)
        renderer.render(painter)
        painter.end()
        px.setDevicePixelRatio(scale)
        icon = QIcon(px)
        self.record_button.setIcon(icon)

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
        self._refresh_report_log_view()
        self.settings_button.setIcon(_make_icon(SVG_SETTINGS, 16, TEXT))
        self.settings_button.setStyleSheet(HEADER_BUTTON_ACTIVE)
        self.footer.hide()
        self.footer_sep.hide()
        self.tabs_bar.hide()

    def _open_models(self):
        self._models_open = True
        self._prev_page = self.content_stack.currentIndex()
        self.content_stack.setCurrentIndex(4)  # models page
        self.models_button.setIcon(_make_icon(SVG_MODELS, 16, TEXT))
        self.models_button.setStyleSheet(HEADER_BUTTON_ACTIVE)
        self.footer.hide()
        self.footer_sep.hide()
        self.tabs_bar.hide()

    def _refresh_report_log_view(self):
        """Show the current console log buffer (what gets sent with the report)."""
        from src.utils.logger import get_log_buffer

        logs = "\n".join(get_log_buffer())
        self.report_log_view.setPlainText(logs)
        # Scroll to the latest log line
        sb = self.report_log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _send_report(self):
        import httpx
        from src.utils.logger import get_log_buffer

        self.send_report_button.setEnabled(False)
        self.report_status_label.hide()
        logs = "\n".join(get_log_buffer())
        self.report_log_view.setPlainText(logs)

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

    # ----- Updates -----------------------------------------------------------

    def _set_update_status(self, text: str, color: str = TEXT_DIM):
        self.update_status_label.setText(text)
        self.update_status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.update_status_label.show()

    @Slot()
    def _on_check_updates(self):
        """Check GitHub for a newer release in a background thread."""
        self.check_updates_button.setEnabled(False)
        self.update_action_button.hide()
        self._pending_update = None
        self._set_update_status(t("checking_updates"))

        self._update_check_thread = _UpdateCheckThread(self)
        self._update_check_thread.finished_ok.connect(self._on_update_check_done)
        self._update_check_thread.failed.connect(self._on_update_check_failed)
        self._update_check_thread.start()

    @Slot(object)
    def _on_update_check_done(self, info):
        self.check_updates_button.setEnabled(True)
        if not info.available:
            self._set_update_status(t("up_to_date"), "#4ade80")
            return

        self._pending_update = info
        self._set_update_status(
            t("update_available", version=info.latest_version), "#4ade80"
        )

        from src.services.updater import can_self_install

        if can_self_install() and info.deb_url:
            self.update_action_button.setText(t("download_install_update"))
        else:
            self.update_action_button.setText(t("open_release_page"))
        self.update_action_button.show()

    @Slot(str)
    def _on_update_check_failed(self, _msg: str):
        self.check_updates_button.setEnabled(True)
        self._set_update_status(t("update_check_failed"), RED)

    @Slot()
    def _on_update_action(self):
        """Either install the .deb in place or open the release page."""
        info = self._pending_update
        if info is None:
            return

        from src.services.updater import can_self_install

        if not (can_self_install() and info.deb_url):
            QDesktopServices.openUrl(QUrl(info.release_url))
            return

        # In-place download + install via pkexec, on a background thread.
        self.update_action_button.setEnabled(False)
        self.check_updates_button.setEnabled(False)
        self._set_update_status(t("downloading_update"))

        self._update_install_thread = _UpdateInstallThread(info, self)
        self._update_install_thread.progress.connect(self._set_update_status)
        self._update_install_thread.installed.connect(self._on_update_installed)
        self._update_install_thread.failed.connect(self._on_update_install_failed)
        self._update_install_thread.start()

    @Slot()
    def _on_update_installed(self):
        self._set_update_status(t("update_installed"), "#4ade80")
        self.update_action_button.setText(t("restart_now"))
        self.update_action_button.setEnabled(True)
        # Repurpose the action button to restart.
        try:
            self.update_action_button.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass
        self.update_action_button.clicked.connect(self._on_restart_after_update)

    @Slot()
    def _on_restart_after_update(self):
        from src.services.updater import restart_app

        restart_app()

    @Slot(str)
    def _on_update_install_failed(self, _msg: str):
        self.check_updates_button.setEnabled(True)
        self.update_action_button.setEnabled(True)
        self._set_update_status(t("update_failed"), RED)

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
        self.always_on_top_button.blockSignals(True)
        self.always_on_top_button.setChecked(self.settings.always_on_top)
        self._update_always_on_top_icon(self.settings.always_on_top)
        self.always_on_top_button.blockSignals(False)
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

        if self.settings.transcription_api_key:
            self.api_key_input.setText(self.settings.transcription_api_key)

        # UI Language
        ui_lang_index = self.ui_language_combo.findData(self.settings.ui_language)
        if ui_lang_index >= 0:
            self.ui_language_combo.setCurrentIndex(ui_lang_index)

    # ── Mouse dragging (frameless window) ───────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Prefer the compositor-driven move: required on Wayland (a client
            # cannot move its own window via global coordinates there) and also
            # the native path on X11/Windows. Fall back to manual move() if no
            # window handle is available yet or startSystemMove() is unsupported.
            handle = self.windowHandle()
            if handle is not None and handle.startSystemMove():
                self._drag_pos = None
                event.accept()
                return
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        # Only used as a fallback; with startSystemMove() the compositor drives
        # the drag and _drag_pos stays None.
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
        # Keep footer toggle in sync
        self.always_on_top_button.blockSignals(True)
        self.always_on_top_button.setChecked(checked)
        self._update_always_on_top_icon(checked)
        self.always_on_top_button.blockSignals(False)

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
        self.include_system_audio_checkbox.setText(t("system_audio_short"))
        if checked:
            self.include_system_audio_checkbox.setStyleSheet(HEADER_BUTTON)
        else:
            self.include_system_audio_checkbox.setStyleSheet(
                HEADER_BUTTON + f"QPushButton {{ color: {TEXT_DIM}; text-decoration: line-through; }}"
            )

    def _update_always_on_top_icon(self, checked: bool):
        color = TEXT if checked else TEXT_DIM
        self.always_on_top_button.setIcon(_make_icon(SVG_PIN, 16, color))

    def _on_always_on_top_toggle(self, checked: bool):
        self._update_always_on_top_icon(checked)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()
        self._save_setting("always_on_top", checked)
        # Keep settings checkbox in sync
        self.always_on_top_checkbox.blockSignals(True)
        self.always_on_top_checkbox.setChecked(checked)
        self.always_on_top_checkbox.blockSignals(False)

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
        self.record_button.setIcon(QIcon())
        self.copy_button.setText(t("copy"))
        self.cancel_button.setText(t("cancel"))

        # Settings page checkboxes
        self.auto_paste_checkbox.setText(t("auto_paste_after_transcribe"))
        self.auto_enter_checkbox.setText(t("press_enter_after_paste"))
        self.always_on_top_checkbox.setText(t("always_on_top"))
        self.persistent_overlay_checkbox.setText(t("persistent_overlay"))
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

        # Updates section
        from src.version import get_version

        self.current_version_label.setText(
            t("current_version", version=get_version())
        )
        self.check_updates_button.setText(t("check_for_updates"))

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

    @Slot(list, str)
    def _on_recording_hotkey_changed(self, modifiers: list[str], key: str):
        if self.settings:
            self.settings.hotkey_modifiers = modifiers
            self.settings.hotkey_key = key
            self.settings.save()
        self.recording_hotkey_changed.emit(modifiers, key)

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
        self.include_system_audio_checkbox.setEnabled(False)

        # If settings are open, don't switch the view — just remember the target page
        if self._settings_open or self._models_open:
            self._prev_page = 1  # recording page
        else:
            self.content_stack.setCurrentIndex(1)  # recording page
        self.recording_label.setText(t("listening"))
        self.recording_label.setStyleSheet(RECORDING_LABEL)
        self.record_button.setText("")
        self.record_button.setIcon(_make_icon(SVG_STOP, 16, "white"))
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
        if sys.platform != "darwin":
            self.include_system_audio_checkbox.setEnabled(True)

        # If settings are open, don't switch the view — just remember the target page
        if self._settings_open or self._models_open:
            self._prev_page = 2 if self.last_transcription else 0
        else:
            if self.last_transcription:
                self.content_stack.setCurrentIndex(2)  # done page
            else:
                self.content_stack.setCurrentIndex(0)  # idle page

        self.record_button.setText(t("record"))
        self.record_button.setIcon(QIcon())
        self.record_button.setStyleSheet(RECORD_BUTTON_IDLE)
        self.processing_label.hide()
        self.cancel_button.hide()
        self.status_label.setText("")

        # Stop timers
        self._elapsed_timer.stop()
        self._dot_pulse_timer.stop()
        self._dots_timer.stop()
        self._loader_timer.stop()
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
        self.record_button.setText("")
        self.record_button.setIcon(_make_icon(SVG_LOADER, 16, "#18181b"))
        self.record_button.setStyleSheet(RECORD_BUTTON_PROCESSING)
        self.copy_button.hide()
        self.cancel_button.show()

        # Start loader spin animation
        self._loader_angle = 0
        self._loader_timer.start()

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
        self.record_button.setIcon(QIcon())
        self.record_button.setStyleSheet(RECORD_BUTTON_IDLE)
        self.cancel_button.hide()
        self.copy_button.setText(t("copy"))
        self.copy_button.setStyleSheet(FOOTER_TEXT_BUTTON)
        self.copy_button.show()

        # Stop timers
        self._elapsed_timer.stop()
        self._dot_pulse_timer.stop()
        self._dots_timer.stop()
        self._loader_timer.stop()
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
        # Stop animation timers to avoid unnecessary CPU/memory activity while hidden
        for attr in ("_elapsed_timer", "_dot_pulse_timer", "_dots_timer"):
            timer = getattr(self, attr, None)
            if timer is not None:
                timer.stop()
        # Stop waveforms
        for attr in ("waveform", "test_audio_waveform"):
            w = getattr(self, attr, None)
            if w is not None:
                w.stop()
        # Clear in-session caches to free memory while the window is hidden
        self._format_cache.clear()
        event.ignore()
        self.hide()
        logger.info("Main window hidden to tray")


class _UpdateCheckThread(QThread):
    """Runs the GitHub release check off the UI thread."""

    finished_ok = Signal(object)  # emits UpdateInfo
    failed = Signal(str)

    def run(self):
        from src.services.updater import check_for_update, UpdateError

        try:
            info = check_for_update()
            self.finished_ok.emit(info)
        except UpdateError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class _UpdateInstallThread(QThread):
    """Downloads the .deb and installs it via pkexec, off the UI thread."""

    progress = Signal(str)  # status text key already resolved
    installed = Signal()
    failed = Signal(str)

    def __init__(self, info, parent=None):
        super().__init__(parent)
        self._info = info

    def run(self):
        from src.services.updater import download_deb, install_deb, UpdateError

        try:
            deb_path = download_deb(self._info.deb_url, self._info.deb_name)
            self.progress.emit(t("installing_update"))
            install_deb(deb_path)
            self.installed.emit()
        except UpdateError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
