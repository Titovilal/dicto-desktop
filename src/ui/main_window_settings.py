"""
SettingsMixin: settings/models panels, settings load/save, event handling,
frameless-window dragging, and i18n for MainWindow.

A flat mixin (not a QMainWindow subclass) that assumes ``self`` is the window.
"""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Slot, Qt, QEvent
from PySide6.QtGui import QIcon, QMouseEvent

from src.i18n import t, set_language
from src.ui.main_window_common import _make_icon, logger
from src.ui.main_window_styles import (
    HEADER_BUTTON,
    HEADER_BUTTON_ACTIVE,
    TEXT,
    TEXT_DIM,
    RED,
)
from src.ui.icons import (
    SVG_SETTINGS,
    SVG_MODELS,
    SVG_SPEAKER,
    SVG_SPEAKER_OFF,
    SVG_PIN,
)


class SettingsMixin:
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
        # The user is now looking at the Updates section, so the badge has done
        # its job — but keep the pending update itself actionable.
        if self._pending_update is not None:
            self._show_pending_update_in_settings(self._pending_update)
        self._clear_update_badge()
        self.settings_button.setIcon(_make_icon(SVG_SETTINGS, 16, TEXT))
        self.settings_button.setStyleSheet(HEADER_BUTTON_ACTIVE)
        self.footer.hide()
        self.footer_sep.hide()
        self._tabs_sep.hide()
        self.tabs_bar.hide()

    def _open_models(self):
        self._models_open = True
        self._prev_page = self.content_stack.currentIndex()
        self.content_stack.setCurrentIndex(4)  # models page
        self.models_button.setIcon(_make_icon(SVG_MODELS, 16, TEXT))
        self.models_button.setStyleSheet(HEADER_BUTTON_ACTIVE)
        self.footer.hide()
        self.footer_sep.hide()
        self._tabs_sep.hide()
        self.tabs_bar.hide()

    def _refresh_report_log_view(self):
        """Show the current console log buffer (what gets sent with the report)."""
        from src.utils.logger import get_log_buffer

        logs = "\n".join(get_log_buffer())
        self.report_log_view.setPlainText(logs)
        # Scroll to the latest log line
        sb = self.report_log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _copy_logs(self):
        """Copy the current console log buffer to the clipboard."""
        from PySide6.QtWidgets import QApplication
        from src.utils.logger import get_log_buffer

        logs = "\n".join(get_log_buffer())
        self.report_log_view.setPlainText(logs)
        QApplication.clipboard().setText(logs)
        self.report_status_label.setText(t("logs_copied"))
        self.report_status_label.setStyleSheet("color: #4ade80; font-size: 11px;")
        self.report_status_label.show()

    def _send_report(self):
        import httpx
        from src.utils.logger import get_log_buffer

        self.send_report_button.setEnabled(False)
        self.report_status_label.hide()
        logs = "\n".join(get_log_buffer())
        self.report_log_view.setPlainText(logs)

        try:
            api_key = self.settings.transcription_api_key if self.settings else ""
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            base_url = os.environ.get("DICTO_API_URL", "https://dicto.up.railway.app")
            response = httpx.post(
                f"{base_url}/api/report",
                headers=headers,
                json={"logs": logs, "source": "desktop_app"},
                timeout=15.0,
            )
            if response.status_code in (200, 201):
                self.report_status_label.setText(t("report_sent"))
                self.report_status_label.setStyleSheet(
                    "color: #4ade80; font-size: 11px;"
                )
            else:
                self.report_status_label.setText(t("report_send_failed"))
                self.report_status_label.setStyleSheet(
                    f"color: {RED}; font-size: 11px;"
                )
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
        self._tabs_sep.show()
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

        mode_index = self.recording_mode_combo.findData(self.settings.recording_mode)
        if mode_index >= 0:
            self.recording_mode_combo.setCurrentIndex(mode_index)

        self.auto_paste_checkbox.setChecked(self.settings.auto_paste)
        self.auto_enter_checkbox.setChecked(self.settings.auto_enter)
        self.restore_clipboard_checkbox.setChecked(self.settings.restore_clipboard)

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

    def _start_window_drag(self, event: QMouseEvent):
        """Header press handler: start a window move. Prefers the compositor's
        native move loop (works on Wayland, where manual `move()` is ignored);
        falls back to the manual drag tracked in mouseMoveEvent."""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        handle = self.windowHandle()
        if handle is not None and handle.startSystemMove():
            event.accept()
            return
        self._drag_pos = (
            event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        )
        event.accept()

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

    def _save_setting(self, attr: str, value):
        """Save a setting attribute and persist to disk."""
        if self.settings:
            setattr(self.settings, attr, value)
            self.settings.save()

    def _on_auto_paste_changed(self, state: int):
        self._save_setting("auto_paste", state == Qt.CheckState.Checked.value)

    def _on_auto_enter_changed(self, state: int):
        self._save_setting("auto_enter", state == Qt.CheckState.Checked.value)

    def _on_restore_clipboard_changed(self, state: int):
        self._save_setting("restore_clipboard", state == Qt.CheckState.Checked.value)

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
                HEADER_BUTTON
                + f"QPushButton {{ color: {TEXT_DIM}; text-decoration: line-through; }}"
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
        self.record_button.setIcon(QIcon())
        self.copy_button.setText(t("copy"))
        self.cancel_button.setText(t("cancel"))

        # Settings page checkboxes
        self.auto_paste_checkbox.setText(t("auto_paste_after_transcribe"))
        self.auto_enter_checkbox.setText(t("press_enter_after_paste"))
        self.restore_clipboard_checkbox.setText(t("restore_clipboard_after_paste"))
        self.always_on_top_checkbox.setText(t("always_on_top"))
        self.persistent_overlay_checkbox.setText(t("persistent_overlay"))
        self.edit_auto_paste_checkbox.setText(t("auto_paste_after_edit"))
        self.edit_auto_enter_checkbox.setText(t("press_enter_after_paste"))
        self.save_api_key_button.setText(t("save_key"))
        if sys.platform == "darwin":
            self.include_system_audio_checkbox.setToolTip(t("system_audio_unsupported"))
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

        self._version_label.setText(t("current_version", version=get_version()))
        self.check_updates_button.setText(t("check_for_updates"))
        if self._pending_update is not None:
            self._show_pending_update_in_settings(self._pending_update)

        # Section labels
        for key, label in self._section_labels.items():
            label.setText(t(key).upper())

        # Hotkey row labels
        for key, label in self._hotkey_labels.items():
            label.setText(t(key))

        # Hotkey buttons (modifier/key names are localized too)
        self.recording_hotkey_button.retranslate()
        self.edit_hotkey_button.retranslate()

        # Recording mode combo items
        self.recording_mode_combo.blockSignals(True)
        self.recording_mode_combo.setItemText(0, t("recording_mode_hold"))
        self.recording_mode_combo.setItemText(1, t("recording_mode_toggle"))
        self.recording_mode_combo.blockSignals(False)

        # Custom prompt row
        self._custom_prompt_input.setPlaceholderText(t("custom_prompt_placeholder"))
        self._custom_apply_btn.setText(t("apply"))

        # Format combo (default item labels are translated)
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

    def _on_recording_mode_changed(self, index: int):
        mode = self.recording_mode_combo.itemData(index)
        self._save_setting("recording_mode", mode)
        self.recording_mode_changed.emit(mode)

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
