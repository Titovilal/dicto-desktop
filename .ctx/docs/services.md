# Services

## What It Does
The services layer provides all the core capabilities that the controller orchestrates: recording audio, transcribing it via an external API, listening for global hotkeys, and interacting with the clipboard and keyboard to deliver results to the user.

## Main Files
- `src/services/recorder.py` - Records microphone audio using `sounddevice`; supports selecting a specific input device and optionally mixing system output audio (via `soundcard`: WASAPI loopback on Windows, PulseAudio/PipeWire monitor source on Linux; Stereo Mix is a Windows-only fallback); streams chunks in a background thread, calculates real-time audio levels, saves output as a temporary WAV file, and exposes a live `AudioMonitor` for the settings "test microphone" button (which also captures system audio via WASAPI loopback when the "include system audio" setting is enabled, so the level bar reacts to playback as well as the mic)
- `src/services/transcriber.py` - Sends audio to the Dicto API for transcription; also supports text transformation and editing via LLM endpoints, with retry logic and detailed error handling (rate limits, file size validation, API key errors)
- `src/services/hotkey.py` - Cross-platform global hotkey listener using `pynput`; supports "hold" mode (press-to-record, release-to-stop) and "press" mode; includes a factory function (`create_hotkey_listener`) that selects the Wayland backend when appropriate
- `src/services/hotkey_wayland.py` - Wayland-specific hotkey listener that uses the XDG GlobalShortcuts portal over D-Bus (`dbus-next`); needed because Wayland compositors don't allow direct key grabbing
- `src/services/clipboard.py` - Platform-aware clipboard read/write; uses `win32clipboard` on Windows and `pyperclip` elsewhere; includes a `wait_for_change` helper that polls for clipboard updates
- `src/services/keyboard_actions.py` - Simulates keyboard shortcuts (Ctrl+V paste, Ctrl+C copy, Enter) via `pynput` to insert transcribed text into the active application

## Flow
1. `HotkeyListener` (or its Wayland variant) detects the configured hotkey and notifies the controller via press/release callbacks
2. The controller tells `AudioRecorder` to start capturing; audio levels are streamed to the overlay waveform in real time
3. On hotkey release, recording stops and the audio file is handed to `Transcriber`, which calls the Dicto API and returns text
4. `ClipboardManager` places the transcribed text on the clipboard, and `KeyboardService` simulates a paste into the focused application

---

**Best practices:** keep it short, focus on the big picture, use plain language. Avoid code snippets, implementation details, and complex jargon. See [`core_architecture.md`](core_architecture.md) for how the controller coordinates these services, and [`ui.md`](ui.md) for the overlay and waveform.
