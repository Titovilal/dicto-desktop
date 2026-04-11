# Project Overview

## What It Does
Dicto is a minimalist desktop app (Windows, Linux, macOS) that transcribes speech to text via a global hotkey. Users press-and-hold a hotkey to record audio, release to send it to a transcription API, and the result is automatically pasted into the active application. It also supports an "edit" flow that transforms selected text using voice instructions.

## Main Files
- `src/main.py` - Application entry point; creates the Qt app, wires all components together (`DictoApp` class)
- `src/controller.py` - Central orchestrator (`Controller`); manages state machine (idle → recording → processing → success/error) and coordinates services
- `src/config/settings.py` - Loads configuration from `config.yaml` and environment variables
- `src/services/recorder.py` - Records audio from the microphone using `sounddevice`
- `src/services/transcriber.py` - Sends audio to the Dicto transcription API via `httpx`
- `src/services/hotkey.py` - Global hotkey listener using `pynput`
- `src/services/hotkey_wayland.py` - Wayland-specific hotkey support via XDG GlobalShortcuts portal
- `src/services/clipboard.py` - Clipboard read/write (platform-specific: `pywin32` on Windows, `pyperclip` elsewhere)
- `src/services/keyboard_actions.py` - Simulates keyboard actions (paste, select-all, copy)
- `src/ui/main_window.py` - Main settings/status window (PySide6)
- `src/ui/overlay.py` - Floating overlay showing recording/processing/success state
- `src/ui/tray.py` - System tray icon and menu
- `src/ui/waveform.py` - Real-time audio waveform widget
- `src/i18n/translations.py` - UI translations (multi-language support)
- `config.yaml` - User configuration (API key, hotkeys, overlay settings, language)

## Flow
1. User presses global hotkey → `HotkeyListener` notifies `Controller` → audio recording starts
2. User releases hotkey → recording stops → audio file sent to transcription API
3. Transcribed text is copied to clipboard and pasted into the active application; overlay shows success

## Documentation available in `.ctx/docs/`
- **`core_architecture.md`** — Entry point, controller state machine, settings, and application lifecycle
- **`services.md`** — Audio recording, transcription API, hotkey listeners, clipboard, and keyboard services
- **`ui.md`** — Main window, overlay, tray, waveform widget, splash screen, icons, and styles
- **`testing_strategy.md`** — Test structure, fixtures, and how to run tests

---

**Best practices:** keep it short, focus on the big picture, use plain language. Avoid code snippets, implementation details, and complex jargon.
