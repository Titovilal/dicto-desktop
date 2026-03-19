# User Interface

## What It Does
Provides a frameless desktop window, a floating overlay, and a system tray icon — all built with PySide6 (Qt). The UI shows recording state, transcription results, format tabs (email/notes/tweet), and a settings panel.

## Main Files
- `src/ui/main_window.py` - Frameless main window with idle/recording/done/settings pages, format tabs, waveform animation, and drag support
- `src/ui/main_window_styles.py` - All style constants, colors, and inline SVG icons used across the UI
- `src/ui/overlay.py` - Draggable always-on-top overlay showing recording/processing/success/error states with a record/stop button
- `src/ui/tray.py` - System tray icon with context menu (open, settings, quit) and notification helpers
- `src/ui/splash.py` - Brief splash screen shown during startup
- `src/utils/icons.py` - Resolves the app icon path for both dev and PyInstaller builds
- `assets/icons/` - App icons (ico, png, svg) used by the tray, window, and installer
- `assets/fonts/` - Custom font (JetBrains Mono) loaded by the UI

## Flow
1. Main window starts on the idle page; user clicks "Grabar" or uses the hotkey to start recording
2. During recording the window shows a waveform animation and elapsed timer; the overlay mirrors the state
3. After transcription, the done page displays the text with format tabs for AI-powered reformatting (email, notes, tweet)
