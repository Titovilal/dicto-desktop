# UI

## What It Does
The UI layer renders the app's visual surface: a system tray icon, a main window shell, a theme system that follows the OS, and an i18n system that lets all text switch language at runtime without restarting.

## Main Files
- `src/dicto/ui/theme/tokens.py` - Semantic token enum (BG, TEXT, ACCENT, STATUS_*, etc.) — widgets reference meaning, never raw hex
- `src/dicto/ui/theme/palettes.py` - Light and dark colour palettes mapping every token to a hex value; validated at import time
- `src/dicto/ui/theme/manager.py` - `ThemeManager`: reads OS preference via Windows registry, builds the Qt stylesheet, emits `themeChanged`, supports live switching
- `src/dicto/ui/tray.py` - `Tray`: system tray icon with a localised context menu (Open / Settings / Quit); recolours the icon when app state changes
- `src/dicto/ui/main/window.py` - `MainWindow`: 900×600 shell; currently shows a placeholder label; closing hides to tray instead of quitting
- `src/dicto/ui/icons.py` - Loads `.ico` files from `assets/icons/`; maps app states to colour-coded variants (idle/recording/processing/success/error)
- `src/dicto/i18n/__init__.py` - `t("key")` lookup with English fallback; `set_language()` notifies all subscribers for hot reload
- `src/dicto/i18n/locales/en.json` - English strings (tray menu, window titles, status labels, settings labels)
- `src/dicto/i18n/locales/es.json` - Spanish strings (same key set)

## Flow
1. `DictoApp` creates a `ThemeManager` (setting from config, defaulting to "system"), calls `apply()` which reads the Windows registry, picks the matching palette, and sets the application-wide Qt stylesheet.
2. `Tray` and `MainWindow` are constructed; both call `t()` to fill their text and subscribe to `on_language_changed` so a later `set_language()` call triggers `retranslate()` in place.
3. When the app state changes (IDLE → RECORDING → PROCESSING → …), the caller invokes `tray.set_state(state)`, which swaps the tray icon to the matching colour variant and updates the tooltip.

---

See `core.md` for the state machine that drives tray icon updates, and `config.md` for where the theme and language settings are persisted.
