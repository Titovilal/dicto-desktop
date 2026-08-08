"""Integration tests for restoring the user's clipboard after auto-paste.

The app hijacks the clipboard to deliver the transcription. When auto-paste is
on, whatever the user had copied before (a URL, a password, a code) must come
back once the paste has consumed our text.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.config.settings import Settings
from src.controller import Controller
from src.services.clipboard import ClipboardManager


@pytest.fixture
def settings(tmp_path):
    s = Settings(config_path=str(tmp_path / "config.yaml"))
    s.transcription_api_key = "sk-dicto-test"
    s.auto_paste = True
    s.auto_enter = False
    s.restore_clipboard = True
    return s


class FakeClipboard:
    """In-memory clipboard driving the *real* ClipboardManager.

    Only the platform backend (read/write) is faked. copy/paste/restore delegate
    to production code, so the compare-and-swap guard inside
    ``ClipboardManager.restore`` is genuinely under test. Reimplementing that
    guard here would leave these tests green even if the real one broke.
    """

    def __init__(self, initial: str = ""):
        self.content = initial

    # ── Platform backend surface (what ClipboardManager calls) ──

    def read(self) -> str:
        return self.content

    def write(self, text: str):
        self.content = text

    # ── ClipboardManager surface (what the controller calls) ────

    def _delegate(self, name, *args):
        with patch("src.services.clipboard._ClipboardBackend", self):
            return getattr(ClipboardManager, name)(*args)

    def copy(self, text: str) -> bool:
        return self._delegate("copy", text)

    def paste(self) -> str:
        return self._delegate("paste")

    def restore(self, previous: str, expected_current: str) -> bool:
        return self._delegate("restore", previous, expected_current)


@pytest.fixture
def make_controller(settings, qtbot):
    """Build a controller with mocked I/O and a fake in-memory clipboard."""
    created = []

    def _make(initial_clipboard: str = "", **setting_overrides):
        for key, value in setting_overrides.items():
            setattr(settings, key, value)

        clipboard = FakeClipboard(initial_clipboard)
        with (
            patch("src.controller.AudioRecorder") as MockRecorder,
            patch("src.controller.Transcriber"),
            patch("src.controller.HotkeyListener"),
            patch("src.controller.KeyboardService"),
            patch("src.controller.ClipboardManager", clipboard),
        ):
            recorder = MockRecorder.return_value
            recorder.is_recording = False
            ctrl = Controller(settings)
            created.append(ctrl)
            # The restore is offloaded to the worker pool in production; run it
            # inline so these tests stay deterministic without sleeping on it.
            ctrl._run_clipboard_io = lambda fn: fn()
            return ctrl, clipboard

    yield _make

    for ctrl in created:
        ctrl._pool.shutdown(wait=False, cancel_futures=True)


def _wait_for_restore(ctrl, qtbot):
    """Wait past the scheduled restore delay."""
    qtbot.wait(ctrl.CLIPBOARD_RESTORE_DELAY_MS + 300)


class TestRestoreAfterAutoPaste:
    def test_previous_content_is_restored(self, make_controller, qtbot):
        ctrl, clipboard = make_controller("https://important.example/url")

        with patch("src.controller.ClipboardManager", clipboard):
            ctrl._on_transcribe_finished("dictated text")
            # The transcription must be on the clipboard for the paste to work.
            assert clipboard.content == "dictated text"
            _wait_for_restore(ctrl, qtbot)

        assert clipboard.content == "https://important.example/url"

    def test_paste_happens_before_restore(self, make_controller, qtbot):
        """The auto-paste must read our text, not the restored content."""
        ctrl, clipboard = make_controller("previous")
        seen_by_paste = []

        def _record_paste():
            seen_by_paste.append(clipboard.content)
            return True  # signal a successful paste to the controller

        ctrl.keyboard.paste.side_effect = _record_paste

        with patch("src.controller.ClipboardManager", clipboard):
            ctrl._on_transcribe_finished("dictated text")
            _wait_for_restore(ctrl, qtbot)

        assert seen_by_paste == ["dictated text"]
        assert clipboard.content == "previous"

    def test_empty_previous_is_not_restored(self, make_controller, qtbot):
        """Nothing to put back, so the transcription stays on the clipboard."""
        ctrl, clipboard = make_controller("")

        with patch("src.controller.ClipboardManager", clipboard):
            ctrl._on_transcribe_finished("dictated text")
            _wait_for_restore(ctrl, qtbot)

        assert clipboard.content == "dictated text"

    def test_manual_copy_is_not_overwritten(self, make_controller, qtbot):
        """If the user copies something new meanwhile, we must not clobber it."""
        ctrl, clipboard = make_controller("previous")

        with patch("src.controller.ClipboardManager", clipboard):
            ctrl._on_transcribe_finished("dictated text")
            # User copies something else while the restore is still pending.
            clipboard.content = "user copied this"
            _wait_for_restore(ctrl, qtbot)

        assert clipboard.content == "user copied this"

    def test_no_restore_without_auto_paste(self, make_controller, qtbot):
        """Without auto-paste the transcription IS the deliverable: keep it."""
        ctrl, clipboard = make_controller("previous", auto_paste=False)

        with patch("src.controller.ClipboardManager", clipboard):
            ctrl._on_transcribe_finished("dictated text")
            _wait_for_restore(ctrl, qtbot)

        assert clipboard.content == "dictated text"

    def test_no_restore_when_the_paste_never_happened(self, make_controller, qtbot):
        """If auto-paste could not run, the text must stay on the clipboard."""
        ctrl, clipboard = make_controller("previous")
        ctrl.keyboard.paste.return_value = False

        with patch("src.controller.ClipboardManager", clipboard):
            ctrl._on_transcribe_finished("dictated text")
            _wait_for_restore(ctrl, qtbot)

        assert clipboard.content == "dictated text"

    def test_no_restore_when_setting_disabled(self, make_controller, qtbot):
        ctrl, clipboard = make_controller("previous", restore_clipboard=False)

        with patch("src.controller.ClipboardManager", clipboard):
            ctrl._on_transcribe_finished("dictated text")
            _wait_for_restore(ctrl, qtbot)

        assert clipboard.content == "dictated text"
