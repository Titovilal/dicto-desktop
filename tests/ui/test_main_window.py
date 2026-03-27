"""UI tests for MainWindow state-driven behavior."""

from __future__ import annotations


import pytest

from src.config.settings import Settings
from src.i18n import t
from src.ui.main_window import MainWindow
from src.ui.main_window_styles import (
    DOT_IDLE,
    DOT_RECORDING,
    DOT_PROCESSING,
    DOT_SUCCESS,
    DOT_EDITING,
    RECORD_BUTTON_IDLE,
    RECORD_BUTTON_RECORDING,
    RECORD_BUTTON_PROCESSING,
    RECORD_BUTTON_EDITING,
)


@pytest.fixture
def settings(tmp_path):
    s = Settings(config_path=str(tmp_path / "config.yaml"))
    s.transcription_api_key = "sk-test"
    return s


@pytest.fixture
def win(settings, qtbot):
    w = MainWindow(settings=settings)
    qtbot.addWidget(w)
    return w


class TestRecordButtonLabel:
    def test_idle_shows_record(self, win):
        win.set_idle_state()
        assert win.record_button.text() == t("record")
        assert win.record_button.styleSheet() == RECORD_BUTTON_IDLE

    def test_recording_shows_stop(self, win):
        win.set_recording_state()
        assert win.record_button.text() == t("stop")
        assert win.record_button.styleSheet() == RECORD_BUTTON_RECORDING

    def test_processing_shows_processing(self, win):
        win.set_processing_state()
        assert win.record_button.text() == t("processing_ellipsis")
        assert win.record_button.styleSheet() == RECORD_BUTTON_PROCESSING

    def test_editing_shows_stop(self, win):
        win.set_editing_state()
        assert win.record_button.text() == t("stop")
        assert win.record_button.styleSheet() == RECORD_BUTTON_EDITING


class TestStatusDot:
    def test_idle_dot(self, win):
        win.set_idle_state()
        assert win.status_dot.styleSheet() == DOT_IDLE

    def test_recording_dot(self, win):
        win.set_recording_state()
        assert win.status_dot.styleSheet() == DOT_RECORDING

    def test_processing_dot(self, win):
        win.set_processing_state()
        assert win.status_dot.styleSheet() == DOT_PROCESSING

    def test_transcription_dot(self, win):
        win.update_transcription("hello")
        assert win.status_dot.styleSheet() == DOT_SUCCESS

    def test_editing_dot(self, win):
        win.set_editing_state()
        assert win.status_dot.styleSheet() == DOT_EDITING


class TestTabsEnableDisable:
    def test_tabs_disabled_during_recording(self, win):
        win.set_recording_state()
        for btn in win.format_tabs:
            fid = btn.property("format_id")
            if fid != "raw":
                assert not btn.isEnabled()

    def test_tabs_enabled_after_transcription(self, win):
        win.update_transcription("hello world")
        for btn in win.format_tabs:
            assert btn.isEnabled()

    def test_tabs_disabled_during_processing(self, win):
        win.set_processing_state()
        for btn in win.format_tabs:
            fid = btn.property("format_id")
            if fid != "raw":
                assert not btn.isEnabled()


class TestContentStack:
    def test_idle_shows_idle_page(self, win):
        win.set_idle_state()
        assert win.content_stack.currentIndex() == 0

    def test_recording_shows_recording_page(self, win):
        win.set_recording_state()
        assert win.content_stack.currentIndex() == 1

    def test_processing_shows_done_page(self, win):
        win.set_processing_state()
        assert win.content_stack.currentIndex() == 2

    def test_transcription_shows_done_page(self, win):
        win.update_transcription("text")
        assert win.content_stack.currentIndex() == 2

    def test_idle_after_transcription_stays_on_done(self, win):
        win.update_transcription("text")
        win.set_idle_state()
        # Should show done page since there is a transcription
        assert win.content_stack.currentIndex() == 2


class TestCancelButton:
    def test_cancel_shown_during_recording(self, win):
        win.set_recording_state()
        # cancel_button.show() was called but parent not shown, check !isHidden
        assert not win.cancel_button.isHidden()

    def test_cancel_shown_during_processing(self, win):
        win.set_processing_state()
        assert not win.cancel_button.isHidden()

    def test_cancel_hidden_when_idle(self, win):
        win.set_idle_state()
        assert win.cancel_button.isHidden()


class TestCopyButton:
    def test_copy_hidden_during_recording(self, win):
        win.set_recording_state()
        assert win.copy_button.isHidden()

    def test_copy_shown_after_transcription(self, win):
        win.update_transcription("hello")
        assert not win.copy_button.isHidden()

    def test_copy_hidden_during_processing(self, win):
        win.set_processing_state()
        assert win.copy_button.isHidden()


class TestSettingsPanel:
    def test_toggle_settings_opens_panel(self, win):
        win._toggle_settings()
        assert win._settings_open
        assert win.content_stack.currentIndex() == 3

    def test_toggle_settings_closes_panel(self, win):
        win._toggle_settings()  # open
        win._toggle_settings()  # close
        assert not win._settings_open
        assert win.content_stack.currentIndex() != 3

    def test_settings_protects_during_recording(self, win):
        """Opening settings during recording should not switch page. Closing restores recording page."""
        win.set_recording_state()
        assert win.content_stack.currentIndex() == 1
        win._toggle_settings()
        assert win.content_stack.currentIndex() == 3
        win._toggle_settings()
        # Should return to recording page
        assert win.content_stack.currentIndex() == 1

    def test_recording_during_settings_remembers_page(self, win):
        """Starting recording while settings open should NOT switch page."""
        win._toggle_settings()
        assert win.content_stack.currentIndex() == 3
        win.set_recording_state()
        # Should stay on settings page
        assert win.content_stack.currentIndex() == 3
        # But prev_page should be set to recording
        assert win._prev_page == 1


class TestTranscriptionDisplay:
    def test_transcription_text_updated(self, win):
        win.update_transcription("hello world")
        assert win.transcription_text.toPlainText() == "hello world"
        assert win.last_transcription == "hello world"

    def test_processing_label_hidden_after_transcription(self, win):
        win.set_processing_state()
        assert not win.processing_label.isHidden()
        win.update_transcription("done")
        assert win.processing_label.isHidden()


class TestTimerLabel:
    def test_timer_shown_during_recording(self, win):
        win.set_recording_state()
        assert not win.timer_label.isHidden()
        assert win.timer_label.text() == "00:00"

    def test_timer_hidden_when_idle(self, win):
        win.set_idle_state()
        assert win.timer_label.isHidden()

    def test_timer_shown_during_processing(self, win):
        win.set_processing_state()
        assert not win.timer_label.isHidden()
