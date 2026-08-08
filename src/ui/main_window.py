"""
Main window for Dicto application.
Redesigned to match the dicto web component aesthetic.

The window's behavior is split across four flat mixins:
- BuildMixin (main_window_build.py): UI construction
- SettingsMixin (main_window_settings.py): settings/models panels, load/save,
  event handling, frameless-window dragging, i18n
- StateMixin (main_window_state.py): formats/transform, animations, copy/cancel,
  recording/processing/idle/editing state transitions
- UpdatesMixin (main_window_updates.py): startup + manual update checks and the
  in-place install flow

Shared module-level helpers live in main_window_common.py.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QLabel
from PySide6.QtCore import Signal, QTimer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.controller import Controller

from src.ui.main_window_common import (  # noqa: F401 (re-exported for callers)
    _make_icon,
    _get_provider_svg_for_model,
    HotkeyButton,
    logger,
)
from src.ui.main_window_build import BuildMixin
from src.ui.main_window_settings import SettingsMixin
from src.ui.main_window_state import StateMixin
from src.ui.main_window_updates import UpdatesMixin


class MainWindow(BuildMixin, SettingsMixin, StateMixin, UpdatesMixin, QMainWindow):
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
    recording_mode_changed = Signal(str)  # "hold" or "toggle"
    edit_hotkey_changed = Signal(list, str)  # (modifiers, key)
    input_device_changed = Signal(object)  # int or None
    include_system_audio_changed = Signal(bool)
    update_available = Signal(str)  # latest version, from the startup check
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
        self._format_cache: dict[
            str, str
        ] = {}  # format_id -> transformed text (LRU, max 30)
        self._transforming_format: str | None = None
        self._user_presets: list[dict] = []  # [{id, name, instructions}]
        self.controller = None  # set externally after init
        self._section_labels: dict[str, QLabel] = {}  # key -> section QLabel
        self._hotkey_labels: dict[str, QLabel] = {}  # key -> hotkey row QLabel
        self._audio_monitor = None  # AudioMonitor while test is active
        self._pending_update = None  # UpdateInfo once a newer release is found
        self._update_check_thread = None
        self._update_install_thread = None
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
