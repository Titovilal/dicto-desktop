"""
BuildMixin: all UI construction for MainWindow.

A flat mixin (not a QMainWindow subclass) that assumes ``self`` is the window.
"""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QCheckBox,
    QComboBox,
    QTextEdit,
    QLineEdit,
    QScrollArea,
)
from PySide6.QtWidgets import QListView, QFrame, QStyledItemDelegate
from PySide6.QtCore import Qt, QSize, QUrl, QTimer
from PySide6.QtGui import QIcon, QColor, QDesktopServices, QPalette
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from src.utils.icons import get_icon_path
from src.i18n import t
from src.i18n.translations import UI_LANGUAGES
from src.ui.waveform import WaveformWidget
from src.ui.main_window_common import (
    _make_icon,
    _get_provider_svg_for_model,
    HotkeyButton,
)
from src.ui.main_window_styles import (
    GLOBAL_STYLE,
    DOT_IDLE,
    HEADER_BUTTON,
    HEADER_BUTTON_CLOSE,
    CONTENT_TEXT,
    IDLE_TEXT,
    IDLE_TEXT_BOLD,
    RECORDING_LABEL,
    PROCESSING_LABEL,
    TIMER_RECORDING,
    RECORD_BUTTON_IDLE,
    FOOTER_TEXT_BUTTON,
    SECTION_LABEL,
    FLAT_BUTTON,
    LOG_VIEW,
    ACCENT_BUTTON,
    SEPARATOR,
    MUTED,
    BORDER,
    TEXT,
    TEXT_DIM,
    RED,
    SECONDARY,
)
from src.ui.icons import (
    SVG_SETTINGS,
    SVG_CLOSE,
    SVG_EXTERNAL,
    SVG_AUDIO_LINES,
    SVG_MODELS,
    SVG_PIN,
)


class _RowHeightDelegate(QStyledItemDelegate):
    """Force a fixed, comfortable row height so popup items never clip."""

    def __init__(self, height: int, parent=None):
        super().__init__(parent)
        self._height = height

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(self._height)
        return size


def _style_combo_popup(combo: QComboBox, bg: str = MUTED) -> None:
    """Force a dark popup for a QComboBox.

    Stylesheets alone don't reliably color the dropdown's viewport on every
    platform style — the popup item delegate paints the background from the
    view's palette, which otherwise defaults to a white system base, leaving
    the light text unreadable. Installing an explicit QListView with a dark
    palette fixes it everywhere.
    """
    view = QListView()
    pal = view.palette()
    base = QColor(bg)
    pal.setColor(QPalette.ColorRole.Base, base)
    pal.setColor(QPalette.ColorRole.Window, base)
    pal.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(SECONDARY))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(TEXT))
    view.setPalette(pal)
    view.setFrameShape(QFrame.Shape.NoFrame)
    # Fix a uniform, comfortable row height so neither the provider icons nor
    # the text get clipped. The stylesheet min-height alone isn't honored as the
    # actual row height by every style, so set it on the view directly.
    view.setUniformItemSizes(True)
    view.setItemDelegate(_RowHeightDelegate(32, view))
    # The popup container (the QFrame wrapping the view) plus the view itself
    # must both be painted dark, or a white system frame shows around the list.
    view.setStyleSheet(
        f"QListView {{ background-color: {bg}; border: 1px solid {BORDER}; outline: none; }}"
        f" QListView::item {{ background-color: {bg}; color: {TEXT}; padding: 0 8px; }}"
        f" QListView::item:selected {{ background-color: {SECONDARY}; color: {TEXT}; }}"
    )
    combo.setView(view)
    # Paint the popup container window (the QFrame that wraps the view) dark too,
    # otherwise its default white base shows as a border around the list.
    container = combo.view().parentWidget()
    if container is not None:
        container.setPalette(pal)
        container.setStyleSheet(f"background-color: {bg}; border: 1px solid {BORDER};")


class BuildMixin:
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

        # Content stack
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)

        self._create_idle_page()
        self._create_recording_page()
        self._create_done_page()
        self._create_settings_page()
        self._create_models_page()

        self._create_tabs_bar(main_layout)
        self._create_footer(main_layout)

        # Start on idle
        self.content_stack.setCurrentIndex(0)

    # ── Header ──────────────────────────────────────────────

    def _create_header(self, parent_layout):
        header = QWidget()
        header.setFixedHeight(44)
        # Let the header act as a drag handle: a click on its empty area is
        # consumed by the child QWidget and never bubbles to the window's
        # mousePressEvent, so forward it to the window manager's move loop.
        header.mousePressEvent = self._start_window_drag
        header.mouseMoveEvent = self.mouseMoveEvent
        header.mouseReleaseEvent = self.mouseReleaseEvent

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

        # Always-on-top (pin) button
        self.always_on_top_button = QPushButton()
        self.always_on_top_button.setFixedSize(28, 28)
        self.always_on_top_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.always_on_top_button.setCheckable(True)
        self.always_on_top_button.setIcon(_make_icon(SVG_PIN, 16, TEXT_DIM))
        self.always_on_top_button.setIconSize(QSize(16, 16))
        self.always_on_top_button.setStyleSheet(HEADER_BUTTON)
        self.always_on_top_button.setToolTip(t("always_on_top"))
        self.always_on_top_button.clicked.connect(self._on_always_on_top_toggle)
        setattr(
            self.always_on_top_button, "_icon_normal", _make_icon(SVG_PIN, 16, TEXT_DIM)
        )
        setattr(self.always_on_top_button, "_icon_hover", _make_icon(SVG_PIN, 16, TEXT))
        self.always_on_top_button.installEventFilter(self)
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
        # Separator line before action bar
        self._tabs_sep = QWidget()
        self._tabs_sep.setFixedHeight(1)
        self._tabs_sep.setStyleSheet(f"background-color: {BORDER};")
        parent_layout.addWidget(self._tabs_sep)

        # ── Action bar: [Select ▼] [custom prompt input ————] [Apply] ──
        self.tabs_bar = QWidget()
        self.tabs_bar.setFixedHeight(42)
        self.tabs_bar.setStyleSheet("QWidget { border: none; }")

        layout = QHBoxLayout(self.tabs_bar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # Format select (QComboBox replaces tab buttons)
        self.format_combo = QComboBox()
        self.format_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        setattr(self.format_combo, "wheelEvent", lambda e: e.ignore())
        self.format_combo.setFixedHeight(30)
        self.format_combo.setMinimumWidth(110)
        self.format_combo.setMaximumWidth(160)
        self.format_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 4px;
                color: {TEXT};
                font-size: 12px;
                padding: 0 8px;
            }}
            QComboBox:disabled {{ color: {TEXT_DIM}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{ image: none; width: 0; }}
            QComboBox QAbstractItemView {{
                background-color: {SECONDARY};
                border: 1px solid {BORDER};
                color: {TEXT};
                selection-background-color: {BORDER};
                selection-color: {TEXT};
                outline: none;
                font-size: 12px;
            }}
            QComboBox QAbstractItemView::item {{
                background-color: {SECONDARY};
                color: {TEXT};
                padding: 4px 8px;
                min-height: 22px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {BORDER};
                color: {TEXT};
            }}
        """)
        _style_combo_popup(self.format_combo, SECONDARY)
        # Populate initial "Original" item
        self.format_combo.addItem(t("tab_original"), "raw")
        # Loading indicator as a disabled item (removed by set_presets)
        self.format_combo.addItem(t("presets_loading"), "__loading__")
        self.format_combo.model().item(1).setEnabled(False)
        self._presets_loading_label = None  # no separate label widget now
        self.format_combo.currentIndexChanged.connect(self._on_format_combo_changed)
        layout.addWidget(self.format_combo)

        # Custom prompt input — always visible to the right
        self._custom_prompt_input = QLineEdit()
        self._custom_prompt_input.setPlaceholderText(t("custom_prompt_placeholder"))
        self._custom_prompt_input.setFixedHeight(30)
        self._custom_prompt_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 4px;
                color: {TEXT};
                font-size: 12px;
                padding: 0 8px;
                letter-spacing: 0;
            }}
            QLineEdit:focus {{ border-color: {TEXT_DIM}; }}
        """)
        self._custom_prompt_input.returnPressed.connect(self._on_custom_transform_apply)
        layout.addWidget(self._custom_prompt_input, 1)

        self._custom_apply_btn = QPushButton(t("apply"))
        self._custom_apply_btn.setFixedHeight(30)
        self._custom_apply_btn.setMinimumWidth(58)
        self._custom_apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._custom_apply_btn.setStyleSheet(FLAT_BUTTON)
        self._custom_apply_btn.clicked.connect(self._on_custom_transform_apply)
        layout.addWidget(self._custom_apply_btn)

        parent_layout.addWidget(self.tabs_bar)

        self._active_format = "raw"
        self._custom_prompt_open = False  # kept for compat, no longer toggles visibility
        # format_tabs list kept for compat methods that iterate it (now empty; combo is used)
        self.format_tabs = []

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
        layout.setContentsMargins(20, 6, 20, 16)

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
        _style_combo_popup(combo)
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

        # Recording mode: hold vs toggle
        layout.addSpacing(10)
        mode_label = QLabel(t("recording_mode"))
        mode_label.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
        self._hotkey_labels["recording_mode"] = mode_label
        layout.addWidget(mode_label)
        layout.addSpacing(4)
        self.recording_mode_combo = self._add_combo(
            layout,
            {"hold": t("recording_mode_hold"), "toggle": t("recording_mode_toggle")},
            self._on_recording_mode_changed,
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
        _style_combo_popup(self.input_device_combo)
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
        layout.setContentsMargins(8, 0, 8, 0)
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

        # Hidden status label kept only for settings feedback (api key / test audio).
        # Not added to the footer layout — no longer shown next to the team toggle.
        self.status_label = QLabel("")

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
