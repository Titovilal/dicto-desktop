# Dicto - Project Overview

## What It Does
Desktop application that transcribes voice to text. Use a global hotkey (press and hold to record, release to transcribe) or the main window controls. The result is automatically copied to clipboard.

## Main Files

### Core
- `src/main.py` - Application entry point, initializes Qt app and connects all components
- `src/controller.py` - Main orchestrator that manages state and coordinates services

### Services
- `src/services/hotkey.py` - Global hotkey listener (press/release detection)
- `src/services/recorder.py` - Audio recording from microphone
- `src/services/transcriber.py` - Speech-to-text via OpenAI/Groq API
- `src/services/clipboard.py` - Copies transcribed text to system clipboard

### UI
- `src/ui/splash.py` - Splash window shown during app startup
- `src/ui/main_window.py` - Main window with record/copy buttons and settings tab
- `src/ui/overlay.py` - Visual feedback overlay (recording, processing, success/error)
- `src/ui/tray.py` - System tray icon and menu

### Config & Utils
- `src/config/settings.py` - Configuration management (loads config.yaml, applies env overrides)
- `src/utils/logger.py` - Logging setup for the application

### Project Files
- `config.yaml` - User configuration (hotkey, overlay, transcription, audio settings)
- `config.yaml.example` - Example config template
- `pyproject.toml` - Project metadata and dependencies
- `Makefile` - Build and dev commands (run, build, release, lint, format)
- `.github/workflows/build.yml` - CI/CD pipeline (build Windows/Linux, create releases)

## Flow
1. App starts -> splash window appears centered on screen while components load
2. Components initialized -> splash closes, main window and tray appear
3. User starts recording via hotkey (press and hold) or main window Record button
4. Audio is captured from microphone -> overlay shows "Recording"
5. User stops recording (release hotkey or click Stop) -> audio is sent to transcription API
6. API returns transcribed text -> text is copied to clipboard -> overlay shows success
7. User can paste the transcribed text anywhere (or use Copy button in main window)

## Architecture
```
DictoApp (main.py)
    |
    +-- SplashWindow (splash.py) [shown during startup]
    |
    +-- Controller (controller.py)
    |       |
    |       +-- HotkeyListener (hotkey.py)
    |       +-- AudioRecorder (recorder.py)
    |       +-- Transcriber (transcriber.py)
    |       +-- ClipboardManager (clipboard.py)
    |
    +-- MainWindow (main_window.py)
    +-- TrayManager (tray.py)
    +-- OverlayWindow (overlay.py)
```

## States
- **IDLE** - Waiting for hotkey press or Record button click
- **RECORDING** - Capturing audio from microphone
- **PROCESSING** - Sending audio to transcription API
- **SUCCESS** - Transcription completed, text in clipboard
- **ERROR** - Something went wrong

## Configuration
Settings loaded from `config.yaml` with environment variable overrides. Behavior settings can also be changed via main window Settings tab or tray menu.
- **hotkey** - Modifier keys and trigger key
- **overlay** - Position, size, opacity
- **transcription** - Provider (openai/groq), API key, language
- **audio** - Sample rate, max duration, channels
- **behavior** - Auto-paste, auto-enter, show success notifications

Environment variables: `OPENAI_API_KEY`, `GROQ_API_KEY`

## CI/CD
GitHub Actions workflow (`.github/workflows/build.yml`):
1. Builds executables for Windows and Linux using PyInstaller
2. Creates GitHub releases with version from `pyproject.toml`
3. Triggered by tag push or manual workflow dispatch

## Technologies
- **PySide6** - Qt bindings for UI (tray icon, overlay window)
- **pynput** - Global hotkey detection
- **sounddevice/soundfile** - Audio recording
- **httpx** - HTTP client for API calls
- **pyperclip** - Clipboard management
- **PyYAML** - Configuration file parsing
- **PyInstaller** - Executable packaging
