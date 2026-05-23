# Rust Backend

## What It Does
The Rust backend powers all system-level capabilities of Dicto Desktop: audio capture, transcription API calls, text transformation, keyboard automation, global hotkeys, and the system tray. It exposes functionality to the React frontend through Tauri commands (IPC bridge).

## Main Files
- `src-tauri/src/commands.rs` — Central IPC bridge; all Tauri commands called from the frontend live here
- `src-tauri/src/audio.rs` — Microphone capture via `cpal`; encodes samples as 16kHz WAV for the transcription API
- `src-tauri/src/transcription.rs` — Sends WAV audio to `/api/transcribe` and returns transcribed text
- `src-tauri/src/transform.rs` — Sends text to `/api/transform` with a preset prompt; fetches saved presets from `/api/presets`
- `src-tauri/src/edit.rs` — Sends selected text + voice instruction to `/api/edit` for context-aware text editing
- `src-tauri/src/hotkeys.rs` — Registers OS-level global shortcuts (record, edit) using the Tauri global shortcut plugin
- `src-tauri/src/keyboard.rs` — Simulates Ctrl+C, Ctrl+V, and Enter keystrokes via the `enigo` library
- `src-tauri/src/tray.rs` — Creates the system tray icon, menu items, and status tooltip updates

## Flow

### Record & Transcribe
1. A global hotkey press (via `hotkeys.rs`) or UI button triggers `start_recording()` in `commands.rs`
2. `audio.rs` captures microphone samples using `cpal`; emits `audio-level` events every 50ms for the UI waveform
3. On stop, `audio.rs` resamples and encodes to 16kHz WAV; `transcription.rs` POSTs it to `/api/transcribe` (with retry logic)
4. The transcribed text is returned to the frontend, which can paste it or send it through a preset transformation

### Edit Flow
1. `commands::start_edit_flow()` calls `keyboard.rs::simulate_copy()` (Ctrl+C) to capture the user's selected text, then starts recording
2. The user speaks a voice instruction (e.g., "make it formal")
3. `commands::complete_edit_flow()` transcribes the instruction via `transcription.rs`, then calls `edit.rs::edit_text()` with the original text and instruction
4. The API returns the modified text; `keyboard.rs` can auto-paste the result back into the active application

### Tray & Status
- `tray.rs` sets up menu items (Open, Record, Quit) and listens for menu events
- `commands::update_app_status()` updates the tray tooltip to reflect idle / recording / processing / success / error states

---

See `frontend_ui.md` and `hooks.md` for how the React side calls these commands and manages the resulting state.
