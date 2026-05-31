"""
Main window for Dicto application.
Redesigned to match the dicto web component aesthetic.

The window is large enough that its responsibilities are split across mixins:
- `BuildMixin` (`main_window_build.py`) — widget construction
- `StateMixin` (`main_window_state.py`) — idle/recording/processing state machine,
  animation timers, format tabs/presets, copy/cancel
- `SettingsMixin` (`main_window_settings.py`) — settings I/O, audio test, i18n,
  panel navigation, frameless-window dragging, close-to-tray
- `UpdatesMixin` (`main_window_updates.py`) — self-update flow and error reporting

`MainWindow` itself only holds the public signals, class-level data, and the
constructor that wires the timers together. All mixin methods share `self`, so
the public API (`set_recording_state`, `update_transcription`, …) is unchanged.
"""

from __future__ import annotations

import logging

from PySide6.QtWidgets import QMainWindow, QLabel
from PySide6.QtCore import Signal, QTimer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.controller import Controller

from src.ui.main_window_build import BuildMixin
from src.ui.main_window_state import StateMixin
from src.ui.main_window_settings import SettingsMixin
from src.ui.main_window_updates import UpdatesMixin

logger = logging.getLogger(__name__)


class MainWindow(BuildMixin, StateMixin, SettingsMixin, UpdatesMixin, QMainWindow):
    controller: "Controller | None"
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
            instructions[f"preset_{p['name']}"] = p["instructions"]
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
