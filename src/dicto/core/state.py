"""Application state machine — pure logic, no Qt.

The app moves through a small set of states. ``AppState`` is the high-level
status surfaced to the tray icon and overlay; ``RecordingSession`` tracks the
lifecycle of a single recording (which can be paused and resumed) and the audio
chunks already written to disk.

This module imports nothing from Qt, the network, or the OS so it can be unit
tested in isolation.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class AppState(enum.Enum):
    """High-level status of the application, shown in the tray and overlay."""

    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"

    @property
    def is_busy(self) -> bool:
        """True while a recording or transcription is in flight."""
        return self in (AppState.RECORDING, AppState.PAUSED, AppState.PROCESSING)


# Allowed transitions between states. Any transition not listed here is a bug.
_TRANSITIONS: dict[AppState, frozenset[AppState]] = {
    AppState.IDLE: frozenset({AppState.RECORDING, AppState.ERROR}),
    AppState.RECORDING: frozenset(
        {AppState.PAUSED, AppState.PROCESSING, AppState.IDLE, AppState.ERROR}
    ),
    AppState.PAUSED: frozenset(
        {AppState.RECORDING, AppState.PROCESSING, AppState.IDLE, AppState.ERROR}
    ),
    AppState.PROCESSING: frozenset({AppState.SUCCESS, AppState.ERROR, AppState.IDLE}),
    AppState.SUCCESS: frozenset({AppState.IDLE, AppState.RECORDING}),
    AppState.ERROR: frozenset({AppState.IDLE, AppState.RECORDING}),
}


def can_transition(src: AppState, dst: AppState) -> bool:
    """Return whether moving from ``src`` to ``dst`` is allowed."""
    return dst in _TRANSITIONS.get(src, frozenset())


class InvalidTransition(RuntimeError):
    """Raised when an illegal state transition is attempted."""

    def __init__(self, src: AppState, dst: AppState) -> None:
        super().__init__(f"illegal transition {src.value} -> {dst.value}")
        self.src = src
        self.dst = dst


@dataclass
class StateMachine:
    """Tiny guarded state machine over :class:`AppState`.

    Holds no Qt signals — the app layer observes changes via the event bus
    (``core.events``) and re-emits them as Qt signals where needed.
    """

    state: AppState = AppState.IDLE

    def transition(self, dst: AppState) -> AppState:
        """Move to ``dst`` if allowed, else raise :class:`InvalidTransition`."""
        if dst is self.state:
            return self.state
        if not can_transition(self.state, dst):
            raise InvalidTransition(self.state, dst)
        self.state = dst
        return self.state

    def reset(self) -> None:
        self.state = AppState.IDLE


class SessionStatus(enum.Enum):
    """Lifecycle of a single recording session."""

    RECORDING = "recording"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class RecordingSession:
    """A single recording: its on-disk chunks and pause/resume state.

    Audio is the sacred datum — every chunk is a path to a file already written
    to disk, never raw bytes held in RAM. Duration is accumulated across
    pause/resume cycles so a class break does not split the file.
    """

    session_id: str
    status: SessionStatus = SessionStatus.RECORDING
    chunk_paths: list[str] = field(default_factory=list)
    # Seconds of audio captured across all resumed segments.
    recorded_seconds: float = 0.0

    def add_chunk(self, path: str, seconds: float) -> None:
        """Register a chunk flushed to disk."""
        if self.status is SessionStatus.STOPPED:
            raise RuntimeError("cannot add chunks to a stopped session")
        self.chunk_paths.append(path)
        self.recorded_seconds += seconds

    def pause(self) -> None:
        if self.status is not SessionStatus.RECORDING:
            raise RuntimeError(f"cannot pause from {self.status.value}")
        self.status = SessionStatus.PAUSED

    def resume(self) -> None:
        if self.status is not SessionStatus.PAUSED:
            raise RuntimeError(f"cannot resume from {self.status.value}")
        self.status = SessionStatus.RECORDING

    def stop(self) -> None:
        self.status = SessionStatus.STOPPED

    @property
    def is_empty(self) -> bool:
        return not self.chunk_paths
