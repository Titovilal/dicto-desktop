# Core Architecture

## What It Does
Defines the application entry point, configuration system, and utility foundations that all other components depend on.

## Main Files
- `src/main.py` - Entry point; creates the `DictoApp` class which initializes Qt, loads settings, wires up all components via signals, and runs the event loop
- `src/config/settings.py` - Loads `config.yaml` (merged with defaults), applies environment variable overrides, and exposes typed properties via `_config_property()` / `_flat_config_property()` descriptor factories for all settings
- `config.yaml` - User-editable configuration file for hotkey, edit_hotkey, overlay, transcription, audio, behavior, and edit settings
- `src/utils/logger.py` - Configures application-wide logging to stdout
- `pyproject.toml` - Project metadata and build configuration
- `Makefile` - Development commands (run, build, etc.)
- `.env` - Environment variables (e.g., `DICTO_API_KEY`)

## Flow
1. `main()` sets up logging, loads `.env`, and creates `DictoApp`
2. `DictoApp.__init__` creates the Qt application, loads fonts, shows splash, loads `Settings` from `config.yaml`, initializes all components (Controller, TrayManager, OverlayWindow, MainWindow), and connects their signals
3. `DictoApp.run()` starts the Controller (which starts the hotkey listener) and enters the Qt event loop
