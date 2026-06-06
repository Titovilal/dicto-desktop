# Services

## What It Does
The services layer handles all external communication: it sends audio to the Dicto backend API for transcription, applies AI-powered text transforms via the same API, and exposes the results back to the application through the event bus. It sits between the core domain and the outside world, keeping network concerns out of the UI and state machine.

## Main Files
- `src/dicto/services/api/client.py` - `ApiClient`: authenticated httpx wrapper that retries *retryable* failures with exponential backoff and normalises HTTP/transport errors into typed exceptions
- `src/dicto/services/api/errors.py` - Typed errors (`AuthError`, `RateLimitError`, `QuotaExceededError`, `NetworkError`, `ServerError`, `AudioTooLong/ShortError`) each carrying a machine `code` and a `retryable` flag the pipeline keys on
- `src/dicto/services/api/transcribe.py` - `transcribe_file()`: POSTs one chunk to `/api/v1/transcribe`, with local size guards, and returns its text
- `src/dicto/services/api/factory.py` - `make_transcribe_chunk()`: builds the `chunk_path -> text` callable the pipeline consumes (optionally VAD-trimming the chunk first)
- `src/dicto/services/api/routes.py` - Endpoint URLs, base host overridable via env var
- `src/dicto/services/clipboard.py` - `Clipboard`: write/read text with a lazily-resolved backend (win32 → Qt → headless no-op). The fallback delivery path and the mechanism injection uses under the hood
- `src/dicto/services/injector.py` - `Injector`: drop a transcript at the focused app's cursor via clipboard + Ctrl+V, optional auto-enter; `available()` reports whether real injection is possible (used by `route_result`). pynput is lazy/headless-safe
- `src/dicto/services/api/mocks.py` - `MockStore`: deterministic in-memory stand-in for the user's backend (transcripts + dictionary terms), with sequential ids and an injectable clock; thread-safe. `get/set/reset_mock_store` manage the process-wide instance. The user swaps it for real httpx calls behind the same service classes (Phase 4)
- `src/dicto/services/api/library.py` - `LibraryService`: CRUD + search over transcripts (mocked). `query_transcripts` is the pure filter/sort (text over body/title/tags, tag filter, newest/oldest/title sort) the UI and tests share
- `src/dicto/services/api/dictionary.py` - `DictionaryService`: CRUD for the user's terms/acronyms/names (mocked); feeds `core/dictionary.build_bias_prompt`
- `src/dicto/services/api/routes.py` - endpoint URLs, including `/library`, `/library/{id}`, `/dictionary`, `/dictionary/{id}` (the contract the user's backend implements)
- `src/dicto/core/pipeline.py` - `Pipeline`: orchestrates per-chunk retryable jobs over the transcribe callable; emits progress/results on the bus
- `src/dicto/core/events.py` - Result signals: `TranscriptionProgress`, `TranscriptionDone`, `ErrorOccurred`
- `src/dicto/config/settings.py` - `TranscriptionSettings` and `TransformSettings` (API key, language, model)
- `src/dicto/transform/__init__.py` - Transform service (placeholder; AI presets land in Phase 5)

## Flow
1. `Pipeline` calls the transcribe callable (built by `factory.make_transcribe_chunk`) once per on-disk chunk. The callable optionally VAD-trims the chunk, then `transcribe_file` POSTs it to `/api/v1/transcribe` through `ApiClient`.
2. `ApiClient` retries retryable failures (network, 429, 5xx) with backoff and raises a typed error otherwise; the pipeline retries a failed chunk from its file on disk, so audio is never lost.
3. As chunks complete, `TranscriptionProgress` (with partial text) and finally `TranscriptionDone` are published on the bus; any permanently-failed chunks surface an `ErrorOccurred(code="partial")`.
4. **Delivery (Phase 3):** on `TranscriptionDone`, `app.py` cleans the text (`core/cleanup`, when `behavior.cleanup_enabled`), asks `core/result_router.route_result` what to do (passing `Injector.available()` as the capability), and then either injects at the cursor (`Injector`, optional auto-enter) or copies to the clipboard (`Clipboard`). Injection always stages the text on the clipboard first, so a failed paste falls back cleanly with nothing lost.
5. **Library + dictionary (Phase 4):** before delivery, `app.py` also saves every cleaned transcript via `LibraryService.create` (mocked `MockStore`), so dictation is never lost; the main window refreshes to show it. The user dictionary biases transcription: at recording start the orchestrator reads `DictionaryService.list`, turns it into a prompt with `core/dictionary.build_bias_prompt`, and passes it to `make_transcribe_chunk(prompt=...)`.

---

**Note:** Transform (AI presets) and the account endpoints land in later phases (5–6). The library/dictionary calls are mocked in-process for now (`MockStore`) behind the real service signatures. The original reference implementation lives in `Antiguo/src/services/transcriber.py`.

See `core.md` for the state machine and event bus, `audio.md` for how chunks are captured, and `config.md` for API key and model settings.
