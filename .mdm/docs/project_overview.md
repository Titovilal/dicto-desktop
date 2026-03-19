# Project Overview

## What It Does
Dicto Desktop is a voice-to-text desktop app for Windows. Users hold a hotkey to record speech, which is transcribed via the Dicto API and automatically copied to the clipboard. It also supports AI-powered text reformatting (email, notes, social post).

## Main Files
- `src/main.py` - Entry point; bootstraps the Qt application and wires all components
- `src/controller.py` - Central state machine coordinating recording, transcription, and UI
- `src/config/settings.py` - Configuration from `config.yaml` + environment variables
- `src/services/` - Backend services: audio recorder, transcriber, hotkey listener, clipboard
- `src/ui/` - PySide6 UI: main window, floating overlay, system tray, styles
- `src/utils/` - Logging setup and icon path resolution
- `assets/` - App icons and custom fonts
- `pyproject.toml` / `requirements.txt` - Python dependencies
- `.github/workflows/build.yml` - CI build pipeline

## Flow
1. App starts, loads config, shows splash, then the main window and system tray
2. User holds the configured hotkey (default Ctrl+Shift+Space) to record audio
3. On release, audio is sent to the Dicto API, transcribed, and copied to clipboard
4. User can view, copy, or reformat the transcription in the main window

## Documentation available in `.mdm/docs/`
- **`core_architecture.md`** — Entry point, controller, settings, and config
- **`services.md`** — Audio recording, transcription API, hotkey listener, clipboard
- **`ui.md`** — Main window, overlay, tray, styles, and visual feedback
