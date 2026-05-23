# Project Overview

## What It Does
Dicto Desktop is a cross-platform desktop app (Windows/Mac) built with Tauri 2 + React that lets users record voice audio, transcribe it via an external API, and optionally transform the transcription using presets. It targets productivity users who want fast, keyboard-driven voice-to-text with a lightweight floating overlay.

## Main Files
- `src/main.tsx` — React entry point, sets up routing to the app windows
- `src/App.tsx` — Root component and route definitions
- `src/pages/MainWindow.tsx` — Primary UI window (record, transcribe, history)
- `src/pages/OverlayWindow.tsx` — Floating overlay window for quick access
- `src/pages/SettingsPage.tsx` — Settings configuration page
- `src/pages/PresetsPage.tsx` — Preset/transformation management page
- `src/hooks/useRecorder.ts` — Audio recording logic and state
- `src/hooks/useAppState.ts` — Global app state management
- `src/hooks/useConfig.ts` — Config loading and persistence
- `src/hooks/useHotkeys.ts` — Global hotkey registration
- `src/hooks/usePresets.ts` — Preset CRUD operations
- `src/hooks/useEditFlow.ts` — Voice edit / transformation flow
- `src/store/configStore.ts` — Persistent config store (via Tauri store plugin)
- `src/i18n/` — i18next setup and locale files (ES, EN, DE)
- `src-tauri/src/audio.rs` — Rust audio capture backend
- `src-tauri/src/transcription.rs` — Transcription API integration
- `src-tauri/src/transform.rs` — Text transformation logic
- `src-tauri/src/commands.rs` — Tauri command handlers exposed to frontend
- `src-tauri/src/hotkeys.rs` — System-level global hotkey handling
- `src-tauri/src/keyboard.rs` — Keyboard injection / paste automation
- `src-tauri/src/tray.rs` — System tray icon and menu
- `src-tauri/src/edit.rs` — Voice edit feature backend
- `src-tauri/tauri.conf.json` — Tauri app configuration (windows, plugins, bundle)

## Flow
1. User triggers recording via global hotkey or UI button — audio is captured by the Rust audio backend
2. On stop, the audio is sent to an external transcription API; the result is returned to the frontend
3. Optionally, the transcription is passed through a preset transformation; the final text is copied to clipboard and/or injected via keyboard automation

## Documentation available in `.ctx/docs/`
- **`frontend_ui.md`** — React pages, components, and UI structure
- **`hooks.md`** — Custom React hooks and their responsibilities
- **`rust_backend.md`** — Tauri Rust commands, audio, transcription, and keyboard modules
- **`config_and_store.md`** — Configuration schema, persistence, and the Tauri store plugin usage
- **`i18n.md`** — Internationalization setup and locale files (ES/EN/DE)
- **`tauri_config.md`** — Tauri configuration, capabilities, plugins, and window setup
