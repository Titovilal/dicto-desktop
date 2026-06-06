"""Unit tests for clipboard + injector services (headless, injected backends)."""

from __future__ import annotations

from dicto.services.clipboard import Clipboard, _NoopBackend
from dicto.services.injector import Injector


# ── Clipboard ──────────────────────────────────────────────────────────────


def test_clipboard_copy_and_paste_roundtrip():
    cb = Clipboard(backend=_NoopBackend())
    assert cb.copy("hello")
    assert cb.paste() == "hello"


def test_clipboard_ignores_empty_copy():
    cb = Clipboard(backend=_NoopBackend())
    assert not cb.copy("")
    assert cb.paste() == ""


def test_clipboard_swallows_backend_errors():
    class Boom:
        def write(self, text):
            raise RuntimeError("nope")

        def read(self):
            raise RuntimeError("nope")

    cb = Clipboard(backend=Boom())
    assert cb.copy("x") is False
    assert cb.paste() == ""


# ── Injector ─────────────────────────────────────────────────────────────


class _FakeKey:
    ctrl = "ctrl"
    enter = "enter"


class _FakeKeyboardModule:
    Key = _FakeKey


class _FakeController:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    def press(self, k):
        self.events.append(("press", k))

    def release(self, k):
        self.events.append(("release", k))


def _injector_with_fake_controller():
    cb = Clipboard(backend=_NoopBackend())
    inj = Injector(cb)
    ctrl = _FakeController()
    inj._keyboard = _FakeKeyboardModule()
    inj._controller = ctrl
    return inj, ctrl, cb


def test_injector_stages_clipboard_and_sends_paste():
    inj, ctrl, cb = _injector_with_fake_controller()
    assert inj.inject("hola")
    assert cb.paste() == "hola"  # staged on clipboard
    # Ctrl down, v down/up, Ctrl up.
    assert ("press", "ctrl") in ctrl.events
    assert ("press", "v") in ctrl.events
    assert ("release", "v") in ctrl.events


def test_injector_auto_enter():
    inj, ctrl, _ = _injector_with_fake_controller()
    inj.inject("x", auto_enter=True)
    assert ("press", "enter") in ctrl.events


def test_injector_no_enter_by_default():
    inj, ctrl, _ = _injector_with_fake_controller()
    inj.inject("x")
    assert ("press", "enter") not in ctrl.events


def test_injector_empty_text_is_noop():
    inj, ctrl, _ = _injector_with_fake_controller()
    assert inj.inject("") is False
    assert ctrl.events == []


def test_injector_unavailable_falls_back_to_clipboard():
    cb = Clipboard(backend=_NoopBackend())
    inj = Injector(cb)
    inj._unavailable = True  # simulate no pynput backend
    assert inj.available() is False
    # inject() returns False but still stages the text on the clipboard.
    assert inj.inject("saved") is False
    assert cb.paste() == "saved"
