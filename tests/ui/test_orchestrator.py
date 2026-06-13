"""Tests for RecordingOrchestrator wiring (needs a QApplication for signals)."""

from __future__ import annotations

import pytest

from dicto.config.settings import Settings
from dicto.core import events
from dicto.core.pipeline import Pipeline
from dicto.core.state import AppState

pytest.importorskip("PySide6.QtWidgets")


class _FakeCapture:
    """Stands in for AudioCapture: yields one known chunk path on stop."""

    error = None

    def __init__(self, chunk: str) -> None:
        self._chunk = chunk
        self.paused = False

    is_running = False

    def start(self) -> bool:
        return True

    def stop(self) -> list[str]:
        return [self._chunk]

    def set_paused(self, paused: bool) -> None:
        self.paused = paused

    @property
    def chunk_paths(self) -> list[str]:
        return [self._chunk]

    @property
    def recorded_seconds(self) -> float:
        return 1.0


@pytest.fixture
def orchestrator(qtbot):
    from dicto.orchestrator import RecordingOrchestrator

    settings = Settings()
    settings.transcription.api_key = "test-key"
    bus = events.EventBus()
    orch = RecordingOrchestrator(settings, bus)
    yield orch
    orch.dispose()


def _drive_to_recording(orch, chunk: str) -> None:
    """Put the orchestrator into RECORDING over a fake capture + fake STT."""
    orch._capture = _FakeCapture(chunk)
    orch._pipeline = Pipeline(
        "sess", orch._capture, lambda p: "hola mundo", bus=orch.bus, retry_backoff=0.0
    )
    orch._sm.state = AppState.RECORDING


def test_stop_builds_client_and_transcribes(qtbot, orchestrator, tmp_path):
    # The client must actually be stored on the orchestrator, not just returned —
    # the transcribe callable reads ``orch._client`` on the worker thread.
    chunk = str(tmp_path / "c0.wav")
    _drive_to_recording(orchestrator, chunk)

    done: list[str] = []
    orchestrator.transcriptionDone.connect(done.append)

    orchestrator.stop_recording()  # emits intent → _do_stop on this thread
    # _build_client must have populated _client before submitting the worker.
    # The instant fake STT may already have finished and cleaned the client up
    # on the worker thread, so "done has fired" also proves the client existed.
    assert orchestrator._client is not None or done

    qtbot.waitUntil(lambda: bool(done), timeout=3000)
    assert done == ["hola mundo"]


def test_stop_without_api_key_errors_but_keeps_audio(qtbot, tmp_path):
    from dicto.orchestrator import RecordingOrchestrator

    settings = Settings()
    settings.transcription.api_key = ""  # no key
    orch = RecordingOrchestrator(settings, events.EventBus())
    try:
        chunk = str(tmp_path / "c0.wav")
        _drive_to_recording(orch, chunk)

        errors: list[tuple[str, str]] = []
        orch.errorOccurred.connect(lambda m, c: errors.append((m, c)))
        orch.stop_recording()

        qtbot.waitUntil(lambda: bool(errors), timeout=2000)
        assert errors[0][1] == "auth"
        assert orch.state is AppState.ERROR
    finally:
        orch.dispose()


def test_start_records_even_without_api_key(qtbot, tmp_path, monkeypatch):
    # Audio is sacred: a missing key must NOT block recording from starting.
    from dicto import orchestrator as orch_mod
    from dicto.orchestrator import RecordingOrchestrator

    settings = Settings()
    settings.transcription.api_key = ""

    # Stub AudioCapture so we don't touch real hardware.
    chunk = str(tmp_path / "c0.wav")

    class _Cap(_FakeCapture):
        def __init__(self, *a, **k) -> None:
            super().__init__(chunk)

    monkeypatch.setattr(orch_mod, "AudioCapture", _Cap)
    orch = RecordingOrchestrator(settings, events.EventBus())
    try:
        states: list[AppState] = []
        orch.stateChanged.connect(states.append)
        orch.start_recording()
        qtbot.waitUntil(lambda: AppState.RECORDING in states, timeout=2000)
        assert orch.state is AppState.RECORDING
    finally:
        orch.dispose()
