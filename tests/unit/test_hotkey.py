"""Unit tests for the pure hotkey matcher (no pynput, headless)."""

from __future__ import annotations

from dicto.services.hotkey import HotkeyMatcher, canonical_modifier


def _matcher(mode: str = "hold"):
    events: list[str] = []
    m = HotkeyMatcher(
        ["ctrl", "shift"],
        "space",
        mode=mode,
        on_start=lambda: events.append("start"),
        on_stop=lambda: events.append("stop"),
    )
    return m, events


def test_canonical_modifier_normalises_sides():
    assert canonical_modifier("ctrl_l") == "ctrl"
    assert canonical_modifier("CTRL_R") == "ctrl"
    assert canonical_modifier("win") == "cmd"
    assert canonical_modifier("space") is None


def test_hold_start_on_combo_stop_on_release():
    m, events = _matcher("hold")
    m.on_press("ctrl")
    m.on_press("shift")
    m.on_press("space")
    assert events == ["start"]
    m.on_release("space")
    assert events == ["start", "stop"]


def test_hold_ignores_key_without_all_modifiers():
    m, events = _matcher("hold")
    m.on_press("ctrl")
    m.on_press("space")  # shift missing
    assert events == []


def test_hold_swallows_autorepeat():
    m, events = _matcher("hold")
    m.on_press("ctrl")
    m.on_press("shift")
    m.on_press("space")
    m.on_press("space")  # OS auto-repeat while held
    m.on_press("space")
    assert events == ["start"]
    m.on_release("space")
    assert events == ["start", "stop"]


def test_side_modifiers_satisfy_generic_requirement():
    m, events = _matcher("hold")
    m.on_press("ctrl_l")
    m.on_press("shift_r")
    m.on_press("space")
    assert events == ["start"]


def test_toggle_alternates_start_stop():
    m, events = _matcher("toggle")
    # First full press: start.
    m.on_press("ctrl")
    m.on_press("shift")
    m.on_press("space")
    m.on_release("space")
    assert events == ["start"]
    # Second full press: stop.
    m.on_press("space")
    m.on_release("space")
    assert events == ["start", "stop"]
    # Third: start again.
    m.on_press("space")
    m.on_release("space")
    assert events == ["start", "stop", "start"]


def test_toggle_release_does_not_stop():
    m, events = _matcher("toggle")
    m.on_press("ctrl")
    m.on_press("shift")
    m.on_press("space")
    assert events == ["start"]
    m.on_release("space")
    # Release must NOT fire stop in toggle mode.
    assert events == ["start"]


def test_reset_clears_held_state():
    m, events = _matcher("hold")
    m.on_press("ctrl")
    m.on_press("shift")
    m.on_press("space")
    m.reset()
    # After reset, a lone space press should not start (modifiers cleared).
    m.on_press("space")
    assert events == ["start"]


def test_callback_exception_is_swallowed():
    def boom() -> None:
        raise RuntimeError("nope")

    m = HotkeyMatcher(["ctrl"], "space", mode="hold", on_start=boom)
    m.on_press("ctrl")
    m.on_press("space")  # must not raise
