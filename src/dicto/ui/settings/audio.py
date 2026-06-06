"""Audio settings panel — microphone picker plus a live mic test.

Pick an input device and see it working through a live waveform driven by
``AudioMonitor`` (no disk writes). Levels arrive on the monitor thread and hop to
the Qt thread via a queued signal before touching the widget.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dicto.audio import devices
from dicto.audio.monitor import AudioMonitor
from dicto.config.settings import Settings
from dicto.i18n import on_language_changed, t
from dicto.ui.overlay.waveform import WaveformWidget
from dicto.ui.theme.manager import ThemeManager
from dicto.ui.theme.tokens import Token

logger = logging.getLogger(__name__)


class MicTestPanel(QWidget):
    """Microphone selection + a start/stop live test with a waveform meter."""

    # Emitted (thread-safe) with each RMS level from the monitor thread.
    _level = Signal(float)

    def __init__(
        self,
        theme: ThemeManager,
        settings: Settings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._settings = settings
        self._monitor: AudioMonitor | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Device row.
        device_row = QHBoxLayout()
        self._device_label = QLabel()
        self._device_label.setProperty("muted", True)
        device_row.addWidget(self._device_label)
        self._device_combo = QComboBox()
        self._device_combo.currentIndexChanged.connect(self._on_device_changed)
        device_row.addWidget(self._device_combo, 1)
        layout.addLayout(device_row)

        # Meter + test button.
        meter_row = QHBoxLayout()
        self._waveform = WaveformWidget(
            self._theme, token=Token.ACCENT, height=24, bar_width=3, bar_gap=2, mode="live"
        )
        meter_row.addWidget(self._waveform, 1)
        self._test_btn = QPushButton()
        self._test_btn.setCheckable(True)
        self._test_btn.clicked.connect(self._on_test_clicked)
        meter_row.addWidget(self._test_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(meter_row)

        self._level.connect(self._waveform.set_level)

        self._populate_devices()
        self.retranslate()
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    # ── devices ─────────────────────────────────────────────────────────

    def _populate_devices(self) -> None:
        self._device_combo.blockSignals(True)
        self._device_combo.clear()
        found = devices.list_input_devices()
        if not found:
            self._device_combo.addItem(t("mic.no_device"), None)
            self._device_combo.setEnabled(False)
            self._test_btn.setEnabled(False)
        else:
            self._device_combo.setEnabled(True)
            self._test_btn.setEnabled(True)
            current = self._settings.audio.input_device
            select_idx = 0
            for i, dev in enumerate(found):
                self._device_combo.addItem(dev.name, dev.id)
                if dev.id == current or (current is None and dev.is_default):
                    select_idx = i
            self._device_combo.setCurrentIndex(select_idx)
        self._device_combo.blockSignals(False)

    def _on_device_changed(self, _index: int) -> None:
        device_id = self._device_combo.currentData()
        self._settings.audio.input_device = device_id
        self._settings.save()
        # Restart the test on the new device if running.
        if self._monitor is not None and self._monitor.is_running:
            self.stop_test()
            self.start_test()

    # ── test lifecycle ──────────────────────────────────────────────────

    def _on_test_clicked(self, checked: bool) -> None:
        if checked:
            self.start_test()
        else:
            self.stop_test()

    def start_test(self) -> None:
        device_id = self._device_combo.currentData()
        self._monitor = AudioMonitor(
            sample_rate=self._settings.audio.sample_rate,
            channels=1,
            input_device=device_id,
            level_callback=self._level.emit,
        )
        self._waveform.start()
        self._monitor.start()
        self._test_btn.setChecked(True)
        self.retranslate()

    def stop_test(self) -> None:
        if self._monitor is not None:
            self._monitor.stop()
            self._monitor = None
        self._waveform.clear()
        self._test_btn.setChecked(False)
        self.retranslate()

    # ── i18n ────────────────────────────────────────────────────────────

    def retranslate(self) -> None:
        self._device_label.setText(t("mic.device"))
        testing = self._monitor is not None and self._monitor.is_running
        self._test_btn.setText(t("mic.stop") if testing else t("mic.start"))

    # ── teardown ────────────────────────────────────────────────────────

    def dispose(self) -> None:
        self.stop_test()
        self._unsub_lang()

    def hideEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        # Don't keep the mic open when the panel is hidden.
        self.stop_test()
        super().hideEvent(event)
