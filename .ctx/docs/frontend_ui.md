# Frontend UI

## What It Does
The frontend is a React + Tauri app with two distinct windows: a main window for recording, transcription, and settings, and a lightweight floating overlay for quick status awareness. Routing between windows is hash-based, and a splash screen is shown while config loads.

## Main Files
- `src/main.tsx` — React entry point; mounts the app into the DOM
- `src/App.tsx` — Root component; shows a splash screen while config loads, then sets up hash routing to the two windows
- `src/pages/MainWindow.tsx` — Primary UI with three tabs: Transcription, Presets, and Settings; handles recording controls, waveform display, overlay toggle, and transcription results
- `src/pages/OverlayWindow.tsx` — Floating overlay window; shows app status and a live waveform; draggable; has a popover menu to open the main app, hide the overlay, or reset position
- `src/pages/SettingsPage.tsx` — Settings form rendered inside the main window's Settings tab; covers API key, models, hotkeys, behavior toggles, audio devices, overlay options, and UI language
- `src/pages/PresetsPage.tsx` — Presets tab inside the main window; lists saved presets and lets the user apply them (or a custom prompt) to the last transcription, then copy the result
- `src/components/ui/Waveform.tsx` — Animated bar waveform component used in both windows to visualize audio levels
- `src/components/ui/SplashScreen.tsx` — Simple loading screen shown while the config store initializes

## Flow
1. `main.tsx` mounts `App`, which waits for `useConfig` to finish loading before rendering anything meaningful
2. `App` uses hash routing: `/` renders `MainWindow`, `/overlay` renders `OverlayWindow` (opened as a separate Tauri window)
3. In `MainWindow`, the user can start/stop recording via buttons or the global hotkey; status is reflected by a colored dot and a `Waveform`; the last transcription is displayed and can be passed to `PresetsPage` for transformation
4. `OverlayWindow` listens to Tauri events (`app-status-changed`, `audio-level`) to mirror the recording state without duplicating logic; a "⋯" menu gives quick actions
5. `SettingsPage` reads from and writes to `useConfig`; hotkey changes are applied immediately by invoking the Rust `register_hotkeys` command
6. `PresetsPage` uses `usePresets` to fetch and apply presets via the API; a custom free-form prompt is also supported; results can be copied to the clipboard
