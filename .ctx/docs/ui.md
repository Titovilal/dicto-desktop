# UI

## What It Does
The UI layer renders the app's visual surface: a system tray icon, an ephemeral recording overlay, a main window with an icon rail + library + detail layout, a theme system that follows the OS, and an i18n system that lets all text switch language at runtime without restarting. The visual language follows the design hand-off in `Dicto - Entrega/` (zinc scale, dark + light, see `codigo/screens/theme.css`).

## Main Files
- `src/dicto/ui/theme/tokens.py` - Semantic token enum mirroring the design system: surfaces (BG / BG_PANEL / BG_ELEVATED / BG_HOVER), three-step text scale (TEXT / TEXT_MUTED / TEXT_DIM), neutral zinc ACCENT, BORDER(_SOFT), BLUE, KBD_BG, STATUS_* — widgets reference meaning, never raw hex
- `src/dicto/ui/theme/palettes.py` - Zinc dark + light palettes (values from the design's `theme.css`); validated at import time
- `src/dicto/ui/theme/manager.py` - `ThemeManager`: reads OS preference via Windows registry, builds the full design-system stylesheet (buttons incl. `ghost`/`iconBtn`/`chip`/`rail` variants, inputs, list cards, tabs, menus, scrollbars), emits `themeChanged`, supports live switching
- `src/dicto/ui/tray.py` - `Tray`: status-coloured icon + menu per the design (Record with hotkey label · Open library / Dictionary / Settings · Quit); emits `recordRequested` / `dictionaryRequested` etc.
- `src/dicto/ui/overlay/overlay.py` - `Overlay`: frameless, always-on-top, draggable card (330×96) per the design: grip dots on top, big round stop button left, status dot + label + mono timer, grey live waveform, pause button right; persists its dragged position in `Settings`, emits intent signals
- `src/dicto/ui/overlay/waveform.py` - `WaveformWidget`: token-coloured animated bars (live / pulse / settle modes); re-paints on `themeChanged`
- `src/dicto/ui/overlay/controls.py` - `OverlayControls` (QObject): owns the elapsed timer (`format_elapsed`) and the stop/pause/timer widgets the overlay lays out; stop turns green/play while paused; emits intent only
- `src/dicto/ui/settings/audio.py` - `MicTestPanel`: microphone picker + a live mic test driven by `AudioMonitor`, shown through a `WaveformWidget`
- `src/dicto/ui/main/window.py` - `MainWindow`: 58px icon rail (round red record button, library, dictionary, settings, avatar — emits `recordRequested`/`dictionaryRequested`/`settingsRequested`; dictionary/settings UIs land in Phase 6) + fixed 344px library column + detail pane; `refresh_library()` reloads the list after an auto-save; closing hides to tray
- `src/dicto/ui/main/library_view.py` - `LibraryView`: heading + count, search box, wrapping tag-filter chips + sort-cycle button, two-line list items (title + tag-dot · duration · date) painted by a `QStyledItemDelegate`; emits `transcriptSelected(id)` / `emptied`. No auto-refresh in the constructor — the owner calls `refresh()` after wiring
- `src/dicto/ui/main/detail_view.py` - `DetailView`: large title + actions (Edit toggle reveals Save + tags row; Copy / Export icon buttons), meta row, tab bar (Transcripción active; transform tabs disabled until Phase 5), transcript body, footer (insert-at-cursor · cleanup-on · live word count); emits `saved` / `statusMessage`
- `src/dicto/ui/main/settings_modal.py` - `SettingsModal`: frameless 720×600 modal over the main window (draggable by its header) with a left nav + stacked panels. Ships Recording (hotkey pill, capture mode, `MicTestPanel`, system audio, overlay position) and Appearance (theme + language, applied live). Changes persist via `Settings.save()` immediately. Opened by `app._open_settings()` from the rail or tray; remaining Phase 6 panels (account, output, privacy, about) plug in as more nav entries
- `src/dicto/ui/components/flow.py` - `FlowLayout`: wraps chips onto new rows (height-for-width)
- `src/dicto/ui/icons.py` - Loads `.ico` files from `assets/icons/`; maps app states to colour-coded tray variants; `svg_icon()` recolours single-path action glyphs from `assets/icons/svg/` (full design icon set: search/list/book/sort/copy/download/edit/grip/sparkles/…) to a theme token
- `src/dicto/i18n/__init__.py` - `t("key")` lookup with English fallback; `set_language()` notifies all subscribers for hot reload
- `src/dicto/i18n/locales/en.json` - English strings (tray menu, window titles, status labels, overlay, mic test, settings labels)
- `src/dicto/i18n/locales/es.json` - Spanish strings (same key set)

## Flow
1. `DictoApp` creates a `ThemeManager` (setting from config, defaulting to "system"), calls `apply()` which reads the Windows registry, picks the matching palette, and sets the application-wide Qt stylesheet.
2. `Tray` and `MainWindow` are constructed; both call `t()` to fill their text and subscribe to `on_language_changed` so a later `set_language()` call triggers `retranslate()` in place.
3. When the app state changes (IDLE → RECORDING → PROCESSING → …), `RecordingOrchestrator.stateChanged` drives both `tray.set_state(state)` (icon colour + tooltip) and `overlay.set_state(state)` (label, status dot, waveform mode, show/hide). Live RMS levels flow `orchestrator.levelChanged → overlay.set_level` so the waveform moves with the voice.
4. Overlay buttons emit intent (stop/pause/resume/openApp) back to the app layer, which calls the orchestrator — the overlay never touches audio. Pause/resume keep one continuous recording file across a class break.
5. When a transcript finishes it is auto-saved to the library; `app.py` calls `window.refresh_library()`, the `LibraryView` reloads and selects it, which loads it in the `DetailView`. There the user edits/saves/copies/exports it; saving refreshes the list (Phase 4).
6. The record intents converge: rail record button and tray "Record" both call `orchestrator.toggle()` (wired in `app.py`), same as the global hotkey in toggle mode.

---

See `core.md` for the state machine that drives tray/overlay updates, `audio.md` for capture and the mic monitor, and `config.md` for where the theme, language and overlay position are persisted.
