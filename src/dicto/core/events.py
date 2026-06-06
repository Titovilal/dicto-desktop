"""Typed domain event bus — decouples ``core`` from Qt.

The core emits plain dataclass events through this bus; the app layer
(``app.py``) subscribes and bridges them to Qt signals for the UI. Keeping the
bus Qt-free means the whole domain can be driven and asserted in unit tests
without a ``QApplication``.

Usage::

    bus = EventBus()
    bus.subscribe(StateChanged, lambda e: print(e.new))
    bus.publish(StateChanged(old=AppState.IDLE, new=AppState.RECORDING))
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from dicto.core.state import AppState

logger = logging.getLogger(__name__)


# ── Event types ──────────────────────────────────────────────────────────


class Event:
    """Base class for all domain events."""


@dataclass(frozen=True)
class StateChanged(Event):
    old: AppState
    new: AppState


@dataclass(frozen=True)
class RecordingStarted(Event):
    session_id: str


@dataclass(frozen=True)
class RecordingProgress(Event):
    session_id: str
    seconds: float
    # Live RMS level in 0..1, for the waveform/meter.
    level: float = 0.0


@dataclass(frozen=True)
class RecordingPaused(Event):
    session_id: str


@dataclass(frozen=True)
class RecordingResumed(Event):
    session_id: str


@dataclass(frozen=True)
class RecordingStopped(Event):
    session_id: str
    chunk_paths: tuple[str, ...]


@dataclass(frozen=True)
class TranscriptionProgress(Event):
    """Partial result emitted while a long recording transcribes chunk by chunk."""

    session_id: str
    text: str
    done: int
    total: int


@dataclass(frozen=True)
class TranscriptionDone(Event):
    session_id: str
    text: str


@dataclass(frozen=True)
class ErrorOccurred(Event):
    message: str
    # Optional machine-readable code (e.g. "auth", "rate_limit", "network").
    code: str | None = None


# ── Bus ──────────────────────────────────────────────────────────────────

E = TypeVar("E", bound=Event)
Handler = Callable[[Event], None]


class EventBus:
    """Minimal synchronous publish/subscribe bus, keyed by event type.

    Handlers are invoked in subscription order. A failing handler is logged and
    swallowed so one bad subscriber cannot break the others.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[Event], list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: type[E], handler: Callable[[E], None]) -> Callable[[], None]:
        """Register ``handler`` for ``event_type``; returns an unsubscribe fn."""
        handlers = self._handlers[event_type]
        handlers.append(handler)  # type: ignore[arg-type]

        def unsubscribe() -> None:
            try:
                handlers.remove(handler)  # type: ignore[arg-type]
            except ValueError:
                pass

        return unsubscribe

    def publish(self, event: Event) -> None:
        """Deliver ``event`` to every handler subscribed to its exact type."""
        for handler in list(self._handlers.get(type(event), ())):
            try:
                handler(event)
            except Exception:  # noqa: BLE001 — one bad handler must not break the bus
                logger.exception("event handler failed for %s", type(event).__name__)

    def clear(self) -> None:
        """Drop all subscriptions (mainly for tests)."""
        self._handlers.clear()
