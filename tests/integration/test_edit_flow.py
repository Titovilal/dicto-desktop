"""Integration tests for the edit selection flow (copy text → record voice → edit via API)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.config.settings import Settings
from src.controller import Controller, AppState


@pytest.fixture
def settings(tmp_path):
    s = Settings(config_path=str(tmp_path / "config.yaml"))
    s.transcription_api_key = "sk-dicto-test"
    s.edit_auto_paste = False
    return s


@pytest.fixture
def controller(settings, qtbot):
    """Controller with mocked I/O boundaries but real internal logic."""
    with patch("src.controller.AudioRecorder") as MockRecorder, \
         patch("src.controller.Transcriber") as MockTranscriber, \
         patch("src.controller.HotkeyListener"), \
         patch("src.controller.KeyboardService") as MockKeyboard, \
         patch("src.controller.ClipboardManager") as MockClipboard:

        recorder = MockRecorder.return_value
        recorder.is_recording = False
        recorder.start_recording.return_value = True
        recorder.stop_recording.return_value = "/tmp/test_edit.wav"
        recorder.get_recording_duration.return_value = 1.0

        transcriber = MockTranscriber.return_value
        MockClipboard.copy.return_value = True
        MockClipboard.paste.return_value = "selected text to edit"

        ctrl = Controller(settings)
        yield ctrl, recorder, transcriber, MockClipboard, MockKeyboard
        qtbot.wait(200)
        ctrl._pool.shutdown(wait=False, cancel_futures=True)


class TestEditHappyPath:

    def test_full_edit_flow(self, controller, qtbot):
        ctrl, recorder, transcriber, clipboard, keyboard = controller

        states = []
        ctrl.state_changed.connect(states.append)
        ctrl.start()

        # 1. Edit hotkey press → recording starts
        ctrl._on_edit_hotkey_press()
        assert ctrl.current_state == AppState.RECORDING
        recorder.start_recording.assert_called_once()

        # 2. Edit hotkey release → processing (via signal bounce to main thread)
        ctrl._stop_edit_recording_and_process()
        assert ctrl.current_state == AppState.PROCESSING
        recorder.stop_recording.assert_called_once()

        # 3. Simulate clipboard timer firing: reads selected text, submits edit job
        ctrl._edit_process_with_audio("/tmp/test_edit.wav", 1.0)
        clipboard.paste.assert_called_once()

        # 4. Simulate edit result arriving
        with qtbot.waitSignal(ctrl.edit_completed, timeout=1000):
            ctrl._on_edit_finished("edited result")

        assert ctrl.current_state == AppState.SUCCESS
        clipboard.copy.assert_called_with("edited result")

        state_values = [s.value for s in states]
        assert "recording" in state_values
        assert "processing" in state_values
        assert "success" in state_values


class TestEditCancelFlow:

    def test_cancel_during_edit_recording(self, controller, qtbot):
        ctrl, recorder, _, _, _ = controller
        ctrl.start()
        ctrl._on_edit_hotkey_press()
        assert ctrl.current_state == AppState.RECORDING

        recorder.is_recording = True
        with qtbot.waitSignal(ctrl.cancel_completed, timeout=1000):
            ctrl.cancel()

        assert ctrl.current_state == AppState.IDLE
        recorder.cleanup_temp_file.assert_called()

    def test_cancel_during_edit_processing_discards_result(self, controller, qtbot):
        ctrl, _, _, clipboard, _ = controller
        ctrl.start()
        ctrl._on_edit_hotkey_press()
        ctrl._stop_edit_recording_and_process()
        assert ctrl.current_state == AppState.PROCESSING

        ctrl.cancel()
        assert ctrl._cancelled is True

        # Result arrives but should be discarded
        ctrl._on_edit_finished("should be discarded")
        assert ctrl.current_state != AppState.SUCCESS


class TestEditErrorFlow:

    def test_edit_error_goes_to_error(self, controller, qtbot):
        ctrl, _, _, _, _ = controller
        ctrl.start()
        ctrl._on_edit_hotkey_press()
        ctrl._stop_edit_recording_and_process()

        with qtbot.waitSignal(ctrl.error_occurred, timeout=1000):
            ctrl._on_edit_error("Edit API failed")

        assert ctrl.current_state == AppState.ERROR

    def test_empty_clipboard_goes_to_error(self, controller, qtbot):
        ctrl, recorder, _, clipboard, _ = controller
        clipboard.paste.return_value = "   "
        ctrl.start()

        with qtbot.waitSignal(ctrl.error_occurred, timeout=1000):
            ctrl._edit_process_with_audio("/tmp/test_edit.wav", 1.0)

        assert ctrl.current_state == AppState.ERROR
        recorder.cleanup_temp_file.assert_called()

    def test_recorder_start_failure_during_edit(self, controller, qtbot):
        ctrl, recorder, _, _, _ = controller
        recorder.start_recording.return_value = False
        ctrl.start()

        with qtbot.waitSignal(ctrl.error_occurred, timeout=1000):
            ctrl._on_edit_hotkey_press()

        assert ctrl.current_state == AppState.ERROR
