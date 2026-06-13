"""Unit tests for the result router (pure delivery decision)."""

from __future__ import annotations

from dicto.core.result_router import route_result


def test_empty_text_is_a_noop():
    d = route_result(text="   ", auto_paste=True, auto_enter=True, can_inject=True)
    assert not d.inject
    assert not d.clipboard
    assert not d.save_to_library
    assert d.primary == "library"


def test_inject_when_auto_paste_and_capable():
    d = route_result(text="hi", auto_paste=True, auto_enter=False, can_inject=True)
    assert d.inject
    assert d.clipboard  # injection stages on the clipboard too
    assert not d.auto_enter
    assert d.save_to_library
    assert not d.used_fallback
    assert d.primary == "cursor"


def test_auto_enter_passes_through():
    d = route_result(text="hi", auto_paste=True, auto_enter=True, can_inject=True)
    assert d.inject and d.auto_enter


def test_fallback_to_clipboard_when_injection_unavailable():
    d = route_result(text="hi", auto_paste=True, auto_enter=True, can_inject=False)
    assert not d.inject
    assert d.clipboard
    assert d.used_fallback
    assert not d.auto_enter  # no cursor → enter makes no sense
    assert d.primary == "clipboard"


def test_clipboard_when_auto_paste_off():
    d = route_result(text="hi", auto_paste=False, auto_enter=True, can_inject=True)
    assert not d.inject
    assert d.clipboard
    assert not d.used_fallback
    assert d.primary == "clipboard"
