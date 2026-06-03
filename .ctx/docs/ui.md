# UI Components

## What It Does
Provides the visual layer of Dicto: a settings/status window, a floating overlay for recording feedback, a system tray icon, a real-time waveform animation, and a startup splash screen. All built with PySide6 using a dark zinc-based theme.

## Main Files
- `src/ui/main_window.py` - The `MainWindow` class itself: public signals, class-level data (languages), and the constructor that wires the animation timers. Its behavior is split across mixins (see below) that all share the same instance, so the public API (`set_recording_state`, `update_transcription`, `set_presets`, …) is unchanged. Provides settings panels, status display, and stacked pages (home, settings, models). Settings includes a "Report error" section with a read-only log preview (a textarea showing the current console log buffer — exactly what will be uploaded; styled with a distinct darker `BG` background and border via the `LOG_VIEW` style so it stands apart from the surrounding settings content) a "Copy logs" button that copies the current log buffer to the clipboard, and a "Send report" button that sends those application logs to help diagnose issues; the preview refreshes whenever the settings panel opens and just before sending, and an "Updates" section showing the current version with a "Check for updates" button that uses `src/services/updater.py` to find newer GitHub releases and (on the Linux `.deb` install) download + install them in place, then offer a restart. Update checks and installs run on background `QThread` workers so the UI stays responsive.
- `src/ui/main_window_build.py` - `BuildMixin`: constructs the window's widgets (header, format tabs, stacked pages, footer, and small layout helpers)
- `src/ui/main_window_state.py` - `StateMixin`: the visual state machine (idle → recording → processing → done), animation timers, format-tab/preset handling, and copy/cancel actions
- `src/ui/main_window_settings.py` - `SettingsMixin`: settings load/save and change handlers, the audio-test monitor, UI-language retranslation, settings/models panel navigation, frameless-window dragging, and close-to-tray
- `src/ui/main_window_updates.py` - `UpdatesMixin`: the self-update flow, the "Copy logs" and "Send report" actions, plus the background `QThread` workers they use. While a check or install is in progress the relevant buttons go "busy" (disabled, dimmed via the shared `:disabled` button style, hand-cursor dropped, and the check button shows "Checking…") so they can't be clicked again or double-triggered; after a successful in-place install the action button becomes "Restart now" and the re-check button stays disabled because the running build is now stale
- `src/ui/widgets/icon_utils.py` - `make_icon` (cached SVG→QIcon) and `get_provider_svg_for_model` helpers shared by the window mixins
- `src/ui/widgets/hotkey_button.py` - `HotkeyButton`, a push button that captures a key combination when clicked
- `src/ui/overlay.py` - Frameless floating overlay showing recording/processing/success state with a draggable card, settings popover, and record/stop button
- `src/ui/tray.py` - System tray icon and context menu (show window, open config, quit)
- `src/ui/waveform.py` - Animated waveform bar widget used by both the main window and the overlay
- `src/ui/splash.py` - Frameless splash window shown during app startup
- `src/ui/icons.py` - SVG icon loader that reads and caches icons from the assets directory
- `src/ui/main_window_styles.py` - Centralized dark-mode color palette (zinc scale), font definitions, and Qt stylesheet helpers
- `src/ui/assets/` - SVG icon files (settings, record, stop, reset, close, models, openai, googlegemini, qwen, etc.)
- `src/i18n/translations.py` - UI string translations for multi-language support

## Flow
1. On startup, `SplashWindow` displays while the app initializes; once ready the main window and overlay are created
2. The `MainWindow` lets users configure settings (API key, hotkeys, audio input device, overlay options, language) and includes a live microphone test button; a system-audio toggle sits in the footer next to the record button on the home page. The `TrayManager` provides quick access from the system tray. During the processing state the footer record button shows a spinning loader icon (animated via `_loader_timer` at 30 ms intervals, rotating the SVG pixmap 12° per tick)
3. During recording the overlay switches to its recording view with a live `WaveformWidget`, then shows processing and success/error states as the controller transitions

---

**Best practices:** keep it short, focus on the big picture, use plain language. Avoid code snippets, implementation details, and complex jargon. See [core_architecture.md](core_architecture.md) for how the controller drives UI state changes, and [services.md](services.md) for the backend services the UI interacts with.
