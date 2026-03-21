# Services

## What It Does
Backend services that handle audio recording, speech-to-text transcription, clipboard management, and global hotkey detection. These are the core engines that power Dicto's voice-to-text pipeline.

## Main Files
- `src/services/recorder.py` - Records audio from the microphone using sounddevice, saves to temporary WAV files
- `src/services/transcriber.py` - Sends audio to the Dicto API for transcription and supports text transformation
- `src/services/clipboard.py` - Copies transcribed text to the system clipboard using pyperclip
- `src/services/hotkey.py` - Listens for global hotkey combinations using pynput to trigger recording
- `src/controller.py` - Orchestrates all services, manages app state (idle/recording/processing/success/error), and bridges UI signals

## Flow
1. `HotkeyListener` detects a key press (default: Ctrl+Shift+Space) and notifies the `Controller`
2. `Controller` tells `AudioRecorder` to start capturing microphone input on a background thread
3. On hotkey release, the recording stops, audio is saved to a temp WAV file, and `Transcriber` sends it to the Dicto API
4. The transcribed text is copied to clipboard via `ClipboardManager`, and optionally auto-pasted and auto-entered via simulated keypresses
