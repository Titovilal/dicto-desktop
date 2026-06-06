# UI

## What It Does
The UI layer renders the app's visual surface: a system tray icon, an ephemeral recording overlay, a main window shell, a theme system that follows the OS, and an i18n system that lets all text switch language at runtime without restarting.

## Main Files
- `src/dicto/ui/theme/tokens.py` - Semantic token enum (BG, TEXT, ACCENT, STATUS_*, etc.) — widgets reference meaning, never raw hex
- `src/dicto/ui/theme/palettes.py` - Light and dark colour palettes mapping every token to a hex value; validated at import time
- `src/dicto/ui/theme/manager.py` - `ThemeManager`: reads OS preference via Windows registry, builds the Qt stylesheet, emits `themeChanged`, supports live switching
- `src/dicto/ui/tray.py` - `Tray`: system tray icon with a localised context menu (Open / Settings / Quit); recolours the icon when app state changes
- `src/dicto/ui/overlay/overlay.py` - `Overlay`: frameless, always-on-top, draggable status card shown while recording/processing; reflects `AppState`, hosts the live waveform and controls, persists its dragged position in `Settings`, emits intent signals (record/stop/pause/resume/openApp)
- `src/dicto/ui/overlay/waveform.py` - `WaveformWidget`: token-coloured animated bars (live / pulse / settle modes); re-paints on `themeChanged`
- `src/dicto/ui/overlay/controls.py` - `OverlayControls`: elapsed timer (`format_elapsed`) plus pause/resume and stop buttons; emits intent only
- `src/dicto/ui/settings/audio.py` - `MicTestPanel`: microphone picker + a live mic test driven by `AudioMonitor`, shown through a `WaveformWidget`
- `src/dicto/ui/main/window.py` - `MainWindow`: 900×600 shell; currently shows a placeholder label; closing hides to tray instead of quitting
- `src/dicto/ui/icons.py` - Loads `.ico` files from `assets/icons/`; maps app states to colour-coded tray variants; `svg_icon()` recolours single-path action glyphs from `assets/icons/svg/` to a theme token (record/stop/pause/settings/…)
- `src/dicto/i18n/__init__.py` - `t("key")` lookup with English fallback; `set_language()` notifies all subscribers for hot reload
- `src/dicto/i18n/locales/en.json` - English strings (tray menu, window titles, status labels, overlay, mic test, settings labels)
- `src/dicto/i18n/locales/es.json` - Spanish strings (same key set)

## Flow
1. `DictoApp` creates a `ThemeManager` (setting from config, defaulting to "system"), calls `apply()` which reads the Windows registry, picks the matching palette, and sets the application-wide Qt stylesheet.
2. `Tray` and `MainWindow` are constructed; both call `t()` to fill their text and subscribe to `on_language_changed` so a later `set_language()` call triggers `retranslate()` in place.
3. When the app state changes (IDLE → RECORDING → PROCESSING → …), `RecordingOrchestrator.stateChanged` drives both `tray.set_state(state)` (icon colour + tooltip) and `overlay.set_state(state)` (label, status dot, waveform mode, show/hide). Live RMS levels flow `orchestrator.levelChanged → overlay.set_level` so the waveform moves with the voice.
4. Overlay buttons emit intent (stop/pause/resume/openApp) back to the app layer, which calls the orchestrator — the overlay never touches audio. Pause/resume keep one continuous recording file across a class break.

---

See `core.md` for the state machine that drives tray/overlay updates, `audio.md` for capture and the mic monitor, and `config.md` for where the theme, language and overlay position are persisted.
