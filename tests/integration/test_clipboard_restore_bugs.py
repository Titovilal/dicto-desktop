"""Regression tests for the clipboard-restore failure modes.

Each test here reproduces a way the restore feature could destroy the user's
transcription. They exercise the *real* timing path (QTimer + the real
``ClipboardManager.restore`` guard), because every one of these bugs lives in
the gap between "we copied the text" and "we put the old content back".
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src import i18n
from src.config.settings import Settings
from src.controller import AppState, Controller
from src.services.clipboard import ClipboardManager


@pytest.fixture
def english():
    """Pin the UI language: other tests mutate the global i18n state."""
    previous = i18n.get_language()
    i18n.set_language("en")
    yield
    i18n.set_language(previous)


@pytest.fixture
def settings(tmp_path):
    s = Settings(config_path=str(tmp_path / "config.yaml"))
    s.transcription_api_key = "sk-dicto-test"
    s.auto_paste = True
    s.auto_enter = False
    s.restore_clipboard = True
    return s


class MemoryClipboard:
    """In-memory clipboard backend driving the real ClipboardManager.

    Only ``read``/``write`` are faked; ``copy``/``paste``/``restore`` are the
    production implementations, so the CAS guard in ``restore`` is genuinely
    under test instead of being reimplemented by the fake.
    """

    def __init__(self, initial: str = ""):
        self.content = initial

    def read(self) -> str:
        return self.content

    def write(self, text: str):
        self.content = text


@pytest.fixture
def make_controller(settings, qtbot):
    created = []

    def _make(initial_clipboard: str = "", **setting_overrides):
        for key, value in setting_overrides.items():
            setattr(settings, key, value)

        backend = MemoryClipboard(initial_clipboard)
        with (
            patch("src.controller.AudioRecorder") as MockRecorder,
            patch("src.controller.Transcriber"),
            patch("src.controller.HotkeyListener"),
            patch("src.controller.KeyboardService"),
        ):
            recorder = MockRecorder.return_value
            recorder.is_recording = False
            ctrl = Controller(settings)
            created.append(ctrl)
        # Run the clipboard work inline so tests stay deterministic.
        ctrl._run_clipboard_io = lambda fn: fn()
        return ctrl, backend

    with patch("src.services.clipboard._ClipboardBackend", MemoryClipboard):
        yield _make

    for ctrl in created:
        ctrl._pool.shutdown(wait=False, cancel_futures=True)


def _with_backend(backend):
    """Point the real ClipboardManager at this test's in-memory backend."""
    return patch("src.services.clipboard._ClipboardBackend", backend)


def _wait_for_restore(ctrl, qtbot):
    qtbot.wait(ctrl.CLIPBOARD_RESTORE_DELAY_MS + 300)


class TestPasteRaises:
    """CRITICAL 1 — pynput raising must not silently swallow the transcription.

    On X11/Windows ``KeyboardService.paste()`` re-raises pynput errors. If the
    controller only logs that, the restore fires 1.2s later and the
    transcription is gone with no trace and no warning.
    """

    def test_transcription_survives_a_raising_paste(self, make_controller, qtbot):
        ctrl, backend = make_controller("previous")
        ctrl.keyboard.paste.side_effect = RuntimeError("no display")

        with _with_backend(backend):
            ctrl._on_transcribe_finished("dictated text")
            _wait_for_restore(ctrl, qtbot)

        assert backend.content == "dictated text"

    def test_user_is_warned_when_paste_raises(self, make_controller, qtbot, english):
        ctrl, backend = make_controller("previous")
        ctrl.keyboard.paste.side_effect = RuntimeError("no display")
        warnings = []
        ctrl.warning_occurred.connect(warnings.append)

        with _with_backend(backend):
            ctrl._on_transcribe_finished("dictated text")
            qtbot.wait(300)

        assert len(warnings) == 1
        assert "Ctrl+V" in warnings[0]

    def test_raising_paste_does_not_flip_to_error_state(self, make_controller, qtbot):
        """The text made it to the clipboard: partial success, not failure."""
        ctrl, backend = make_controller("previous")
        ctrl.keyboard.paste.side_effect = RuntimeError("no display")

        with _with_backend(backend):
            ctrl._on_transcribe_finished("dictated text")
            qtbot.wait(300)

        assert ctrl.current_state == AppState.SUCCESS


class TestOverlappingTranscriptions:
    """CRITICAL 2 — a stale restore timer must never touch a newer text."""

    def test_stale_timer_does_not_clobber_the_new_transcription(
        self, make_controller, qtbot
    ):
        ctrl, backend = make_controller("previous")

        with _with_backend(backend):
            ctrl._on_transcribe_finished("first text")
            qtbot.wait(300)
            ctrl._on_transcribe_finished("second text")
            # Past the *first* transcription's restore deadline, but still
            # inside the second's.
            qtbot.wait(ctrl.CLIPBOARD_RESTORE_DELAY_MS - 200)
            assert backend.content == "second text"
            _wait_for_restore(ctrl, qtbot)

        # Only the second transcription's restore may act, and it must put back
        # the user's real clipboard — not the first transcription, which was all
        # that was actually on the clipboard when the second one started.
        assert backend.content == "previous"

    def test_only_one_restore_timer_is_ever_pending(self, make_controller, qtbot):
        ctrl, backend = make_controller("previous")

        with _with_backend(backend):
            ctrl._on_transcribe_finished("first text")
            qtbot.wait(50)
            ctrl._on_transcribe_finished("second text")
            restores = []
            with patch.object(
                ClipboardManager,
                "restore",
                side_effect=lambda p, c: restores.append((p, c)),
            ):
                _wait_for_restore(ctrl, qtbot)

        assert restores == [("previous", "second text")]

    def test_users_clipboard_survives_a_chain_of_dictations(
        self, make_controller, qtbot
    ):
        """Three back-to-back dictations must still give the original back.

        Each new transcription reads the clipboard to snapshot it, but at that
        moment the clipboard holds the *previous transcription*. Snapshotting
        that naively would lose the user's data forever.
        """
        ctrl, backend = make_controller("precious")

        with _with_backend(backend):
            for text in ("one", "two", "three"):
                ctrl._on_transcribe_finished(text)
                qtbot.wait(200)
            _wait_for_restore(ctrl, qtbot)

        assert backend.content == "precious"

    def test_failed_paste_protection_is_per_transcription(self, make_controller, qtbot):
        """HIGH 3 — T1's failure must not be undone by T2 resetting the flag.

        T1's paste fails, so T1's text must stay on the clipboard. T2 starts
        before T1's restore fires; if the failure flag lives on ``self`` the
        reset makes T1's restore run and wipe the text.
        """
        ctrl, backend = make_controller("previous")
        ctrl.keyboard.paste.return_value = False

        restores = []
        with _with_backend(backend):
            ctrl._on_transcribe_finished("first text")
            qtbot.wait(300)
            # T2 succeeds at pasting, and resets any shared failure state.
            ctrl.keyboard.paste.return_value = True
            ctrl._on_transcribe_finished("second text")
            with patch.object(
                ClipboardManager,
                "restore",
                side_effect=lambda p, c: restores.append((p, c)),
            ):
                _wait_for_restore(ctrl, qtbot)

        # T1's restore must never run; only T2's may.
        assert restores == [("previous", "second text")]


class TestWarningSeverity:
    """HIGH 4 — the notice is a warning, not an error, and must not truncate."""

    def test_uses_warning_signal_not_error_signal(self, make_controller, qtbot):
        ctrl, backend = make_controller("previous")
        ctrl.keyboard.paste.return_value = False
        errors, warnings = [], []
        ctrl.error_occurred.connect(errors.append)
        ctrl.warning_occurred.connect(warnings.append)

        with _with_backend(backend):
            ctrl._on_transcribe_finished("dictated text")
            qtbot.wait(300)

        assert errors == []
        assert len(warnings) == 1

    def test_message_is_actionable(self, make_controller, qtbot, english):
        ctrl, backend = make_controller("previous")
        ctrl.keyboard.paste.return_value = False
        warnings = []
        ctrl.warning_occurred.connect(warnings.append)

        with _with_backend(backend):
            ctrl._on_transcribe_finished("dictated text")
            qtbot.wait(300)

        message = warnings[0]
        # Reassure, then the action, then the fix.
        assert "Ctrl+V" in message
        assert "ydotoold" in message
        assert "INSTALL_LINUX.md" in message


class TestRestoreEdgeCases:
    def test_previous_equal_to_copied_text_is_a_no_op(self, make_controller, qtbot):
        """Dictating exactly what was already copied must leave it intact."""
        ctrl, backend = make_controller("same text")

        with _with_backend(backend):
            ctrl._on_transcribe_finished("same text")
            _wait_for_restore(ctrl, qtbot)

        assert backend.content == "same text"

    def test_restore_still_runs_after_entering_error_state(
        self, make_controller, qtbot
    ):
        """An unrelated later error must not strand the user's clipboard."""
        ctrl, backend = make_controller("previous")

        with _with_backend(backend):
            ctrl._on_transcribe_finished("dictated text")
            qtbot.wait(300)
            ctrl._handle_error("something else broke")
            _wait_for_restore(ctrl, qtbot)

        assert ctrl.current_state == AppState.ERROR
        assert backend.content == "previous"

    def test_auto_enter_fires_before_the_restore(self, make_controller, qtbot):
        """auto_enter runs at +150ms, well inside the 1.2s restore window."""
        ctrl, backend = make_controller("previous", auto_enter=True)
        seen = []
        ctrl.keyboard.enter.side_effect = lambda: seen.append(backend.content)

        with _with_backend(backend):
            ctrl._on_transcribe_finished("dictated text")
            _wait_for_restore(ctrl, qtbot)

        # Enter was pressed while our text was still on the clipboard.
        assert seen == ["dictated text"]
        assert backend.content == "previous"
