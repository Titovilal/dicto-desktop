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


class TestOverlayWarning:
    """A partial success must not look, or read, like a failure."""

    MESSAGE = "Your text is safe on the clipboard — press Ctrl+V to paste it."

    def test_shows_the_message_verbatim(self, overlay):
        """Not truncated: the actionable part sits at the end of the text."""
        overlay.show_warning(self.MESSAGE, auto_hide_delay=100000)
        assert overlay.status_label.text() == self.MESSAGE

    def test_has_no_error_prefix_and_is_not_red(self, overlay):
        from src.ui.main_window_styles import AMBER, RED

        overlay.show_warning(self.MESSAGE, auto_hide_delay=100000)
        assert overlay.current_state == "warning"
        assert not overlay.status_label.text().startswith(f"{t('error')}:")
        assert AMBER in overlay.status_label.styleSheet()
        assert RED not in overlay.status_label.styleSheet()

    def test_full_text_is_available_as_a_tooltip(self, overlay):
        overlay.show_warning(self.MESSAGE, auto_hide_delay=100000)
        assert overlay.status_label.toolTip() == self.MESSAGE


class TestOverlayActionButton:
    def test_stop_button_emits_signal(self, overlay, qtbot):
        # While recording, the record button acts as a stop button.
        overlay.show_recording()
        with qtbot.waitSignal(overlay.stop_requested, timeout=1000):
            overlay.record_btn.click()

    def test_settings_button_shows_popover(self, overlay):
        overlay.show_idle()
        overlay.show()
        overlay.action_btn.click()
        assert overlay._popover.isVisible()

    def test_record_button_emits_signal(self, overlay, qtbot):
        # In idle (settings) mode, the record button starts recording.
        overlay.show_idle()
        with qtbot.waitSignal(overlay.record_requested, timeout=1000):
            overlay.record_btn.click()


class TestOverlayPersistent:
    def test_persistent_mode_shows_idle(self, overlay):
        overlay.set_persistent(True)
        assert overlay.isVisible()
        assert overlay.current_state == "idle"

    def test_non_persistent_hides_on_idle(self, overlay):
        overlay.set_persistent(False)
        overlay.hide()
        assert not overlay.isVisible()


class TestOverlayDragging:
    """The overlay must move on Wayland, where move() is ignored and only the
    compositor's own move loop works."""

    def _press(self, overlay):
        from PySide6.QtCore import QPoint, QPointF, Qt
        from PySide6.QtGui import QMouseEvent

        return QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(10, 10),
            overlay.mapToGlobal(QPoint(10, 10)).toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

    def test_press_asks_the_compositor_to_move_the_window(self, overlay, monkeypatch):
        overlay.show()
        called = []
        handle = overlay.windowHandle()
        assert handle is not None
        monkeypatch.setattr(
            handle, "startSystemMove", lambda: (called.append(True), True)[1]
        )

        overlay.mousePressEvent(self._press(overlay))

        assert called, "startSystemMove() was never attempted"
        # The compositor owns the drag now; no manual fallback should engage.
        assert not overlay._drag_active

    def test_falls_back_to_manual_drag_when_compositor_refuses(
        self, overlay, monkeypatch
    ):
        overlay.show()
        handle = overlay.windowHandle()
        assert handle is not None
        monkeypatch.setattr(handle, "startSystemMove", lambda: False)

        overlay.mousePressEvent(self._press(overlay))

        assert overlay._drag_active

    def test_popover_follows_the_window_when_it_moves(self, overlay):
        from PySide6.QtCore import QPoint

        overlay.show()
        overlay._show_popover_at_button()
        before = overlay._popover.pos()

        overlay.move(overlay.pos() + QPoint(120, 90))

        assert overlay._popover.pos() != before
