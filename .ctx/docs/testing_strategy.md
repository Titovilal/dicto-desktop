# Testing Strategy

## What It Does
The test suite validates Dicto's core flows — recording, transcription, editing, cancellation — plus individual services and UI components. Tests are organized by scope (unit, integration, UI, API) and run with pytest and pytest-qt.

## Main Files
- `tests/conftest.py` - Shared fixtures: temporary config, default settings, custom config factory, sample WAV file
- `tests/unit/test_controller.py` - State machine transitions, cancel logic, hotkey handlers
- `tests/unit/test_settings.py` - Config loading, YAML parsing, env variable overrides, save roundtrip
- `tests/unit/test_transcriber.py` - API client validation, request/response handling, error parsing
- `tests/unit/test_recorder.py` - Audio recorder init, recording state, duration, cleanup
- `tests/unit/test_hotkey.py` - Hotkey string parsing (special keys, modifiers, hold/press modes)
- `tests/unit/test_clipboard.py` - Copy, paste, clear, wait-for-change with timeout
- `tests/unit/test_i18n.py` - Translation retrieval, fallback to English, completeness checks
- `tests/unit/test_platform.py` - Platform-specific behavior (Windows event filter, Wayland detection)
- `tests/integration/test_recording_flow.py` - Full recording → transcription → clipboard flow
- `tests/integration/test_edit_flow.py` - Edit selection flow (copy → record → transform via API)
- `tests/integration/test_cancel_flow.py` - Cancel edge cases during recording and processing
- `tests/integration/test_settings_sync.py` - Settings ↔ Controller hotkey synchronization
- `tests/api/test_api_contracts.py` - Request format and response parsing for all API endpoints
- `tests/ui/test_main_window.py` - Main window widget behavior
- `tests/ui/test_overlay.py` - Overlay state display
- `tests/ui/test_waveform.py` - Waveform widget rendering

## Flow
1. **Unit tests** mock external I/O (filesystem, audio devices, network) and verify individual components in isolation
2. **Integration tests** mock only I/O boundaries (recorder, transcriber, clipboard) while keeping the controller state machine real, then verify full user flows end-to-end
3. **UI tests** use `pytest-qt`'s `qtbot` fixture to create widgets, simulate interactions, and assert signal emissions
4. **API contract tests** verify request format and response parsing without hitting the real API

## How to Run
- All tests: `pytest tests/`
- By category: `pytest tests/unit/`, `pytest tests/integration/`, `pytest tests/ui/`, `pytest tests/api/`
- With coverage: `pytest --cov=src tests/`
- Skip real-API tests: `pytest -m "not api"`

## Key Patterns
- **Shared fixtures** in `conftest.py` provide isolated temporary configs and a minimal valid WAV file
- **qtbot** (from pytest-qt) handles widget lifecycle and signal verification via `waitSignal()`
- **Mocking strategy**: external I/O mocked at boundaries; internal logic runs for real
- **Marker `api`** flags tests that call the real Dicto API, so they can be excluded in CI

---

**Best practices:** keep it short, focus on the big picture, use plain language. Avoid code snippets, implementation details, and complex jargon.
