"""UI construction for the main window.

`BuildMixin` holds all the widget-creation methods (header, format tabs, the
stacked pages, footer, and small layout helpers). It is mixed into
`MainWindow`; every method operates on the shared `self` instance, so the
attributes it creates (e.g. ``self.content_stack``, ``self.record_button``)
are used by the other mixins.
"""

from __future__ import annotations

import os
import sys

from PySide6.QtCore import Qt, QSize, QUrl, QTimer
from PySide6.QtGui import QIcon, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QCheckBox,
    QComboBox,
    QListView,
    QTextEdit,
    QLineEdit,
    QScrollArea,
    QGraphicsDropShadowEffect,
)

from src.utils.icons import get_icon_path
from src.i18n import t
from src.i18n.translations import UI_LANGUAGES
from src.ui.waveform import WaveformWidget
from src.ui.widgets.hotkey_button import HotkeyButton
from src.ui.widgets.icon_utils import (
    make_icon as _make_icon,
    get_provider_svg_for_model as _get_provider_svg_for_model,
)
from src.ui.main_window_styles import (
    GLOBAL_STYLE,
    DOT_IDLE,
    HEADER_BUTTON,
    HEADER_BUTTON_CLOSE,
    TAB_BUTTON_ACTIVE,
    CONTENT_TEXT,
    LOG_VIEW,
    IDLE_TEXT,
    IDLE_TEXT_BOLD,
    RECORDING_LABEL,
    PROCESSING_LABEL,
    TIMER_RECORDING,
    RECORD_BUTTON_IDLE,
    FOOTER_TEXT_BUTTON,
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
)


class BuildMixin:
    """Widget-construction methods for MainWindow."""

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

    def _make_combo(self) -> QComboBox:
        """Create a QComboBox whose drop-down is a styleable QListView.

        Forcing an explicit QListView view makes the popup a Qt widget that
        inherits the dark stylesheet (`QComboBox QListView`), instead of the
        platform-native popup which renders unstyled (white background, on
        Wayland in particular).
        """
        combo = QComboBox()
        view = QListView()
        # Style the view (and its popup container) directly. Relying only on the
        # descendant selector `QComboBox QListView` leaves the popup frame's
        # viewport unstyled — a white band above/below the items, visible on
        # Wayland. Styling the view itself covers its viewport too.
        view.setStyleSheet(
            f"QListView {{ background-color: {MUTED}; border: 1px solid {BORDER}; "
            f"outline: none; }}"
        )
        combo.setView(view)
        # The popup lives in a QFrame container parented to the view; give it the
        # same dark background so no white frame shows around the list.
        container = view.parentWidget()
        if container is not None:
            container.setStyleSheet(f"background-color: {MUTED};")
        combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        setattr(combo, "wheelEvent", lambda e: e.ignore())
        return combo

    def _add_combo(
        self, layout, items: dict, callback, with_provider_icons: bool = False
    ) -> QComboBox:
        """Create a combo box with items, connect its signal, add to layout, and return it.

        If ``with_provider_icons`` is True, a small provider logo is shown next to
        each item using the model key to detect the provider automatically.
        """
        combo = self._make_combo()
        for value, label in items.items():
            if with_provider_icons:
                provider_svg = _get_provider_svg_for_model(value)
                if provider_svg:
                    # Simple Icons SVGs don't use currentColor — inject fill directly
                    colored_svg = provider_svg.replace(
                        "<svg ", f'<svg fill="{TEXT}" ', 1
                    )
                    icon = _make_icon(colored_svg, 14, TEXT)
                    combo.addItem(icon, label, value)
                    continue
            combo.addItem(label, value)
        combo.currentIndexChanged.connect(callback)
        layout.addWidget(combo)
        return combo

    def _repopulate_combo(
        self, combo: QComboBox, items: dict, with_provider_icons: bool = False
    ) -> None:
        """Replace the items of an existing combo, preserving the current selection.

        The combo's ``currentIndexChanged`` signal is blocked during the rebuild
        so repopulating from the API doesn't fire the change handler (which would
        spuriously persist a setting). If the previously-selected value still
        exists it is reselected.
        """
        previous = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for value, label in items.items():
            if with_provider_icons:
                provider_svg = _get_provider_svg_for_model(value)
                if provider_svg:
                    colored_svg = provider_svg.replace(
                        "<svg ", f'<svg fill="{TEXT}" ', 1
                    )
                    icon = _make_icon(colored_svg, 14, TEXT)
                    combo.addItem(icon, label, value)
                    continue
            combo.addItem(label, value)
        if previous is not None:
            idx = combo.findData(previous)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.blockSignals(False)

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
        self.input_device_combo = self._make_combo()
        # Prevent long device names from expanding the combo (and the whole page) beyond the window width.
        self.input_device_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.input_device_combo.setMinimumContentsLength(10)
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

        report_buttons_row = QHBoxLayout()
        report_buttons_row.setSpacing(8)

        self.copy_logs_button = QPushButton(t("copy_logs"))
        self.copy_logs_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_logs_button.setFixedHeight(32)
        self.copy_logs_button.setStyleSheet(FLAT_BUTTON)
        self.copy_logs_button.clicked.connect(self._copy_logs)
        report_buttons_row.addWidget(self.copy_logs_button)

        self.send_report_button = QPushButton(t("send_report"))
        self.send_report_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_report_button.setFixedHeight(32)
        self.send_report_button.setStyleSheet(FLAT_BUTTON)
        self.send_report_button.clicked.connect(self._send_report)
        report_buttons_row.addWidget(self.send_report_button)

        layout.addLayout(report_buttons_row)
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

        self.current_version_label = QLabel(t("current_version", version=get_version()))
        self.current_version_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
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
        # Built-in fallback lists, used until/unless the API's GET /api/v1/models
        # response replaces them via set_models().
        self._default_transcription_models = {
            "v3-turbo": "Whisper V3 Turbo",
            "v3": f"Whisper V3 ({t('recommended')})",
            "gemini-3-flash-preview": "Gemini 3 Flash",
            "gemini-3.1-flash-lite-preview": "Gemini 3.1 Flash Lite",
        }
        self._default_transformation_models = {
            "qwen/qwen3-32b": "Qwen 3 32B",
            "openai/gpt-oss-120b": f"GPT OSS 120B ({t('recommended')})",
            "openai/gpt-oss-20b": "GPT OSS 20B",
            "gemini-3-flash-preview": "Gemini 3 Flash",
            "gemini-3.1-flash-lite-preview": "Gemini 3.1 Flash Lite",
        }
        self.model_combo = self._add_combo(
            layout,
            self._default_transcription_models,
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
            self._default_transformation_models,
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
            self.include_system_audio_checkbox.setToolTip(t("system_audio_unsupported"))
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
