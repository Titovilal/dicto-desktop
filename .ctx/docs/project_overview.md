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
- `src/dicto/core/cleanup.py` - `clean_dictation`: pure dictation tidying (fillers, whitespace, capitalisation)
- `src/dicto/core/result_router.py` - `route_result`: pure cursor/clipboard/library delivery decision
- `src/dicto/core/export.py` - pure txt/Markdown export of a transcript
- `src/dicto/core/dictionary.py` - `build_bias_prompt`: pure conversion of the user's dictionary terms into a biasing prompt for the STT model
- `src/dicto/services/api/mocks.py` - `MockStore`: deterministic in-memory stand-in for the user's backend (library + dictionary)
- `src/dicto/services/api/library.py` - `LibraryService`: CRUD + search over transcripts (mocked); `query_transcripts` is the pure filter/sort
- `src/dicto/services/api/dictionary.py` - `DictionaryService`: CRUD for the user's dictionary terms (mocked)
- `src/dicto/ui/main/library_view.py` - `LibraryView`: searchable/sortable/tag-filterable transcript list
- `src/dicto/ui/main/detail_view.py` - `DetailView`: view/edit a transcript, copy, export
- `src/dicto/services/clipboard.py` - `Clipboard`: text clipboard with win32/Qt/no-op backends
- `src/dicto/services/injector.py` - `Injector`: paste a transcript at the cursor (clipboard + Ctrl+V, optional auto-enter)
- `src/dicto/config/settings.py` - Pydantic settings model, loaded from `%APPDATA%\dicto\config.yaml`
- `src/dicto/config/defaults.py` - All default values (language, hotkey, audio, models)
- `src/dicto/i18n/__init__.py` - Translations via `t("key")`, hot-switchable language
- `src/dicto/i18n/locales/` - JSON locale files (`en.json`, `es.json`)
- `src/dicto/ui/theme/manager.py` - ThemeManager: builds Qt stylesheet from design tokens, follows OS
- `src/dicto/ui/theme/tokens.py` - Design token enum (BG, TEXT, ACCENT, etc.)
- `src/dicto/ui/theme/palettes.py` - Light and dark colour palettes mapped to tokens
- `src/dicto/ui/tray.py` - System tray icon and context menu (Open / Settings / Quit)
- `src/dicto/ui/main/window.py` - Main window shell: rail + library + detail split, opens the settings/dictionary modals
- `src/dicto/ui/main/settings_modal.py` - `SettingsModal`: frameless, translucent in-window modal (recording + appearance panels) rendered on a rounded `#modalCard`
- `src/dicto/ui/main/dictionary_modal.py` - `DictionaryModal`: frameless, translucent modal to manage the user's bias dictionary terms
- `scripts/screenshot.py` - Dev aid: boots the app and saves PNGs of each view to `screenshots/` (gitignored). Lets an agent *see* the UI to iterate; `--theme dark` for the dark palette
- `src/dicto/ui/icons.py` - Icon helpers for status colours and app icon
- `src/dicto/utils/logger.py` - Logging setup
- `src/dicto/utils/platform.py` - OS-specific path helpers (`%APPDATA%`)

## Flow
1. User launches the app (`dicto` CLI or `python -m dicto`); `DictoApp` loads settings, applies theme and language, shows the system tray icon and main window, and starts the global hotkey listener.
2. User presses the global hotkey (default: Ctrl+Shift+Space — hold or toggle). `RecordingOrchestrator` starts an `AudioCapture` + `Pipeline`, the overlay appears showing a live waveform and elapsed timer, and the tray icon turns red. The recording can be paused/resumed without splitting the file.
3. When recording stops, the orchestrator finalises the chunks and runs transcription on a worker thread (biased by the user's dictionary via `core/dictionary`); per-chunk progress and the final text are published on the event bus and bridged to Qt. On the final text, `app.py` cleans the dictation (`core/cleanup`), saves it to the library (`services/api/library`, mocked) so nothing is lost, then the result router (`core/result_router`) decides delivery: inject at the cursor (`services/injector`, optional auto-enter) or copy to the clipboard (`services/clipboard`) as the fallback. The saved transcript appears in the main window's library, where it can be searched, edited, copied and exported.

## Development

- **Seeing the UI** — run `PYTHONPATH=src .venv/Scripts/python.exe scripts/screenshot.py`
  to render the main window, overlay, settings modal and dictionary modal to
  `screenshots/*.png`, then read those PNGs to inspect or iterate on the visuals.
  Add `--theme dark` for the dark palette. The modals are frameless + translucent,
  so the script renders each widget with `widget.grab()` (screen-region capture is
  unreliable for frameless windows on Windows); the 1px translucent margin around a
  modal shows as a flat colour in the PNG but is transparent in the running app.

## Documentation available in `.ctx/docs/`
- **`core.md`** — state machine, event bus, and domain models
- **`config.md`** — settings model, defaults, and persistence
- **`ui.md`** — theme system, tray, main window, and i18n
- **`audio.md`** — audio capture, VAD, and chunk management
- **`services.md`** — API client, transcription service, and transform service
