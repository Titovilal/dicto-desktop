# Core Architecture

## What It Does
Defines the application entry point, central state machine, and configuration system. These files bootstrap the app, coordinate all services and UI components through a signal-based architecture, and manage user settings.

## Main Files
- `src/main.py` - Entry point; creates the Qt app, initializes all components, and wires signals between controller, UI, and tray (`DictoApp` class)
- `src/controller.py` - Central orchestrator (`Controller`); owns the state machine (idle → recording → processing → success/error), manages hotkey callbacks, and delegates work to services via a background thread pool
- `src/config/settings.py` - Loads and merges configuration from `config.yaml` and environment variables into a `Settings` object with typed properties
- `config.yaml` - User-editable configuration file (API key, hotkeys, overlay, audio, behavior, language)
- `src/utils/logger.py` - Logging setup used across the application
- `src/utils/icons.py` - Resolves the application icon path for taskbar and windows
- `src/i18n/translations.py` - Multi-language UI string translations

## Flow
1. `main()` sets up logging, creates `DictoApp` which initializes the Qt application, loads settings, shows a splash screen, and creates the controller, overlay, tray, and main window
2. `DictoApp._connect_signals()` wires Qt signals between the controller and all UI components (overlay, tray, main window, waveform widgets) so state changes propagate automatically
3. `Controller.start()` activates hotkey listeners and sets the app to idle; from there the state machine drives transitions: hotkey press → recording → release → processing → success/error → idle
4. On shutdown, `DictoApp.quit()` cancels active operations, stops the controller (hotkeys, thread pool, recorder, transcriber), and closes all windows

---

**Best practices:** keep it short, focus on the big picture, use plain language. Avoid code snippets, implementation details, and complex jargon. See [services.md](services.md) for details on individual services, and [ui.md](ui.md) for UI components.
