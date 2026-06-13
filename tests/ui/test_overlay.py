"""UI tests for the overlay: elapsed formatting (pure) + widget behaviour.

The widget tests need a QApplication; they use pytest-qt's ``qtbot`` and are
skipped automatically where Qt cannot create a display.
"""

from __future__ import annotations

import pytest

from dicto.config.settings import Settings
from dicto.core.state import AppState
from dicto.ui.overlay.controls import format_elapsed

# Skip the whole widget section gracefully if Qt has no platform plugin.
pytest.importorskip("PySide6.QtWidgets")


# ── pure: elapsed formatting ──────────────────────────────────────────────


def test_format_elapsed_under_a_minute():
    assert format_elapsed(0) == "0:00"
    assert format_elapsed(5) == "0:05"
    assert format_elapsed(59) == "0:59"


def test_format_elapsed_minutes():
    assert format_elapsed(60) == "1:00"
    assert format_elapsed(125) == "2:05"
    assert format_elapsed(3599) == "59:59"


def test_format_elapsed_hours():
    assert format_elapsed(3600) == "1:00:00"
    assert format_elapsed(3661) == "1:01:01"


# ── widget behaviour ──────────────────────────────────────────────────────


@pytest.fixture
def theme(qtbot):
    from PySide6.QtWidgets import QApplication

    from dicto.ui.theme.manager import ThemeManager

    return ThemeManager(QApplication.instance(), theme="light")


@pytest.fixture
def settings(tmp_path):
    s = Settings()
    s._path = tmp_path / "config.yaml"
    return s


def test_overlay_hidden_by_default(qtbot, theme, settings):
    from dicto.ui.overlay.overlay import Overlay

    overlay = Overlay(theme, settings)
    qtbot.addWidget(overlay)
    assert not overlay.isVisible()


def test_overlay_shows_on_recording(qtbot, theme, settings):
    from dicto.ui.overlay.overlay import Overlay

    overlay = Overlay(theme, settings)
    qtbot.addWidget(overlay)
    overlay.set_state(AppState.RECORDING)
    assert overlay.isVisible()


def test_overlay_remembers_dragged_position(qtbot, theme, settings):
    from dicto.ui.overlay.overlay import Overlay

    overlay = Overlay(theme, settings)
    qtbot.addWidget(overlay)
    overlay.move(321, 234)
    overlay._persist_position()
    assert settings.overlay.x == 321
    assert settings.overlay.y == 234


def test_overlay_reset_position_clears_saved(qtbot, theme, settings):
    from dicto.ui.overlay.overlay import Overlay

    settings.overlay.x = 500
    settings.overlay.y = 400
    overlay = Overlay(theme, settings)
    qtbot.addWidget(overlay)
    overlay.reset_position()
    assert settings.overlay.x is None
    assert settings.overlay.y is None


def test_overlay_pause_button_emits_pause_then_resume(qtbot, theme, settings):
    from dicto.ui.overlay.overlay import Overlay

    overlay = Overlay(theme, settings)
    qtbot.addWidget(overlay)
    overlay.set_state(AppState.RECORDING)

    fired: list[str] = []
    overlay.pauseRequested.connect(lambda: fired.append("pause"))
    overlay.resumeRequested.connect(lambda: fired.append("resume"))

    overlay._controls._on_pause_clicked()  # first click → pause
    overlay._controls._on_pause_clicked()  # second click → resume
    assert fired == ["pause", "resume"]


def test_overlay_stop_button_emits_stop(qtbot, theme, settings):
    from dicto.ui.overlay.overlay import Overlay

    overlay = Overlay(theme, settings)
    qtbot.addWidget(overlay)
    overlay.set_state(AppState.RECORDING)

    fired: list[str] = []
    overlay.stopRequested.connect(lambda: fired.append("stop"))
    overlay._controls.stopRequested.emit()
    assert fired == ["stop"]


def test_overlay_success_then_error_states_apply(qtbot, theme, settings):
    from dicto.ui.overlay.overlay import Overlay

    overlay = Overlay(theme, settings)
    qtbot.addWidget(overlay)
    # Should not raise as it walks the state machine visuals.
    overlay.set_state(AppState.RECORDING)
    overlay.set_state(AppState.PROCESSING)
    overlay.set_state(AppState.SUCCESS)
    assert overlay._state is AppState.SUCCESS
