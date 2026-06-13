"""Unit tests for the Qt-free state machine and recording session."""

from __future__ import annotations

import pytest

from dicto.core.state import (
    AppState,
    InvalidTransition,
    RecordingSession,
    SessionStatus,
    StateMachine,
    can_transition,
)


def test_app_state_is_busy():
    assert AppState.RECORDING.is_busy
    assert AppState.PAUSED.is_busy
    assert AppState.PROCESSING.is_busy
    assert not AppState.IDLE.is_busy
    assert not AppState.SUCCESS.is_busy


def test_legal_transition_sequence():
    sm = StateMachine()
    assert sm.state is AppState.IDLE
    sm.transition(AppState.RECORDING)
    sm.transition(AppState.PAUSED)
    sm.transition(AppState.RECORDING)
    sm.transition(AppState.PROCESSING)
    sm.transition(AppState.SUCCESS)
    sm.transition(AppState.IDLE)
    assert sm.state is AppState.IDLE


def test_transition_to_same_state_is_noop():
    sm = StateMachine()
    assert sm.transition(AppState.IDLE) is AppState.IDLE


def test_illegal_transition_raises():
    sm = StateMachine()
    with pytest.raises(InvalidTransition):
        sm.transition(AppState.SUCCESS)  # idle -> success not allowed


def test_can_transition_table():
    assert can_transition(AppState.IDLE, AppState.RECORDING)
    assert not can_transition(AppState.IDLE, AppState.PROCESSING)
    assert can_transition(AppState.ERROR, AppState.RECORDING)


def test_recording_session_accumulates_chunks_and_duration():
    s = RecordingSession(session_id="abc")
    s.add_chunk("c0.wav", 5.0)
    s.add_chunk("c1.wav", 4.5)
    assert s.chunk_paths == ["c0.wav", "c1.wav"]
    assert s.recorded_seconds == pytest.approx(9.5)
    assert not s.is_empty


def test_recording_session_pause_resume_keeps_duration():
    s = RecordingSession(session_id="abc")
    s.add_chunk("c0.wav", 10.0)
    s.pause()
    assert s.status is SessionStatus.PAUSED
    s.resume()
    s.add_chunk("c1.wav", 10.0)
    assert s.recorded_seconds == pytest.approx(20.0)


def test_recording_session_stop_blocks_chunks():
    s = RecordingSession(session_id="abc")
    s.stop()
    assert s.status is SessionStatus.STOPPED
    with pytest.raises(RuntimeError):
        s.add_chunk("late.wav", 1.0)


def test_recording_session_invalid_pause_resume():
    s = RecordingSession(session_id="abc")
    with pytest.raises(RuntimeError):
        s.resume()  # not paused
    s.pause()
    with pytest.raises(RuntimeError):
        s.pause()  # already paused
