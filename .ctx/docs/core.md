# Core

## What It Does
The core layer holds the pure domain logic for Dicto: a guarded state machine tracking whether the app is idle, recording, or processing; a Qt-free event bus that connects domain actions to the UI; and a set of plain dataclasses representing the app's domain objects (jobs, transcripts, accounts). Nothing here imports Qt, making the whole layer unit-testable in isolation.

## Main Files
- `src/dicto/core/state.py` - `AppState` enum and `StateMachine` with enforced transition rules; also `RecordingSession` tracking a single recording's on-disk chunks and pause/resume lifecycle
- `src/dicto/core/events.py` - `EventBus` (synchronous pub/sub keyed by event type) and all typed event dataclasses (recording lifecycle, transcription progress, errors)
- `src/dicto/core/models.py` - Domain dataclasses: `Job`, `Transcript`, `TransformResult`, `DictTerm`, `Plan`, `Account`
- `src/dicto/core/pipeline.py` - `Pipeline`: pure orchestrator of capture→persist→transcribe; one retryable `Job` per on-disk chunk, with progress/partial-result events. Effects (capture, network) are injected, so the reliability story is unit-testable. See `audio.md`/`services.md`.
- `src/dicto/core/chunking.py`, `src/dicto/core/vad.py` - chunk-rotation policy and silence trimming (detailed in `audio.md`)

## Flow
1. The app layer creates a `StateMachine` and an `EventBus` at startup, then subscribes UI handlers to relevant event types.
2. As the user records, the domain transitions the state machine (`IDLE → RECORDING → PROCESSING → SUCCESS/ERROR`) and publishes typed events (`RecordingStarted`, `RecordingProgress`, `TranscriptionDone`, etc.) onto the bus.
3. The app layer receives these events and bridges them to Qt signals, driving tray icon updates, overlays, and clipboard writes. If a transition is illegal, `InvalidTransition` is raised immediately, surfacing bugs rather than silently corrupting state.

---

See [`services.md`](services.md) for how transcription results are produced, and [`ui.md`](ui.md) for how events are consumed by the interface.
