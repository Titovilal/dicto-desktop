# Project Overview

## What It Does
Dicto Desktop is a minimalist Windows desktop app for voice-to-text transcription. Users hold a global hotkey to record speech, and the app automatically transcribes it via the Dicto API and copies the result to the clipboard. It also supports text transformation (reformatting transcribed text with custom instructions).

## Main Files
- `src/main.py` - Application entry point and component wiring
- `src/controller.py` - Central orchestrator managing state and service coordination
- `src/config/settings.py` - Configuration from `config.yaml` and environment variables
- `src/services/` - Audio recording, transcription API, clipboard, and hotkey detection
- `src/ui/` - Main window, floating overlay, system tray, splash screen, and shared styles
- `src/utils/` - Logging and icon utilities

## Flow
1. User holds the global hotkey (default: Ctrl+Shift+Space) to start recording from the microphone
2. On release, the audio is sent to the Dicto API for transcription in a background thread
3. The transcribed text is copied to the clipboard (and optionally auto-pasted into the active window)

### Edit Selection Flow
1. User selects text in any application and holds the edit hotkey (default: Ctrl+Shift+E)
2. On press: the app copies the selected text (simulates Ctrl+C), reads it from clipboard, and starts recording voice instructions from the microphone
3. On release: stops recording, transcribes the voice to get text instructions, sends both the selected text and instructions to `/api/transform`
4. The transformed text is copied to clipboard and optionally auto-pasted back

## Documentation available in `.mdm/docs/`
- **`core_architecture.md`** — Entry point, configuration system, and utility foundations
- **`services.md`** — Audio recording, transcription, clipboard, hotkey detection, and the controller
- **`ui.md`** — Main window, overlay, system tray, and splash screen
