"""Unit tests for AudioRecorder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.services.recorder import AudioRecorder


class TestInit:
    def test_default_params(self):
        with patch("src.services.recorder.sd"):
            r = AudioRecorder()
            assert r.sample_rate == 16000
            assert r.channels == 1
            assert r.max_duration == 7200
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

    def test_get_duration_after_frames_cleared(self):
        # stop_recording() clears self.frames; the duration must still be
        # reported from the saved value rather than collapsing to 0.0.
        with patch("src.services.recorder.sd"):
            r = AudioRecorder(sample_rate=16000)
            r._last_duration = 2.5
            r.frames = []
            assert r.get_recording_duration() == pytest.approx(2.5)


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


class TestStuckRecordingThread:
    """Regression: a recording thread that outlives its join() must not wedge
    the recorder. Reported as "Recording already in progress" after a couple of
    recordings, after which every later hotkey press failed permanently.
    """

    def test_stop_disowns_thread_that_ignores_join(self):
        """stop_recording must not leave is_recording set when the thread hangs."""
        import threading

        with patch("src.services.recorder.sd"):
            r = AudioRecorder()
            release = threading.Event()

            def hang():
                release.wait(timeout=10)

            r.is_recording = True
            r.recording_thread = threading.Thread(target=hang, daemon=True)
            r.recording_thread.start()
            r.frames = [np.zeros((10, 1), dtype=np.int16)]

            with patch.object(r.recording_thread, "join", lambda timeout=None: None):
                r.stop_recording()

            # The flag is down and the thread was disowned, so a new recording
            # is allowed even though the old thread is still running.
            assert r.is_recording is False
            assert r.recording_thread is None
            release.set()

    def test_stale_thread_finally_does_not_clobber_next_recording(self):
        """The wedged thread's finally block must not touch the new session."""
        with patch("src.services.recorder.sd"):
            r = AudioRecorder()

            # Session 1 is running; session 2 has since replaced it.
            r._session_id = 2
            r.is_recording = True
            r.frames = [np.zeros((5, 1), dtype=np.int16)]

            # The old thread (session=1) finally reaches its finally block.
            # Force it down the abort path immediately.
            with patch.object(
                r, "_negotiate_mic_samplerate", side_effect=RuntimeError("device gone")
            ):
                r._record_audio(session=1)

            # Session 2's state survives untouched.
            assert r.is_recording is True, "stale thread cleared the live flag"
            assert len(r.frames) == 1, "stale thread wiped live audio frames"
            assert r._record_error is None, "stale thread leaked its error"

    def test_recorder_recovers_after_a_hung_recording(self):
        """End to end: a hung recording must not block the following one."""
        import threading

        with patch("src.services.recorder.sd"):
            r = AudioRecorder()
            release = threading.Event()

            r.is_recording = True
            r.recording_thread = threading.Thread(
                target=lambda: release.wait(timeout=10), daemon=True
            )
            r.recording_thread.start()
            r.frames = [np.zeros((10, 1), dtype=np.int16)]
            with patch.object(r.recording_thread, "join", lambda timeout=None: None):
                r.stop_recording()

            # The next press must be accepted, not rejected as "already in progress".
            with patch.object(r, "_record_audio"):
                assert r.start_recording() is True
            new_session = r._session_id

            # Now the hung thread from the FIRST recording finally unblocks and
            # runs its finally block, while recording #2 is live. This is the
            # exact ordering from the bug report; it must be a no-op.
            release.set()
            with patch.object(
                r, "_negotiate_mic_samplerate", side_effect=RuntimeError("device gone")
            ):
                r._record_audio(session=new_session - 1)

            assert r.is_recording is True, "the hung thread killed recording #2"
