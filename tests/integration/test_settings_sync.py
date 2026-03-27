"""Integration tests for settings <-> controller synchronization."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from src.config.settings import Settings
from src.controller import Controller


@pytest.fixture
def settings(tmp_path):
    s = Settings(config_path=str(tmp_path / "config.yaml"))
    s.transcription_api_key = "sk-dicto-test"
    return s


@pytest.fixture
def controller(settings, qtbot):
    with patch("src.controller.AudioRecorder") as MockRecorder, \
         patch("src.controller.Transcriber"), \
         patch("src.controller.HotkeyListener") as MockHotkey, \
         patch("src.controller.KeyboardService"):

        recorder = MockRecorder.return_value
        recorder.is_recording = False

        # Each call to HotkeyListener() returns a new MagicMock
        MockHotkey.side_effect = lambda **kwargs: MagicMock(**kwargs)

        ctrl = Controller(settings)
        yield ctrl, MockHotkey
        ctrl._pool.shutdown(wait=False, cancel_futures=True)


class TestHotkeyUpdate:

    def test_update_recording_hotkey_recreates_listener(self, controller, qtbot):
        ctrl, MockHotkey = controller
        ctrl.start()

        initial_listener = ctrl.hotkey_listener
        ctrl.update_recording_hotkey(["alt"], "f1")

        initial_listener.stop.assert_called()
        assert ctrl.hotkey_listener is not initial_listener

    def test_update_edit_hotkey_recreates_listener(self, controller, qtbot):
        ctrl, MockHotkey = controller
        ctrl.start()

        initial_listener = ctrl.edit_hotkey_listener
        ctrl.update_edit_hotkey(["ctrl", "shift"], "e")

        initial_listener.stop.assert_called()
        assert ctrl.edit_hotkey_listener is not initial_listener
