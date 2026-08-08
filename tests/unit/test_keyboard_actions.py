"""Unit tests for KeyboardService, the Wayland key fallbacks and the
controller's auto-paste degradation path."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from src.config.settings import Settings
from src.controller import AppState, Controller, _Delivery
from src.services import keyboard_actions
from src.services.keyboard_actions import KeyboardService


class _CompletedProcess:
    """Minimal stand-in for subprocess.CompletedProcess."""

    def __init__(self, returncode: int = 0, stderr: bytes = b""):
        self.returncode = returncode
        self.stderr = stderr


@pytest.fixture
def wayland(monkeypatch):
    """Force the Wayland code path."""
    monkeypatch.setattr(keyboard_actions, "_is_wayland", lambda: True)


@pytest.fixture
def no_tools(monkeypatch):
    """No ydotool and no xdotool on PATH."""
    monkeypatch.setattr(keyboard_actions.shutil, "which", lambda name: None)


def _tools(monkeypatch, **available):
    """Make only the named tools resolvable on PATH."""
    monkeypatch.setattr(
        keyboard_actions.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if available.get(name) else None,
    )


class TestWaylandWithoutTools:
    def test_paste_returns_false(self, wayland, no_tools):
        assert KeyboardService().paste() is False

    def test_enter_and_copy_return_false(self, wayland, no_tools):
        service = KeyboardService()
        assert service.enter() is False
        assert service.copy() is False

    def test_logs_actionable_warning(self, wayland, no_tools, caplog):
        with caplog.at_level(logging.WARNING, logger="src.services.keyboard_actions"):
            KeyboardService().paste()
        messages = [r.getMessage() for r in caplog.records]
        assert any("ydotool" in m and "xdotool" in m for m in messages)

    def test_does_not_fall_back_to_pynput(self, wayland, no_tools, monkeypatch):
        """pynput can't inject into other windows on Wayland: never used there."""
        ensure = MagicMock()
        monkeypatch.setattr(KeyboardService, "_ensure_controller", ensure)
        assert KeyboardService().paste() is False
        ensure.assert_not_called()


class TestWaylandWithTools:
    def test_paste_with_ydotool_ok(self, wayland, monkeypatch):
        _tools(monkeypatch, ydotool=True)
        run = MagicMock(return_value=_CompletedProcess(0))
        monkeypatch.setattr(keyboard_actions.subprocess, "run", run)

        assert KeyboardService().paste() is True
        args = run.call_args[0][0]
        assert args[0] == "/usr/bin/ydotool"
        assert args[1] == "key"

    def test_enter_with_ydotool_ok(self, wayland, monkeypatch):
        _tools(monkeypatch, ydotool=True)
        monkeypatch.setattr(
            keyboard_actions.subprocess, "run", lambda *a, **k: _CompletedProcess(0)
        )
        assert KeyboardService().enter() is True

    def test_falls_back_to_xdotool_when_ydotool_fails(self, wayland, monkeypatch):
        _tools(monkeypatch, ydotool=True, xdotool=True)
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd[0])
            if cmd[0].endswith("ydotool"):
                return _CompletedProcess(1, b"no daemon")
            return _CompletedProcess(0)

        monkeypatch.setattr(keyboard_actions.subprocess, "run", fake_run)

        assert KeyboardService().paste() is True
        assert calls == ["/usr/bin/ydotool", "/usr/bin/xdotool"]

    def test_returns_false_when_every_tool_fails(self, wayland, monkeypatch):
        _tools(monkeypatch, ydotool=True, xdotool=True)
        monkeypatch.setattr(
            keyboard_actions.subprocess,
            "run",
            lambda *a, **k: _CompletedProcess(1, b"boom"),
        )
        assert KeyboardService().paste() is False


class TestNonWayland:
    """On X11/Windows/macOS the pynput path is unchanged and reports success."""

    @pytest.fixture(autouse=True)
    def _not_wayland(self, monkeypatch):
        monkeypatch.setattr(keyboard_actions, "_is_wayland", lambda: False)

    @pytest.fixture
    def service(self, monkeypatch):
        service = KeyboardService()
        service._controller = MagicMock()
        KeyboardService._keyboard = MagicMock()
        monkeypatch.setattr(KeyboardService, "_ensure_controller", lambda self: None)
        return service

    def test_paste_uses_pynput_and_returns_true(self, service, monkeypatch):
        run = MagicMock()
        monkeypatch.setattr(keyboard_actions.subprocess, "run", run)

        assert service.paste() is True
        run.assert_not_called()
        assert service._controller.press.call_count == 2
        assert service._controller.release.call_count == 2

    def test_enter_and_copy_return_true(self, service):
        assert service.enter() is True
        assert service.copy() is True

    def test_paste_reraises_pynput_errors(self, service):
        service._controller.press.side_effect = RuntimeError("no display")
        with pytest.raises(RuntimeError):
            service.paste()


@pytest.fixture
def controller(tmp_path, qtbot):
    """Controller with mocked external services."""
    settings = Settings(config_path=str(tmp_path / "config.yaml"))
    settings.transcription_api_key = "sk-dicto-test"
    with (
        patch("src.controller.AudioRecorder"),
        patch("src.controller.Transcriber"),
        patch("src.controller.HotkeyListener"),
        patch("src.controller.KeyboardService"),
    ):
        ctrl = Controller(settings)
        yield ctrl
        qtbot.wait(50)
        ctrl._pool.shutdown(wait=False, cancel_futures=True)


def _delivery(controller, text: str = "dictated", previous: str = "previous"):
    """A delivery like the one _on_transcribe_finished builds."""
    controller._delivery_generation += 1
    return _Delivery(
        previous=previous,
        copied_text=text,
        generation=controller._delivery_generation,
    )


class TestControllerAutoPaste:
    def test_warns_user_when_paste_did_not_happen(self, controller, qtbot):
        controller.keyboard.paste.return_value = False
        controller.current_state = AppState.SUCCESS

        with qtbot.waitSignal(controller.warning_occurred, timeout=1000) as blocker:
            controller._do_auto_paste(_delivery(controller), auto_enter=False)

        message = blocker.args[0]
        assert "Ctrl+V" in message
        assert "ydotool" in message
        # A failed paste is a partial success: state must stay untouched.
        assert controller.current_state == AppState.SUCCESS

    def test_warning_is_not_reported_as_an_error(self, controller, qtbot):
        """It must not reach error_occurred: the UI paints that red and cuts it."""
        controller.keyboard.paste.return_value = False
        errors = []
        controller.error_occurred.connect(errors.append)

        controller._do_auto_paste(_delivery(controller), auto_enter=False)
        qtbot.wait(120)

        assert errors == []

    def test_skips_auto_enter_when_paste_failed(self, controller, qtbot):
        controller.keyboard.paste.return_value = False
        controller._do_auto_paste(_delivery(controller), auto_enter=True)
        qtbot.wait(120)
        controller.keyboard.enter.assert_not_called()

    def test_paste_raising_is_treated_as_a_failed_paste(self, controller, qtbot):
        """pynput raises on X11/Windows; that must warn, not vanish silently."""
        controller.keyboard.paste.side_effect = RuntimeError("no display")
        delivery = _delivery(controller)

        with qtbot.waitSignal(controller.warning_occurred, timeout=1000):
            controller._do_auto_paste(delivery, auto_enter=True)

        assert delivery.paste_failed is True
        qtbot.wait(120)
        controller.keyboard.enter.assert_not_called()

    def test_failed_paste_keeps_text_on_clipboard(self, controller, qtbot):
        """The user was told to press Ctrl+V, so our text must survive.

        Driven through the real path — a full transcription, the +100ms
        auto-paste timer, then the 1.2s restore timer — because the bug this
        guards against lives entirely in that timing gap. Calling
        ``_restore_clipboard`` directly would skip it and pass regardless.
        """
        controller.settings.auto_paste = True
        controller.settings.restore_clipboard = True
        controller.keyboard.paste.return_value = False
        controller._run_clipboard_io = lambda fn: fn()

        with patch("src.controller.ClipboardManager") as clipboard:
            clipboard.paste.return_value = "previous"
            clipboard.copy.return_value = True
            controller._on_transcribe_finished("dictated")
            qtbot.wait(controller.CLIPBOARD_RESTORE_DELAY_MS + 300)
            clipboard.restore.assert_not_called()

    def test_no_warning_when_paste_succeeded(self, controller, qtbot):
        controller.keyboard.paste.return_value = True
        received = []
        controller.error_occurred.connect(received.append)
        controller.warning_occurred.connect(received.append)

        controller._do_auto_paste(_delivery(controller), auto_enter=True)
        qtbot.wait(120)

        assert received == []
        controller.keyboard.enter.assert_called_once()
