"""Unit tests for Controller state machine and cancel logic."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.config.settings import Settings
from src.controller import Controller, AppState


@pytest.fixture
def mock_settings(tmp_path):
    """Settings with a test API key so Transcriber initializes."""
    s = Settings(config_path=str(tmp_path / "config.yaml"))
    s.transcription_api_key = "sk-dicto-test"
    return s


@pytest.fixture
def controller(mock_settings, qtbot):
    """Controller with mocked external services."""
    with patch("src.controller.AudioRecorder") as MockRecorder, \
         patch("src.controller.Transcriber"), \
         patch("src.controller.HotkeyListener"), \
         patch("src.controller.KeyboardService"):

        recorder = MockRecorder.return_value
        recorder.is_recording = False
        recorder.start_recording.return_value = True
        recorder.stop_recording.return_value = "/tmp/test.wav"
        recorder.get_recording_duration.return_value = 1.5

        ctrl = Controller(mock_settings)
        yield ctrl
        ctrl._pool.shutdown(wait=False, cancel_futures=True)


class TestStateTransitions:

    def test_initial_state_after_start(self, controller, qtbot):
        controller.start()
        assert controller.current_state == AppState.IDLE

    def test_hotkey_press_starts_recording(self, controller, qtbot):
        controller.start()
        with qtbot.waitSignal(controller.state_changed, timeout=1000):
            controller._on_hotkey_press()
        assert controller.current_state == AppState.RECORDING

    def test_hotkey_press_ignored_during_processing(self, controller, qtbot):
        controller.current_state = AppState.PROCESSING
        controller._on_hotkey_press()
        assert controller.current_state == AppState.PROCESSING

    def test_hotkey_release_triggers_processing(self, controller, qtbot):
        controller.start()
        controller._on_hotkey_press()
        with qtbot.waitSignal(controller.state_changed, timeout=1000):
            controller._on_hotkey_release()
        assert controller.current_state == AppState.PROCESSING

    def test_hotkey_release_ignored_when_idle(self, controller, qtbot):
        controller.start()
        controller._on_hotkey_release()
        assert controller.current_state == AppState.IDLE

    def test_can_record_from_success_state(self, controller, qtbot):
        controller.current_state = AppState.SUCCESS
        with qtbot.waitSignal(controller.state_changed, timeout=1000):
            controller._on_hotkey_press()
        assert controller.current_state == AppState.RECORDING


class TestCancel:

    def test_cancel_during_recording(self, controller, qtbot):
        controller.start()
        controller._on_hotkey_press()
        assert controller.current_state == AppState.RECORDING

        controller.recorder.is_recording = True
        with qtbot.waitSignal(controller.cancel_completed, timeout=1000):
            controller.cancel()

        assert controller.current_state == AppState.IDLE
        controller.recorder.stop_recording.assert_called()
        controller.recorder.cleanup_temp_file.assert_called()

    def test_cancel_during_processing_sets_flag(self, controller, qtbot):
        controller.current_state = AppState.PROCESSING
        with qtbot.waitSignal(controller.cancel_completed, timeout=1000):
            controller.cancel()

        assert controller._cancelled is True
        assert controller.current_state == AppState.IDLE

    def test_cancel_ignored_when_idle(self, controller, qtbot):
        controller.start()
        controller.cancel()
        assert controller.current_state == AppState.IDLE

    def test_cancelled_flag_discards_transcription(self, controller, qtbot):
        controller._cancelled = True
        controller._on_transcribe_finished("some text")
        # Should NOT emit transcription_completed
        assert controller.current_state != AppState.SUCCESS


class TestTranscriptionResult:

    @patch("src.controller.ClipboardManager")
    def test_successful_transcription_copies_to_clipboard(self, MockClipboard, controller, qtbot):
        MockClipboard.copy.return_value = True
        with qtbot.waitSignal(controller.transcription_completed, timeout=1000):
            controller._on_transcribe_finished("hello world")
        MockClipboard.copy.assert_called_once_with("hello world")
        assert controller.current_state == AppState.SUCCESS

    @patch("src.controller.ClipboardManager")
    def test_clipboard_failure_emits_error(self, MockClipboard, controller, qtbot):
        MockClipboard.copy.return_value = False
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._on_transcribe_finished("hello world")
        assert controller.current_state == AppState.ERROR

    def test_transcription_error_goes_to_error_state(self, controller, qtbot):
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._on_transcribe_error("API failed")
        assert controller.current_state == AppState.ERROR


class TestManualControls:

    def test_start_recording_manual(self, controller, qtbot):
        controller.start()
        with qtbot.waitSignal(controller.recording_started, timeout=1000):
            controller.start_recording_manual()
        assert controller.current_state == AppState.RECORDING

    def test_stop_recording_manual(self, controller, qtbot):
        controller.start()
        controller._on_hotkey_press()
        controller.stop_recording_manual()
        assert controller.current_state == AppState.PROCESSING

    def test_stop_manual_during_processing_cancels(self, controller, qtbot):
        controller.current_state = AppState.PROCESSING
        with qtbot.waitSignal(controller.cancel_completed, timeout=1000):
            controller.stop_recording_manual()
        assert controller.current_state == AppState.IDLE

    def test_return_to_idle(self, controller, qtbot):
        controller.current_state = AppState.SUCCESS
        with qtbot.waitSignal(controller.state_changed, timeout=1000):
            controller.return_to_idle()
        assert controller.current_state == AppState.IDLE


class TestNoRecorder:

    def test_start_recording_without_recorder(self, controller, qtbot):
        controller.recorder = None
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._start_recording()
        assert controller.current_state == AppState.ERROR

    def test_stop_recording_without_recorder(self, controller, qtbot):
        controller.recorder = None
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._stop_recording_and_process()
        assert controller.current_state == AppState.ERROR


class TestNoTranscriber:

    def test_transcribe_without_transcriber(self, controller, qtbot):
        controller.transcriber = None
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._transcribe_audio("/tmp/test.wav")
        assert controller.current_state == AppState.ERROR


class TestEditFlow:

    def test_edit_hotkey_press_starts_recording(self, controller, qtbot):
        controller.start()
        with qtbot.waitSignal(controller.edit_started, timeout=1000):
            controller._on_edit_hotkey_press()
        assert controller.current_state == AppState.RECORDING

    def test_edit_hotkey_press_ignored_during_processing(self, controller, qtbot):
        controller.current_state = AppState.PROCESSING
        controller._on_edit_hotkey_press()
        assert controller.current_state == AppState.PROCESSING

    def test_edit_hotkey_press_ignored_during_recording(self, controller, qtbot):
        controller.current_state = AppState.RECORDING
        controller._on_edit_hotkey_press()
        assert controller.current_state == AppState.RECORDING

    def test_edit_hotkey_release_emits_signal_when_recording(self, controller, qtbot):
        controller.current_state = AppState.RECORDING
        with qtbot.waitSignal(controller._edit_hotkey_released, timeout=1000):
            controller._on_edit_hotkey_release()

    def test_edit_hotkey_release_ignored_when_idle(self, controller, qtbot):
        controller.start()
        # Should not emit _edit_hotkey_released
        controller._on_edit_hotkey_release()
        assert controller.current_state == AppState.IDLE

    @patch("src.controller.ClipboardManager")
    def test_edit_finished_copies_to_clipboard(self, MockClipboard, controller, qtbot):
        MockClipboard.copy.return_value = True
        with qtbot.waitSignal(controller.edit_completed, timeout=1000):
            controller._on_edit_finished("edited text")
        MockClipboard.copy.assert_called_once_with("edited text")
        assert controller.current_state == AppState.SUCCESS

    @patch("src.controller.ClipboardManager")
    def test_edit_finished_clipboard_failure(self, MockClipboard, controller, qtbot):
        MockClipboard.copy.return_value = False
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._on_edit_finished("edited text")
        assert controller.current_state == AppState.ERROR

    def test_edit_finished_discarded_when_cancelled(self, controller, qtbot):
        controller._cancelled = True
        controller._on_edit_finished("edited text")
        assert controller.current_state != AppState.SUCCESS
        assert controller._cancelled is False

    def test_edit_error_goes_to_error_state(self, controller, qtbot):
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._on_edit_error("Edit API failed")
        assert controller.current_state == AppState.ERROR

    def test_start_edit_without_transcriber(self, controller, qtbot):
        controller.transcriber = None
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._start_edit_flow()
        assert controller.current_state == AppState.ERROR

    def test_start_edit_without_recorder(self, controller, qtbot):
        controller.recorder = None
        with qtbot.waitSignal(controller.error_occurred, timeout=1000):
            controller._start_edit_flow()
        assert controller.current_state == AppState.ERROR

    def test_edit_can_start_from_success_state(self, controller, qtbot):
        controller.current_state = AppState.SUCCESS
        with qtbot.waitSignal(controller.edit_started, timeout=1000):
            controller._on_edit_hotkey_press()
        assert controller.current_state == AppState.RECORDING


class TestTransform:

    def test_transform_without_transcriber(self, controller, qtbot):
        controller.transcriber = None
        with qtbot.waitSignal(controller.transform_failed, timeout=1000):
            controller.request_transform("formal", "hello", "make formal")

    def test_transform_success(self, controller, qtbot):
        controller.transcriber.transform.return_value = "Hello, good day."
        controller.transcriber.last_transcription_id = 42
        with qtbot.waitSignal(controller.transform_completed, timeout=1000) as blocker:
            controller.request_transform("formal", "hello", "make formal")
        assert blocker.args == ["formal", "Hello, good day."]
        controller.transcriber.transform.assert_called_once_with("hello", "make formal", 42)

    def test_transform_error(self, controller, qtbot):
        controller.transcriber.transform.side_effect = Exception("API error")
        controller.transcriber.last_transcription_id = None
        with qtbot.waitSignal(controller.transform_failed, timeout=1000) as blocker:
            controller.request_transform("formal", "hello", "make formal")
        assert blocker.args[0] == "formal"
        assert "API error" in blocker.args[1]
