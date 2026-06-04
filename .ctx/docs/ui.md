# UI Components

## What It Does
Provides the visual layer of Dicto: a settings/status window, a floating overlay for recording feedback, a system tray icon, a real-time waveform animation, and a startup splash screen. All built with PySide6 using a dark zinc-based theme.

## Main Files
- `src/ui/main_window.py` - Main application window with settings panels, status display, and stacked pages (home, settings, models). Settings includes a "Report error" section with a live log preview (`report_log_view`, refreshed each time the settings page opens), a "Copy logs" button that copies the log buffer to the clipboard, and a "Send report" button that uploads the logs to help diagnose issues. The `MainWindow` class is kept small: it declares the signals, class attributes, and `__init__`, and composes its behavior from three flat mixins — `BuildMixin`, `SettingsMixin`, `StateMixin` (with `QMainWindow` last in the inheritance order).
- `src/ui/main_window_build.py` - `BuildMixin`: all UI construction (header, tabs/action bar, idle/recording/done/settings/models pages, footer, and the small widget-building helpers).
- `src/ui/main_window_settings.py` - `SettingsMixin`: settings/models panels, settings load/save, event filtering, frameless-window dragging, the `_on_*` change handlers, audio test, i18n retranslation, and `closeEvent`.
- `src/ui/main_window_state.py` - `StateMixin`: format/transform handling, animations, copy/cancel actions, and the recording/processing/idle/editing state transitions.
- `src/ui/main_window_common.py` - Shared module-level helpers used by the mixins: the cached SVG-to-`QIcon` builder, the model-to-provider icon lookup, and the `HotkeyButton` widget.
- `src/ui/overlay.py` - Frameless floating overlay showing recording/processing/success state with a draggable card, settings popover, and record/stop button. It honors the configured `overlay_position` and reapplies `_position_window()` right after each `show()`, because Wayland ignores `move()` on a still-hidden window (otherwise the overlay lands in the screen center).
- `src/ui/tray.py` - System tray icon and context menu (show window, open config, quit)
- `src/ui/waveform.py` - Animated waveform bar widget used by both the main window and the overlay
- `src/ui/splash.py` - Frameless splash window shown during app startup
- `src/ui/icons.py` - SVG icon loader that reads and caches icons from the assets directory
- `src/ui/main_window_styles.py` - Centralized dark-mode color palette (zinc scale), font definitions, and Qt stylesheet helpers. The app forces the Qt "Fusion" style at startup (`main.py`) so combo-box dropdown popups honor the dark stylesheet — native platform styles (notably GTK on Linux) ignore stylesheet backgrounds for popup items and would otherwise render them on a light system palette where the light text is unreadable. Combo styles also set explicit `QComboBox QAbstractItemView::item` background/color rules for the same reason.
- `src/ui/assets/` - SVG icon files (settings, record, stop, reset, close, models, openai, googlegemini, qwen, etc.)
- `src/i18n/translations.py` - UI string translations for multi-language support

## Flow
1. On startup, `SplashWindow` displays while the app initializes; once ready the main window and overlay are created
2. The `MainWindow` lets users configure settings (API key, hotkeys, audio input device, overlay options, language) and includes a live microphone test button; a system-audio toggle sits in the footer next to the record button on the home page. The `TrayManager` provides quick access from the system tray. During processing/editing states the footer record button shows a spinning loader icon (animated via `_loader_timer` at 30 ms intervals, rotating the SVG pixmap 12° per tick). Below the content area (above the footer) an action bar contains a format `QComboBox` (Original + user presets) and an always-visible custom-prompt `QLineEdit` + Apply button on its right; selecting a preset or applying a custom prompt emits `transform_requested` with a timestamped `custom_<ms>` format_id. The settings page exposes two hotkey rows backed by separate `Settings` properties: the main record hotkey (`hotkey.modifiers`/`hotkey.key`, default `Ctrl+Shift+Space`) and the edit hotkey (`hotkey.edit_modifiers`/`hotkey.edit_key`, default `Ctrl+Alt+Space`)
3. The window is frameless (`FramelessWindowHint`); the 44px header acts as the drag handle. Its `mousePressEvent` calls `_start_window_drag`, which prefers the compositor's native `QWindow.startSystemMove()` (required on Wayland, where manual `move()` is ignored) and falls back to the manual `_drag_pos` tracking in `mouseMoveEvent`. The header's move/release events are bound to the window's handlers so the fallback drag completes — needed because a child `QWidget` consumes mouse events instead of bubbling them to the window.
4. During recording the overlay switches to its recording view with a live `WaveformWidget`, then shows processing and success/error states as the controller transitions

---

**Best practices:** keep it short, focus on the big picture, use plain language. Avoid code snippets, implementation details, and complex jargon. See [core_architecture.md](core_architecture.md) for how the controller drives UI state changes, and [services.md](services.md) for the backend services the UI interacts with.
