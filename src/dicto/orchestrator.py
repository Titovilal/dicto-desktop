"""RecordingOrchestrator — app-layer glue between input, core and UI.

Owns a recording's lifecycle (start → pause/resume → stop → transcribe), runs
transcription on a worker thread, and bridges the Qt-free event bus to Qt
signals. Audio is recorded straight to disk; the API key is only needed to stop
and transcribe, so a missing key never blocks recording.
"""

from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, Signal

from dicto.audio.capture import AudioCapture
from dicto.config.settings import Settings
from dicto.core import events
from dicto.core.pipeline import Pipeline
from dicto.core.state import AppState, StateMachine
from dicto.services.api.client import ApiClient
from dicto.services.api.factory import make_transcribe_chunk
from dicto.utils.platform import get_session_audio_dir

logger = logging.getLogger(__name__)


class RecordingOrchestrator(QObject):
    """Owns recording lifecycle; bridges the domain bus to Qt signals."""

    # Bridged to the main thread for the UI (overlay/tray/window).
    stateChanged = Signal(AppState)
    levelChanged = Signal(float)
    transcriptionProgress = Signal(str, int, int)  # text, done, total
    transcriptionDone = Signal(str)
    errorOccurred = Signal(str, str)  # message, code

    # Internal intent signals. The hotkey fires on pynput's thread; emitting
    # these hops the work onto the orchestrator's (main) thread via Qt's queued
    # delivery, so capture and widget-touching state changes never run off-thread.
    _toggleIntent = Signal()
    _startIntent = Signal()
    _stopIntent = Signal()
    _pauseIntent = Signal()
    _resumeIntent = Signal()

    def __init__(self, settings: Settings, bus: events.EventBus) -> None:
        super().__init__()
        self.settings = settings
        self.bus = bus
        self._sm = StateMachine()
        self._pipeline: Pipeline | None = None
        self._capture: AudioCapture | None = None
        self._client: ApiClient | None = None
        self._session_id: str | None = None
        # One worker thread: transcription is sequential and blocking.
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dicto-stt")

        # Route intents to the real handlers on this object's thread.
        self._toggleIntent.connect(self._do_toggle)
        self._startIntent.connect(self._do_start)
        self._stopIntent.connect(self._do_stop)
        self._pauseIntent.connect(self._do_pause)
        self._resumeIntent.connect(self._do_resume)

        # Subscribe to the domain bus and re-emit as Qt signals (thread-safe via
        # Qt's queued connections when crossing threads).
        bus.subscribe(events.TranscriptionProgress, self._on_progress)
        bus.subscribe(events.TranscriptionDone, self._on_done)
        bus.subscribe(events.ErrorOccurred, self._on_error)

    # ── state helpers ───────────────────────────────────────────────────

    @property
    def state(self) -> AppState:
        return self._sm.state

    def _set_state(self, state: AppState) -> None:
        try:
            self._sm.transition(state)
        except Exception:  # noqa: BLE001 — illegal transition: log, don't crash
            logger.warning("ignored illegal state change to %s from %s", state, self._sm.state)
            return
        self.stateChanged.emit(state)

    # ── public controls (safe to call from ANY thread) ──────────────────
    # These just emit an intent; the matching ``_do_*`` runs on the
    # orchestrator's own thread, so capture/Qt work is always on the main loop.

    def toggle(self) -> None:
        """Hotkey/overlay entry point: start when idle, stop when recording."""
        self._toggleIntent.emit()

    def start_recording(self) -> None:
        self._startIntent.emit()

    def stop_recording(self) -> None:
        self._stopIntent.emit()

    def pause(self) -> None:
        self._pauseIntent.emit()

    def resume(self) -> None:
        self._resumeIntent.emit()

    # ── handlers (run on the orchestrator's thread) ─────────────────────

    def _do_toggle(self) -> None:
        if self.state in (AppState.IDLE, AppState.SUCCESS, AppState.ERROR):
            self._do_start()
        elif self.state in (AppState.RECORDING, AppState.PAUSED):
            self._do_stop()

    def _do_start(self) -> None:
        if self.state in (AppState.RECORDING, AppState.PAUSED, AppState.PROCESSING):
            return
        session_id = uuid.uuid4().hex[:12]
        self._session_id = session_id
        session_dir = get_session_audio_dir(session_id)

        # Audio is sacred: start capturing immediately. The API key is only
        # needed to *transcribe*, so we don't block recording on it — a missing
        # key surfaces when we stop, with the audio already safe on disk.
        self._capture = AudioCapture(
            session_dir,
            sample_rate=self.settings.audio.sample_rate,
            channels=self.settings.audio.channels,
            input_device=self.settings.audio.input_device,
            max_duration=self.settings.audio.max_duration,
            level_callback=self.levelChanged.emit,
        )

        def transcribe_chunk(path: str) -> str:
            # Bound lazily so the client only exists once we actually transcribe.
            assert self._client is not None
            return make_transcribe_chunk(self._client, self.settings, apply_vad=True)(path)

        self._pipeline = Pipeline(session_id, self._capture, transcribe_chunk, self.bus)

        if not self._pipeline.start():
            msg = self._capture.error or "failed to start recording"
            self.errorOccurred.emit(msg, "capture")
            self._set_state(AppState.ERROR)
            return
        self._set_state(AppState.RECORDING)

    def _do_pause(self) -> None:
        if self.state is AppState.RECORDING and self._pipeline is not None:
            self._pipeline.pause()
            self._set_state(AppState.PAUSED)

    def _do_resume(self) -> None:
        if self.state is AppState.PAUSED and self._pipeline is not None:
            self._pipeline.resume()
            self._set_state(AppState.RECORDING)

    def _do_stop(self) -> None:
        if self._pipeline is None or self.state not in (AppState.RECORDING, AppState.PAUSED):
            return
        self._pipeline.stop()
        # Now that recording is over, we need the API client to transcribe. If
        # there's no key the audio is still safe on disk for a later retry.
        if self._build_client() is None:
            return
        self._set_state(AppState.PROCESSING)
        pipeline = self._pipeline
        self._pool.submit(self._run_transcription, pipeline)

    # ── worker thread ───────────────────────────────────────────────────

    def _run_transcription(self, pipeline: Pipeline) -> None:
        try:
            pipeline.transcribe()
        except Exception:  # noqa: BLE001 — surfaced via the bus already; guard the thread
            logger.exception("transcription worker crashed")

    def _build_client(self) -> ApiClient | None:
        """Build (and store) the API client used to transcribe. None on failure."""
        if self._client is not None:
            return self._client
        api_key = self.settings.transcription.api_key
        if not api_key:
            self.errorOccurred.emit("API key is required to transcribe", "auth")
            self._set_state(AppState.ERROR)
            return None
        try:
            self._client = ApiClient(api_key)
        except Exception as exc:  # noqa: BLE001
            self.errorOccurred.emit(str(exc), "auth")
            self._set_state(AppState.ERROR)
            return None
        return self._client

    # ── bus → Qt (may run on the worker thread; signals queue to main) ──

    def _on_progress(self, e: events.TranscriptionProgress) -> None:
        self.transcriptionProgress.emit(e.text, e.done, e.total)

    def _on_done(self, e: events.TranscriptionDone) -> None:
        self.transcriptionDone.emit(e.text)
        # Move PROCESSING → SUCCESS on the main thread via the queued signal.
        self.stateChanged.emit(AppState.SUCCESS)
        self._sm.state = AppState.SUCCESS
        self._cleanup_client()

    def _on_error(self, e: events.ErrorOccurred) -> None:
        # "partial" is a soft warning emitted alongside a (partial) result; keep
        # the success path and just surface the message.
        self.errorOccurred.emit(e.message, e.code or "error")
        if e.code != "partial":
            self.stateChanged.emit(AppState.ERROR)
            self._sm.state = AppState.ERROR
            self._cleanup_client()

    def _cleanup_client(self) -> None:
        client = self._client
        if client is not None:
            try:
                client.close()
            except Exception:  # noqa: BLE001
                pass
            self._client = None

    # ── teardown ────────────────────────────────────────────────────────

    def reset_idle(self) -> None:
        if self.state in (AppState.SUCCESS, AppState.ERROR):
            self._set_state(AppState.IDLE)

    def dispose(self) -> None:
        if self._capture is not None and self._capture.is_running:
            try:
                self._capture.stop()
            except Exception:  # noqa: BLE001
                pass
        self._cleanup_client()
        self._pool.shutdown(wait=False, cancel_futures=True)
