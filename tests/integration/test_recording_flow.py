"""Integration tests for the complete recording → transcription → clipboard flow."""
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
    """Controller with mocked I/O boundaries but real internal logic."""
    with patch("src.controller.AudioRecorder") as MockRecorder, \
         patch("src.controller.Transcriber") as MockTranscriber, \
         patch("src.controller.HotkeyListener"), \
         patch("src.controller.KeyboardService"), \
         patch("src.controller.ClipboardManager") as MockClipboard:

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


class TestHappyPath:

    def test_full_recording_flow(self, controller, qtbot):
        ctrl, recorder, transcriber, clipboard = controller

        # Collect emitted signals
        states = []
        ctrl.state_changed.connect(states.append)

        ctrl.start()

        # 1. Press hotkey -> recording
        ctrl._on_hotkey_press()
        assert ctrl.current_state == AppState.RECORDING
        recorder.start_recording.assert_called_once()

        # 2. Release hotkey -> processing
        ctrl._on_hotkey_release()
        assert ctrl.current_state == AppState.PROCESSING
        recorder.stop_recording.assert_called_once()

        # 3. Simulate transcription result arriving on main thread
        with qtbot.waitSignal(ctrl.transcription_completed, timeout=1000):
            ctrl._on_transcribe_finished("transcribed text")

        assert ctrl.current_state == AppState.SUCCESS
        clipboard.copy.assert_called_with("transcribed text")

        # Verify state transition order (idle is initial, may not emit if already idle)
        state_values = [s.value for s in states]
        assert "recording" in state_values
        assert "processing" in state_values
        assert "success" in state_values


class TestCancelFlow:

    def test_cancel_during_recording_returns_to_idle(self, controller, qtbot):
        ctrl, recorder, _, _ = controller
        ctrl.start()
        ctrl._on_hotkey_press()
        assert ctrl.current_state == AppState.RECORDING

        recorder.is_recording = True
        with qtbot.waitSignal(ctrl.cancel_completed, timeout=1000):
            ctrl.cancel()

        assert ctrl.current_state == AppState.IDLE
        recorder.cleanup_temp_file.assert_called()

    def test_cancel_during_processing_discards_result(self, controller, qtbot):
        ctrl, recorder, _, clipboard = controller
        ctrl.start()
        ctrl._on_hotkey_press()
        ctrl._on_hotkey_release()
        assert ctrl.current_state == AppState.PROCESSING

        ctrl.cancel()
        assert ctrl._cancelled is True

        # Result arrives but should be discarded
        ctrl._on_transcribe_finished("should be discarded")
        clipboard.copy.assert_not_called()
        assert ctrl.current_state != AppState.SUCCESS


class TestErrorFlow:

    def test_transcription_error_goes_to_error(self, controller, qtbot):
        ctrl, _, _, _ = controller
        ctrl.start()
        ctrl._on_hotkey_press()
        ctrl._on_hotkey_release()

        with qtbot.waitSignal(ctrl.error_occurred, timeout=1000):
            ctrl._on_transcribe_error("API rate limit")

        assert ctrl.current_state == AppState.ERROR

    def test_recorder_start_failure(self, controller, qtbot):
        ctrl, recorder, _, _ = controller
        recorder.start_recording.return_value = False
        ctrl.start()

        with qtbot.waitSignal(ctrl.error_occurred, timeout=1000):
            ctrl._on_hotkey_press()

        assert ctrl.current_state == AppState.ERROR

    def test_no_audio_recorded(self, controller, qtbot):
        ctrl, recorder, _, _ = controller
        recorder.stop_recording.return_value = None
        ctrl.start()
        ctrl._on_hotkey_press()

        with qtbot.waitSignal(ctrl.error_occurred, timeout=1000):
            ctrl._on_hotkey_release()

        assert ctrl.current_state == AppState.ERROR
