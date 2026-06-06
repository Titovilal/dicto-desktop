"""
StateMixin: format/transform handling, animations, copy/cancel actions, and
recording/processing/idle/editing state transitions for MainWindow.

A flat mixin (not a QMainWindow subclass) that assumes ``self`` is the window.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Slot, Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QPainter, QColor, QPixmap

from src.i18n import t
from src.ui.main_window_common import _make_icon, logger
from src.ui.main_window_styles import (
    DOT_IDLE,
    DOT_RECORDING,
    DOT_PROCESSING,
    DOT_SUCCESS,
    DOT_EDITING,
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
    RED,
    BLUE,
)
from src.ui.icons import (
    SVG_STOP,
    SVG_LOADER,
)


class StateMixin:
    def _update_tabs_enabled(self, enabled: bool):
        self.format_combo.setEnabled(enabled)
        # Custom input/apply enabled only when there's text
        self._custom_prompt_input.setEnabled(enabled)
        self._custom_apply_btn.setEnabled(enabled)

    def _on_format_combo_changed(self, index: int):
        fid = self.format_combo.itemData(index)
        if not fid or fid == "__loading__" or fid == self._active_format:
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

    def _on_custom_transform_apply(self):
        prompt = self._custom_prompt_input.text().strip()
        if not prompt or not self.last_transcription:
            return

        import time
        fid = f"custom_{int(time.time() * 1000)}"
        self._active_format = fid
        self._update_tabs_enabled(True)

        self._transforming_format = fid
        self.transcription_text.setText("")
        self.processing_label.setText(t("transforming"))
        self.processing_label.show()
        self.copy_button.hide()
        self.cancel_button.show()
        self._dots_timer.start(400)

        self.transform_requested.emit(fid, self.last_transcription, prompt)

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
        """Update format combo with user's favorite presets from the API."""
        self._user_presets = presets
        self._rebuild_format_tabs()

    def _rebuild_format_tabs(self):
        """Rebuild format combo: Original + user presets."""
        self.format_combo.blockSignals(True)
        self.format_combo.clear()
        self._format_cache.clear()

        # Build format list: Original + user presets
        formats: list[tuple[str, str]] = [("raw", t("tab_original"))]
        for i, p in enumerate(self._user_presets):
            preset_id = p.get("id", i)
            formats.append((f"preset_{preset_id}", p["name"]))

        for fid, label in formats:
            self.format_combo.addItem(label, fid)

        # Restore active selection
        idx = self.format_combo.findData(self._active_format)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        else:
            self._active_format = "raw"
            self.format_combo.setCurrentIndex(0)

        has_text = bool(self.last_transcription)
        self.format_combo.setEnabled(has_text)
        self.format_combo.blockSignals(False)

    def _animate_dots(self):
        self._dots_count = (self._dots_count + 1) % 4
        dots = "." * self._dots_count + " " * (3 - self._dots_count)
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

    # ── State updates ───────────────────────────────────────

    @Slot(str)
    def update_status(self, status: str):
        # Footer status label was removed; status is reflected by the dot,
        # waveform and overlay instead. Kept as a no-op for the state signal.
        pass

    @Slot()
    def set_recording_state(self):
        self.is_recording = True
        self.is_processing = False
        self._is_editing = False
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
        self._is_editing = False
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
        self.record_button.setText("")
        self.record_button.setIcon(_make_icon(SVG_STOP, 16, "#18181b"))
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
        self.record_button.setText("")
        self.record_button.setIcon(_make_icon(SVG_LOADER, 16, "#18181b"))
        self.record_button.setStyleSheet(RECORD_BUTTON_EDITING)
        self.copy_button.hide()
        self.cancel_button.show()

        # Start loader spin animation
        self._loader_angle = 0
        self._loader_timer.start()

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
        self.format_combo.blockSignals(True)
        idx = self.format_combo.findData("raw")
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        self.format_combo.blockSignals(False)
        self._update_tabs_enabled(True)
