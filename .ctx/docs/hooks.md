# Custom React Hooks

## What It Does
These hooks encapsulate all stateful logic for recording, transcription, configuration, hotkeys, presets, and voice editing. They act as the bridge between the React UI and the Tauri/Rust backend.

## Main Files
- `src/hooks/useRecorder.ts` — Wraps Tauri commands for starting/stopping audio recording and transcribing audio; also listens for real-time audio level events from Rust
- `src/hooks/useAppState.ts` — Top-level state machine that orchestrates recording, transcription, and edit flows; exposes a single `status` value (`idle`, `recording`, `processing`, `editing`, `success`, `error`) to the UI
- `src/hooks/useConfig.ts` — Loads and persists `AppConfig` via the Tauri store plugin (`config.json`); merges saved values with defaults on startup
- `src/hooks/useHotkeys.ts` — Registers listeners for `hotkey-record` and `hotkey-edit` Tauri events and exposes `updateHotkeys` to re-register hotkeys at the Rust level
- `src/hooks/usePresets.ts` — Fetches preset definitions from the backend (`fetch_presets`), and provides `applyPreset` / `applyCustomPrompt` which call the `transform_text` Rust command
- `src/hooks/useEditFlow.ts` — Manages the two-step voice-edit flow: captures selected text via clipboard on `edit-copy-done`, records a voice edit command, then calls `complete_edit_flow` and optionally auto-pastes/enters the result

## Flow
1. On mount, `useConfig` loads the persisted config; `useHotkeys` attaches event listeners for global hotkeys forwarded by Rust
2. When a record hotkey fires, `useAppState` calls `useRecorder.startRecording()` and transitions status to `recording`; on a second press it stops recording, transcribes the audio, copies the result to clipboard, and moves through `processing → success → idle`
3. When the edit hotkey fires, `useAppState` delegates to `useEditFlow`: the first press captures the currently selected text and records a voice instruction; the second press sends both to the backend, writes the transformed text to clipboard, and optionally simulates paste/enter

---

See `rust_backend.md` for the Tauri commands these hooks invoke, and `config_and_store.md` for the config schema and store details.
