# UI Components

## What It Does
Provides the visual layer of Dicto: a settings/status window, a floating overlay for recording feedback, a system tray icon, a real-time waveform animation, and a startup splash screen. All built with PySide6 using a dark zinc-based theme.

## Main Files
- `src/ui/main_window.py` - Main application window with settings panels, status display, and stacked pages (home, settings, models)
- `src/ui/overlay.py` - Frameless floating overlay showing recording/processing/success state with a draggable card, settings popover, and record/stop button
- `src/ui/tray.py` - System tray icon and context menu (show window, open config, quit)
- `src/ui/waveform.py` - Animated waveform bar widget used by both the main window and the overlay
- `src/ui/splash.py` - Frameless splash window shown during app startup
- `src/ui/icons.py` - SVG icon loader that reads and caches icons from the assets directory
- `src/ui/main_window_styles.py` - Centralized dark-mode color palette (zinc scale), font definitions, and Qt stylesheet helpers
- `src/ui/assets/` - SVG icon files (settings, record, stop, reset, close, models, etc.)
- `src/i18n/translations.py` - UI string translations for multi-language support

## Flow
1. On startup, `SplashWindow` displays while the app initializes; once ready the main window and overlay are created
2. The `MainWindow` lets users configure settings (API key, hotkeys, overlay options, language); the `TrayManager` provides quick access from the system tray
3. During recording the overlay switches to its recording view with a live `WaveformWidget`, then shows processing and success/error states as the controller transitions

---

**Best practices:** keep it short, focus on the big picture, use plain language. Avoid code snippets, implementation details, and complex jargon. See [core_architecture.md](core_architecture.md) for how the controller drives UI state changes, and [services.md](services.md) for the backend services the UI interacts with.
