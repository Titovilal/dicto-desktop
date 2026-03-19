# Services

## What It Does
Backend services that handle audio capture, speech-to-text transcription, text transformation, clipboard access, and global hotkey detection.

## Main Files
- `src/services/recorder.py` - Records microphone audio via `sounddevice` into a temp WAV file
- `src/services/transcriber.py` - Sends audio to the Dicto API (`POST /api/transcribe`) and supports text transformation (`POST /api/transform`)
- `src/services/hotkey.py` - Global hotkey listener using `pynput`; tracks modifier+key combos with press/release callbacks
- `src/services/clipboard.py` - Clipboard read/write via `pyperclip`
- `src/services/__init__.py` - Package init

## Flow
1. HotkeyListener detects the configured key combo and fires press/release callbacks to the Controller
2. AudioRecorder streams microphone input in a background thread, saves to a temp WAV on stop
3. Transcriber uploads the WAV to `https://terturionsland.dev/api/transcribe` with auth, retries on rate limits
4. ClipboardManager copies the transcription text; Controller can then auto-paste via simulated Ctrl+V
