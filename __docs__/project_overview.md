# Dicto - Project Overview

## What It Does
Desktop application that transcribes voice to text using a global hotkey. Press and hold the hotkey to record, release to transcribe, and the result is automatically copied to clipboard.

## Main Files
- `src/main.py` - Application entry point, initializes Qt app and connects all components
- `src/controller.py` - Main orchestrator that manages state and coordinates services
- `src/config/settings.py` - Configuration management (hotkeys, API keys, audio settings)
- `src/services/hotkey.py` - Global hotkey listener (press/release detection)
- `src/services/recorder.py` - Audio recording from microphone
- `src/services/transcriber.py` - Speech-to-text via OpenAI/Groq API
- `src/services/clipboard.py` - Copies transcribed text to system clipboard
- `src/ui/overlay.py` - Visual feedback overlay (recording, processing, success/error)
- `src/ui/tray.py` - System tray icon and menu

## Flow
1. User presses global hotkey (e.g., Ctrl+Shift+Space) -> hotkey listener triggers recording start
2. Audio is captured from microphone while hotkey is held -> overlay shows "Recording"
3. User releases hotkey -> recording stops, audio is sent to transcription API
4. API returns transcribed text -> text is copied to clipboard -> overlay shows success
5. User can paste the transcribed text anywhere

## Architecture
```
DictoApp (main.py)
    |
    +-- Controller (controller.py)
    |       |
    |       +-- HotkeyListener (hotkey.py)
    |       +-- AudioRecorder (recorder.py)
    |       +-- Transcriber (transcriber.py)
    |       +-- ClipboardManager (clipboard.py)
    |
    +-- TrayManager (tray.py)
    +-- OverlayWindow (overlay.py)
```

## States
- **IDLE** - Waiting for hotkey press
- **RECORDING** - Capturing audio from microphone
- **PROCESSING** - Sending audio to transcription API
- **SUCCESS** - Transcription completed, text in clipboard
- **ERROR** - Something went wrong

## Technologies
- **PySide6** - Qt bindings for UI (tray icon, overlay window)
- **pynput** - Global hotkey detection
- **sounddevice/soundfile** - Audio recording
- **httpx** - HTTP client for API calls
- **pyperclip** - Clipboard management
