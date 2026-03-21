# User Interface

## What It Does
Provides the visual layer of the Dicto desktop app: a main window for transcription history and settings, a floating overlay for recording feedback, a system tray icon for background access, and a splash screen shown at startup.

## Main Files
- `src/ui/main_window.py` - Main application window with transcription display, record/stop controls, settings tab, and text transformation UI
- `src/ui/main_window_styles.py` - Shared style constants (colors, fonts, stylesheets) used across all UI components
- `src/ui/overlay.py` - Draggable floating overlay that shows recording/processing/success/error states with waveform animation
- `src/ui/tray.py` - System tray icon with context menu (open window, settings, quit) and notification support
- `src/ui/splash.py` - Frameless splash window displayed while the app loads
- `src/utils/icons.py` - Resolves icon file paths, supporting both development and PyInstaller-bundled modes

## Flow
1. On startup, `SplashWindow` is shown while components initialize, then replaced by `MainWindow`
2. During recording, the `OverlayWindow` appears with a pulsing dot and waveform animation; it shows processing and success/error states afterward
3. `TrayManager` keeps a system tray icon updated with current status and provides quick access to the window, settings, and quit
