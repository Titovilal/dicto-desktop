"""Integration tests for cancel flows — recording and processing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.config.settings import Settings
from src.controller import Controller, AppState


@pytest.fixture
def settings(tmp_path):
    s = Settings(config_path=str(tmp_path / "config.yaml"))
    s.transcription_api_key = "sk-dicto-test"
    s.auto_paste = False
    return s


@pytest.fixture
def controller(settings, qtbot):
    with (
        patch("src.controller.AudioRecorder") as MockRecorder,
        patch("src.controller.Transcriber") as MockTranscriber,
        patch("src.controller.HotkeyListener"),
        patch("src.controller.KeyboardService"),
        patch("src.controller.ClipboardManager") as MockClipboard,
    ):
        recorder = MockRecorder.return_value
        recorder.is_recording = False
        recorder.start_recording.return_value = True
        recorder.stop_recording.return_value = "/tmp/test.wav"
        recorder.get_recording_duration.return_value = 2.0

        transcriber = MockTranscriber.return_value
        MockClipboard.copy.return_value = True

        ctrl = Controller(settings)
        yield ctrl, recorder, transcriber, MockClipboard
        qtbot.wait(200)
        ctrl._pool.shutdown(wait=False, cancel_futures=True)


class TestCancelDuringRecording:
    def test_cancel_stops_recorder_and_cleans_up(self, controller, qtbot):
        ctrl, recorder, _, _ = controller
        ctrl.start()
        ctrl._on_hotkey_press()
        assert ctrl.current_state == AppState.RECORDING

        recorder.is_recording = True
        with qtbot.waitSignal(ctrl.cancel_completed, timeout=1000):
            ctrl.cancel()

        assert ctrl.current_state == AppState.IDLE
        recorder.stop_recording.assert_called()
        recorder.cleanup_temp_file.assert_called()

    def test_cancel_recording_then_record_again(self, controller, qtbot):
        """After cancelling, a new recording should work normally."""
        ctrl, recorder, _, clipboard = controller
        ctrl.start()

        # First: record then cancel
        ctrl._on_hotkey_press()
        recorder.is_recording = True
        ctrl.cancel()
        assert ctrl.current_state == AppState.IDLE

        # Second: record again
        recorder.is_recording = False
        recorder.start_recording.return_value = True
        ctrl._on_hotkey_press()
        assert ctrl.current_state == AppState.RECORDING

        ctrl._on_hotkey_release()
        assert ctrl.current_state == AppState.PROCESSING

        with qtbot.waitSignal(ctrl.transcription_completed, timeout=1000):
            ctrl._on_transcribe_finished("second try")

        assert ctrl.current_state == AppState.SUCCESS
        clipboard.copy.assert_called_with("second try")

    def test_state_transitions_on_cancel_recording(self, controller, qtbot):
        ctrl, recorder, _, _ = controller
        states = []
        ctrl.state_changed.connect(states.append)
        ctrl.start()

        ctrl._on_hotkey_press()
        recorder.is_recording = True
        ctrl.cancel()

        state_values = [s.value for s in states]
        assert "recording" in state_values
        assert state_values[-1] == "idle"


class TestCancelDuringProcessing:
    def test_cancel_processing_discards_result(self, controller, qtbot):
        ctrl, _, _, clipboard = controller
        ctrl.start()
        ctrl._on_hotkey_press()
        ctrl._on_hotkey_release()
        assert ctrl.current_state == AppState.PROCESSING

        ctrl.cancel()
        assert ctrl._cancelled is True
        assert ctrl.current_state == AppState.IDLE

        # Late result arrives — should be discarded
        ctrl._on_transcribe_finished("should be ignored")
        clipboard.copy.assert_not_called()
        assert ctrl.current_state != AppState.SUCCESS

    def test_cancel_processing_then_record_again(self, controller, qtbot):
        """After cancelling processing, next recording should work."""
        ctrl, recorder, _, clipboard = controller
        ctrl.start()

        # Record -> process -> cancel
        ctrl._on_hotkey_press()
        ctrl._on_hotkey_release()
        ctrl.cancel()

        # Deliver the discarded result so _cancelled resets
        ctrl._on_transcribe_finished("discarded")
        assert ctrl._cancelled is False

        # New recording
        ctrl._on_hotkey_press()
        assert ctrl.current_state == AppState.RECORDING
        ctrl._on_hotkey_release()

        with qtbot.waitSignal(ctrl.transcription_completed, timeout=1000):
            ctrl._on_transcribe_finished("new result")
        clipboard.copy.assert_called_with("new result")

    def test_cancel_processing_emits_signal(self, controller, qtbot):
        ctrl, _, _, _ = controller
        ctrl.start()
        ctrl._on_hotkey_press()
        ctrl._on_hotkey_release()

        with qtbot.waitSignal(ctrl.cancel_completed, timeout=1000):
            ctrl.cancel()


class TestCancelEdgeCase:
    def test_cancel_when_idle_is_noop(self, controller, qtbot):
        ctrl, recorder, _, _ = controller
        ctrl.start()
        assert ctrl.current_state == AppState.IDLE
        ctrl.cancel()
        assert ctrl.current_state == AppState.IDLE
        recorder.stop_recording.assert_not_called()

    def test_cancel_during_error_is_noop(self, controller, qtbot):
        ctrl, _, _, _ = controller
        ctrl._handle_error("some error")
        assert ctrl.current_state == AppState.ERROR
        ctrl.cancel()
        # cancel does nothing in error state
        assert ctrl.current_state == AppState.ERROR

    def test_cancel_during_success_is_noop(self, controller, qtbot):
        ctrl, _, _, clipboard = controller
        clipboard.copy.return_value = True
        ctrl._on_transcribe_finished("text")
        assert ctrl.current_state == AppState.SUCCESS
        ctrl.cancel()
        assert ctrl.current_state == AppState.SUCCESS
