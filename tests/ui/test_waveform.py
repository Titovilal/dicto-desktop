"""UI tests for WaveformWidget."""

from __future__ import annotations

import pytest

from src.ui.waveform import WaveformWidget


@pytest.fixture
def waveform(qtbot):
    w = WaveformWidget(bar_count=10, bar_width=2, bar_gap=1, height=28, mode="wave")
    qtbot.addWidget(w)
    return w


class TestWaveformModes:
    def test_wave_mode_starts_timer(self, qtbot):
        w = WaveformWidget(mode="wave")
        qtbot.addWidget(w)
        w.start()
        assert w._timer.isActive()
        w.stop()

    def test_pulse_mode_starts_timer(self, qtbot):
        w = WaveformWidget(mode="pulse")
        qtbot.addWidget(w)
        w.start()
        assert w._timer.isActive()
        w.stop()

    def test_settle_mode_starts_timer(self, qtbot):
        w = WaveformWidget(mode="settle")
        qtbot.addWidget(w)
        w.start()
        assert w._timer.isActive()
        w.stop()

    def test_live_mode_does_not_start_timer(self, qtbot):
        w = WaveformWidget(mode="live")
        qtbot.addWidget(w)
        w.start()
        assert not w._timer.isActive()

    def test_stop_stops_timer(self, waveform):
        waveform.start()
        waveform.stop()
        assert not waveform._timer.isActive()


class TestSetLevel:
    def test_set_level_scrolls_bars(self, waveform):
        waveform.start()
        waveform.bar_heights = [0.0] * waveform.bar_count
        waveform.set_level(0.8)
        assert waveform.bar_heights[-1] == 0.8
        assert len(waveform.bar_heights) == waveform.bar_count

    def test_multiple_levels(self, waveform):
        waveform.bar_heights = [0.0] * waveform.bar_count
        waveform.set_level(0.5)
        waveform.set_level(0.9)
        assert waveform.bar_heights[-1] == 0.9
        assert waveform.bar_heights[-2] == 0.5


class TestPaintEvent:
    def test_paint_does_not_crash(self, waveform):
        """Render each mode without crashing."""
        for mode in ("wave", "pulse", "settle", "live"):
            waveform.mode = mode
            waveform.bar_heights = [0.5] * waveform.bar_count
            waveform.repaint()
