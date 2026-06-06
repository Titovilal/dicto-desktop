# Services

## What It Does
The services layer handles all external communication: it sends audio to the Dicto backend API for transcription, applies AI-powered text transforms via the same API, and exposes the results back to the application through the event bus. It sits between the core domain and the outside world, keeping network concerns out of the UI and state machine.

## Main Files
- `src/dicto/services/api/client.py` - `ApiClient`: authenticated httpx wrapper that retries *retryable* failures with exponential backoff and normalises HTTP/transport errors into typed exceptions
- `src/dicto/services/api/errors.py` - Typed errors (`AuthError`, `RateLimitError`, `QuotaExceededError`, `NetworkError`, `ServerError`, `AudioTooLong/ShortError`) each carrying a machine `code` and a `retryable` flag the pipeline keys on
- `src/dicto/services/api/transcribe.py` - `transcribe_file()`: POSTs one chunk to `/api/v1/transcribe`, with local size guards, and returns its text
- `src/dicto/services/api/factory.py` - `make_transcribe_chunk()`: builds the `chunk_path -> text` callable the pipeline consumes (optionally VAD-trimming the chunk first)
- `src/dicto/services/api/routes.py` - Endpoint URLs, base host overridable via env var
- `src/dicto/core/pipeline.py` - `Pipeline`: orchestrates per-chunk retryable jobs over the transcribe callable; emits progress/results on the bus
- `src/dicto/core/events.py` - Result signals: `TranscriptionProgress`, `TranscriptionDone`, `ErrorOccurred`
- `src/dicto/config/settings.py` - `TranscriptionSettings` and `TransformSettings` (API key, language, model)
- `src/dicto/transform/__init__.py` - Transform service (placeholder; AI presets land in Phase 5)

## Flow
1. `Pipeline` calls the transcribe callable (built by `factory.make_transcribe_chunk`) once per on-disk chunk. The callable optionally VAD-trims the chunk, then `transcribe_file` POSTs it to `/api/v1/transcribe` through `ApiClient`.
2. `ApiClient` retries retryable failures (network, 429, 5xx) with backoff and raises a typed error otherwise; the pipeline retries a failed chunk from its file on disk, so audio is never lost.
3. As chunks complete, `TranscriptionProgress` (with partial text) and finally `TranscriptionDone` are published on the bus; any permanently-failed chunks surface an `ErrorOccurred(code="partial")`.

---

**Note:** Transform (AI presets) and the other mock CRUD endpoints land in later phases (5–6). The original reference implementation lives in `Antiguo/src/services/transcriber.py`.

See `core.md` for the state machine and event bus, `audio.md` for how chunks are captured, and `config.md` for API key and model settings.
