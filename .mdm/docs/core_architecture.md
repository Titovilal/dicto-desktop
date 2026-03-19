# Core Architecture

## What It Does
Orchestrates the full voice-to-text pipeline: listens for a global hotkey, records audio, sends it to the Dicto API for transcription, and copies the result to the clipboard. A central controller coordinates services and UI via Qt signals.

## Main Files
- `src/main.py` - Application entry point; creates all components, wires signals, runs the Qt event loop
- `src/controller.py` - State machine (idle/recording/processing/success/error) that connects hotkey, recorder, transcriber, and clipboard
- `src/config/settings.py` - Loads `config.yaml` with env-var overrides; exposes typed properties for all settings
- `src/utils/logger.py` - Configures application-wide logging to stdout
- `config.yaml` / `config.yaml.example` - User configuration (hotkey, language, API key, behavior flags)

## Flow
1. `DictoApp` initializes Qt, loads settings, creates Controller, UI components, and connects all signals
2. Controller starts the hotkey listener; on hotkey press it records audio, on release it transcribes via the API
3. Transcription result is copied to clipboard, shown in the main window, and optionally auto-pasted
