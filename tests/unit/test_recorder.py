"""Unit tests for AudioRecorder."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from src.services.recorder import AudioRecorder


class TestInit:

    def test_default_params(self):
        with patch("src.services.recorder.sd"):
            r = AudioRecorder()
            assert r.sample_rate == 16000
            assert r.channels == 1
            assert r.max_duration == 120
            assert r.is_recording is False

    def test_custom_params(self):
        with patch("src.services.recorder.sd"):
            r = AudioRecorder(sample_rate=44100, channels=2, max_duration=60)
            assert r.sample_rate == 44100
            assert r.channels == 2
            assert r.max_duration == 60


class TestRecordingState:

    def test_stop_when_not_recording_returns_none(self):
        with patch("src.services.recorder.sd"):
            r = AudioRecorder()
            assert r.stop_recording() is None

    def test_double_start_returns_false(self):
        with patch("src.services.recorder.sd"):
            r = AudioRecorder()
            r.is_recording = True
            assert r.start_recording() is False

    def test_get_duration_empty(self):
        with patch("src.services.recorder.sd"):
            r = AudioRecorder()
            assert r.get_recording_duration() == 0.0

    def test_get_duration_with_frames(self):
        with patch("src.services.recorder.sd"):
            r = AudioRecorder(sample_rate=16000)
            r.frames = [np.zeros(1600), np.zeros(3200)]
            assert r.get_recording_duration() == pytest.approx(0.3)


class TestCleanup:

    def test_cleanup_temp_file(self, tmp_path):
        with patch("src.services.recorder.sd"):
            r = AudioRecorder()
            temp_file = tmp_path / "test.wav"
            temp_file.write_bytes(b"\x00")
            r.temp_file_path = str(temp_file)

            r.cleanup_temp_file()
            assert not temp_file.exists()
            assert r.temp_file_path is None

    def test_cleanup_nonexistent_file(self):
        with patch("src.services.recorder.sd"):
            r = AudioRecorder()
            r.temp_file_path = "/nonexistent/file.wav"
            r.cleanup_temp_file()  # Should not raise


class TestAudioLevelCallback:

    def test_callback_is_set(self):
        with patch("src.services.recorder.sd"):
            r = AudioRecorder()
            cb = MagicMock()
            r.set_audio_level_callback(cb)
            assert r._audio_level_callback is cb
