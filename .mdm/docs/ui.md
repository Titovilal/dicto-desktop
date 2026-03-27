# User Interface

## What It Does
Provides the visual layer of the Dicto desktop app: a main window for transcription history and settings, a floating overlay for recording feedback, a system tray icon for background access, and a splash screen shown at startup.

## Main Files
- `src/ui/main_window.py` - Main application window with transcription display, record/stop/cancel controls, settings panel, models panel, and text transformation UI. The record button is context-sensitive: shows "Record" when idle, "Stop" when recording, and "Cancel" when processing. Emits `cancel_clicked` signal when clicked during processing. Uses builder helpers (`_add_checkbox`, `_add_combo`, `_add_section`, `_add_hotkey_row`), `_save_setting()`, and `_create_scroll_page()` to reduce settings/models page boilerplate. The header has two panel buttons (models and settings) that toggle separate scrollable pages (indices 4 and 3 respectively)
- `src/ui/main_window_styles.py` - Shared style constants (colors, fonts, stylesheets, SVG icons) used across all UI components
- `src/ui/waveform.py` - Unified `WaveformWidget` with configurable bar count, size, gap, color, optional fixed width, and animation `mode` (`"live"` for real-time audio level display driven externally via `set_level()`, `"wave"` for sine flow, `"pulse"` for processing center-outward ripple, `"settle"` for success rise-and-settle). Used by both MainWindow and OverlayWindow
- `src/ui/overlay.py` - Fixed top-right overlay that shows recording/processing/success/error states using three WaveformWidget instances with different modes and colors
- `src/ui/tray.py` - System tray icon with context menu (open window, settings, quit) and notification support
- `src/ui/splash.py` - Frameless splash window displayed while the app loads
- `src/utils/icons.py` - Resolves icon file paths, supporting both development and PyInstaller-bundled modes
- `src/i18n/__init__.py` - Internationalization module: `t(key)` function, `set_language()`/`get_language()` for UI language
- `src/i18n/translations.py` - Translation dictionaries for 5 languages (en, es, de, fr, pt) and `UI_LANGUAGES` map

## Window System

There are 3 windows:

1. **System Tray** (`TrayManager`) - Always present in the system tray. Provides quick access to open the main window, settings, and quit.

2. **Main Window** (`MainWindow`) - The primary window (420x400) showing transcription content, format tabs, settings, record/stop controls, and all header buttons. Uses a 10px border-radius on the central card.

3. **Overlay Window** (`OverlayWindow`) - Fixed to top-right of the screen (not draggable), positioned 50px from the top for clearance. Purely informational with no interactive elements — displays a wide waveform animation on top, then a status row with a dot and label below. Designed as a compact indicator (160x60px) with an opaque dark background. Shows recording/processing/success/error state and hides after success/error.

## Tab Behavior
The transcription area has format tabs: Original, Correo, Notas, Post. On startup and whenever there is no transcription content, all tabs except "Original" (the `raw` format) are disabled via `btn.setEnabled(False)` and styled with `TAB_BUTTON_DISABLED`. When a transcription completes and text is available, `_update_tabs_enabled(True)` re-enables all tabs. When the state resets, they are disabled again.

## Hotkey Configuration
The settings page includes a "Atajos de teclado" (Hotkeys) section with two `HotkeyButton` widgets — one for the recording hotkey and one for the edit-selection hotkey. `HotkeyButton` is a custom `QPushButton` subclass that, when clicked, enters a "listening" mode (displays "Presiona una combinación..."). The user then presses a key combination (modifiers + key) which is captured via `keyPressEvent`, displayed in a readable format (e.g. "Ctrl+Shift+Space"), saved to settings, and propagated via `recording_hotkey_changed` / `edit_hotkey_changed` signals. These signals are wired through `main.py` to `Controller.update_recording_hotkey()` / `update_edit_hotkey()`, which stop the old `HotkeyListener` and start a new one with the updated combination. Pressing Escape while listening cancels and restores the previous hotkey display.

## Panel View Protection
When the user is viewing the settings or models panel, state changes (recording, processing, idle, transcription result) do **not** switch the content stack away from the panel. Instead, they update `_prev_page` so the correct page is shown when the user closes the panel. The status dot, timer, and header indicators still update in real time; the overlay provides recording/processing feedback. All background state (transcription text, format cache, button states) is updated normally so results are ready when the user returns to the transcription view. Opening one panel while the other is open closes the first via `_close_panel()`.

## Settings Page Order
Settings are ordered by importance for new users: API Key (essential to start), Keyboard Shortcuts, Behavior (auto-paste), Edit Selection behavior, Application (always on top + persistent overlay), and UI Language (rarely changed). Model configuration lives in the separate Models panel.

## Models Page
The Models panel (content stack index 4, toggled via the cube icon in the header) groups all model-related settings: transcription model, transcription language, transformation model, and edition model.

## Internationalization (i18n)
All user-visible strings are translated via `src/i18n`. The `t(key)` function returns the translated string for the current UI language. Supported languages: English (en), Spanish (es), German (de), French (fr), Portuguese (pt). The UI language is stored in `config.yaml` as `ui_language` (default: "es") and can be changed in the settings page. Language is set at startup in `main.py` via `set_language()`. When the user changes the language in settings, `_retranslate_ui()` updates most visible labels immediately; some static labels (section headers, tab labels) require an app restart.

## Flow
1. On startup, `SplashWindow` is shown while components initialize, then replaced by `MainWindow`
2. During recording, the `OverlayWindow` appears with a pulsing dot and live waveform driven by real audio levels from the microphone (live mode); it shows processing (pulse mode waveform) and success (settle mode waveform) states afterward
3. `TrayManager` keeps a system tray icon updated with current status and provides quick access to the window, settings, and quit
