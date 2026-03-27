# Services

## What It Does
Backend services that handle audio recording, speech-to-text transcription, clipboard management, and global hotkey detection. These are the core engines that power Dicto's voice-to-text pipeline.

## Main Files
- `src/services/recorder.py` - Records audio from the microphone using sounddevice, saves to temporary WAV files. Supports an optional audio level callback (`set_audio_level_callback`) that emits RMS-based levels (0.0-1.0) per chunk for real-time waveform visualization
- `src/services/transcriber.py` - Sends audio to the Dicto API for transcription, text transformation, and voice-based text editing. Accepts separate model settings for transcription (`model`), transformation (`transformation_model`), and edition (`edition_model`)
- `src/services/clipboard.py` - Copies transcribed text to the system clipboard using pyperclip
- `src/services/hotkey.py` - Listens for global hotkey combinations using pynput to trigger recording
- `src/services/keyboard_actions.py` - Centralizes keyboard simulation (paste, enter, copy) via pynput, used by Controller for auto-paste/auto-enter and edit flows
- `src/controller.py` - Orchestrates all services, manages app state (idle/recording/processing/success/error), and bridges UI signals. Uses `KeyboardService` for keyboard automation and a generic `_update_hotkey_listener()` for hotkey reconfiguration. Emits `audio_level_changed(float)` signal from the recorder's audio callback for real-time waveform updates. Provides a `cancel()` method that aborts the current operation: if recording, stops and cleans up the temp file; if processing, sets a `_cancelled` flag so background task results are discarded when they arrive on the main thread. Emits `cancel_completed` signal after cancellation

## Flow
1. `HotkeyListener` detects a key press (default: Ctrl+Shift+Space) and notifies the `Controller`
2. `Controller` tells `AudioRecorder` to start capturing microphone input on a background thread
3. On hotkey release, the recording stops, audio is saved to a temp WAV file, and `Transcriber` sends it to the Dicto API
4. The transcribed text is copied to clipboard via `ClipboardManager`, and optionally auto-pasted and auto-entered via simulated keypresses

### Edit Selection Flow
A second `HotkeyListener` (mode="hold", default: Ctrl+Shift+E) triggers the edit flow:
1. On press: Controller simulates Ctrl+C to copy selected text, waits 150ms, reads clipboard, then starts recording voice instructions from the microphone
2. On release: Stops recording, transcribes the voice audio to get text instructions, then sends both the selected text and transcribed instructions to `Transcriber.transform()`
3. Copies the result to clipboard and optionally auto-pastes/auto-enters based on `edit` settings

## HotkeyListener Modes
- `"hold"` (default): fires `on_press` when hotkey is pressed, `on_release` when released (used for recording and edit selection)
- `"press"`: fires `on_press` on a single press without tracking release state
