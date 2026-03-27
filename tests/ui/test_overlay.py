"""UI tests for OverlayWindow state changes."""

from __future__ import annotations

import pytest

from src.i18n import t
from src.ui.overlay import OverlayWindow


@pytest.fixture
def overlay(qtbot):
    w = OverlayWindow()
    qtbot.addWidget(w)
    return w


class TestOverlayStates:
    def test_show_idle(self, overlay):
        overlay.show_idle()
        assert overlay.current_state == "idle"
        assert t("ready") in overlay.status_label.text()
        assert not overlay.icon_stack.isVisible()
        assert overlay._action_mode == "settings"

    def test_show_recording(self, overlay):
        overlay.show_recording()
        assert overlay.current_state == "recording"
        assert overlay.icon_stack.isVisible()
        assert overlay.icon_stack.currentIndex() == 0
        assert overlay._action_mode == "stop"

    def test_show_processing(self, overlay):
        overlay.show()  # processing doesn't call show() itself
        overlay.show_processing()
        assert overlay.current_state == "processing"
        assert overlay.icon_stack.isVisible()
        assert overlay.icon_stack.currentIndex() == 1
        assert overlay._action_mode == "stop"

    def test_show_success(self, overlay):
        overlay.show()
        overlay.show_success(auto_hide_delay=100000)
        assert overlay.current_state == "success"
        assert overlay.icon_stack.isVisible()
        assert overlay.icon_stack.currentIndex() == 2
        assert overlay._action_mode == "settings"

    def test_show_error(self, overlay):
        overlay.show_error("test error", auto_hide_delay=100000)
        assert overlay.current_state == "error"
        assert "test error" in overlay.status_label.text()
        assert not overlay.icon_stack.isVisible()
        assert overlay._action_mode == "settings"

    def test_show_editing(self, overlay):
        overlay.show_editing()
        assert overlay.current_state == "editing"
        assert overlay.icon_stack.isVisible()
        assert overlay.icon_stack.currentIndex() == 3
        assert overlay._action_mode == "stop"


class TestOverlayActionButton:
    def test_stop_button_emits_signal(self, overlay, qtbot):
        overlay.show_recording()
        with qtbot.waitSignal(overlay.stop_requested, timeout=1000):
            overlay.action_btn.click()

    def test_settings_button_shows_popover(self, overlay):
        overlay.show_idle()
        overlay.show()
        overlay.action_btn.click()
        assert overlay._popover.isVisible()

    def test_popover_record_emits_signal(self, overlay, qtbot):
        overlay.show()
        with qtbot.waitSignal(overlay.record_requested, timeout=1000):
            overlay._popover.record_btn.click()


class TestOverlayPersistent:
    def test_persistent_mode_shows_idle(self, overlay):
        overlay.set_persistent(True)
        assert overlay.isVisible()
        assert overlay.current_state == "idle"

    def test_non_persistent_hides_on_idle(self, overlay):
        overlay.set_persistent(False)
        overlay.hide()
        assert not overlay.isVisible()
