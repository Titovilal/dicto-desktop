# Project Overview

## What It Does
Dicto is a Windows desktop app that lets users record voice via a global hotkey, transcribes it using a speech-to-text API, and can apply AI transforms to the resulting text. It targets knowledge workers who want fast voice-to-clipboard dictation without leaving their current application.

## Main Files
- `src/dicto/app.py` - Entry point: boots Qt, wires UI and domain layers together
- `src/dicto/__main__.py` - `python -m dicto` entry point
- `src/dicto/orchestrator.py` - `RecordingOrchestrator`: app-layer glue between hotkey/overlay input, the pure pipeline, and the UI; runs transcription on a worker thread and bridges the domain event bus to Qt signals
- `src/dicto/services/hotkey.py` - Global hotkey: a pure `HotkeyMatcher` (hold/toggle, headless-testable) wrapped by a pynput-backed `HotkeyListener`
- `src/dicto/audio/monitor.py` - `AudioMonitor`: live mic level for the test panel, writes nothing to disk
- `src/dicto/ui/overlay/overlay.py` - `Overlay`: ephemeral draggable status card (waveform + timer + pause/stop), remembers its position
- `src/dicto/core/state.py` - Pure state machine (IDLE → RECORDING → PROCESSING → SUCCESS/ERROR)
- `src/dicto/core/events.py` - Qt-free typed event bus connecting core to UI
- `src/dicto/core/models.py` - Domain dataclasses: Job, Transcript, TransformResult, Account
- `src/dicto/config/settings.py` - Pydantic settings model, loaded from `%APPDATA%\dicto\config.yaml`
- `src/dicto/config/defaults.py` - All default values (language, hotkey, audio, models)
- `src/dicto/i18n/__init__.py` - Translations via `t("key")`, hot-switchable language
- `src/dicto/i18n/locales/` - JSON locale files (`en.json`, `es.json`)
- `src/dicto/ui/theme/manager.py` - ThemeManager: builds Qt stylesheet from design tokens, follows OS
- `src/dicto/ui/theme/tokens.py` - Design token enum (BG, TEXT, ACCENT, etc.)
- `src/dicto/ui/theme/palettes.py` - Light and dark colour palettes mapped to tokens
- `src/dicto/ui/tray.py` - System tray icon and context menu (Open / Settings / Quit)
- `src/dicto/ui/main/window.py` - Main window shell (currently a placeholder, expands in later phases)
- `src/dicto/ui/icons.py` - Icon helpers for status colours and app icon
- `src/dicto/utils/logger.py` - Logging setup
- `src/dicto/utils/platform.py` - OS-specific path helpers (`%APPDATA%`)

## Flow
1. User launches the app (`dicto` CLI or `python -m dicto`); `DictoApp` loads settings, applies theme and language, shows the system tray icon and main window, and starts the global hotkey listener.
2. User presses the global hotkey (default: Ctrl+Shift+Space — hold or toggle). `RecordingOrchestrator` starts an `AudioCapture` + `Pipeline`, the overlay appears showing a live waveform and elapsed timer, and the tray icon turns red. The recording can be paused/resumed without splitting the file.
3. When recording stops, the orchestrator finalises the chunks and runs transcription on a worker thread; per-chunk progress and the final text are published on the event bus, bridged to Qt, and (Phase 2) copied to the clipboard. Phase 3 adds the result router (cursor/clipboard/library) and cleanup.

## Documentation available in `.ctx/docs/`
- **`core.md`** — state machine, event bus, and domain models
- **`config.md`** — settings model, defaults, and persistence
- **`ui.md`** — theme system, tray, main window, and i18n
- **`audio.md`** — audio capture, VAD, and chunk management
- **`services.md`** — API client, transcription service, and transform service
