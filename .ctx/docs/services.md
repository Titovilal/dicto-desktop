# Services

## What It Does
The services layer provides all the core capabilities that the controller orchestrates: recording audio, transcribing it via an external API, listening for global hotkeys, and interacting with the clipboard and keyboard to deliver results to the user.

## Main Files
- `src/services/recorder.py` - Records microphone audio using `sounddevice`; supports selecting a specific input device and optionally mixing system output audio (via `soundcard`: WASAPI loopback; Stereo Mix is a fallback); streams chunks in a background thread, calculates real-time audio levels, saves output as a temporary WAV file. If no input device is available (no default mic) it aborts with a clear error that `stop_recording`/`get_last_error` surface to the controller instead of a cryptic "Error querying device -1". The recorded duration is captured at stop time (`_last_duration`/`get_recording_duration`) because `stop_recording()` clears the frame buffer, which otherwise made the reported duration collapse to 0. It also exposes a live `AudioMonitor` for the settings "test microphone" button (which also captures system audio via WASAPI loopback when the "include system audio" setting is enabled, so the level bar reacts to playback as well as the mic)
- `src/services/transcriber.py` - Sends audio to the Dicto API for transcription; also supports text transformation via an LLM endpoint, with retry logic and detailed error handling (rate limits, file size validation, API key errors)
- `src/services/hotkey.py` - Global hotkey listener using `pynput`; supports "hold" mode (press-to-record, release-to-stop) and "press"/toggle mode (one fire per tap; the release just re-arms it and does not stop recording). Both modes mark the combo as pressed on key-down so OS key auto-repeat can't re-fire the callback while it is held. The user picks hold vs toggle in Settings (`behavior.recording_mode`); the controller maps "toggle" to the pynput "press" mode and routes the single press to `_on_hotkey_toggle`, which decides start vs stop from `AppState`
- `src/services/clipboard.py` - Clipboard read/write using `win32clipboard`; includes a `wait_for_change` helper that polls for clipboard updates
- `src/services/keyboard_actions.py` - Simulates keyboard shortcuts (Ctrl+V paste, Ctrl+C copy, Enter) via `pynput` to insert transcribed text into the active application; `pynput` is imported lazily on first key simulation
- `src/services/updater.py` - In-app self-update: queries the project's GitHub Releases for the latest version, compares it against the running version, and on frozen builds installs the new version in place. It downloads the Inno Setup installer (`Dicto-<ver>-setup.exe`), launches it silently (`/SILENT`), and exits the process so the installer can replace the locked files and relaunch the app when done. Falls back to opening the release download page when in-place install isn't possible. The running version is resolved by `src/version.py` from packaged metadata (baked into the PyInstaller bundle via `--copy-metadata dicto`)

## Flow
1. `HotkeyListener` detects the configured hotkey and notifies the controller via press/release callbacks
2. The controller tells `AudioRecorder` to start capturing; audio levels are streamed to the overlay waveform in real time
3. On hotkey release, recording stops and the audio file is handed to `Transcriber`, which calls the Dicto API and returns text
4. `ClipboardManager` places the transcribed text on the clipboard, and `KeyboardService` simulates a paste into the focused application

---

**Best practices:** keep it short, focus on the big picture, use plain language. Avoid code snippets, implementation details, and complex jargon. See [`core_architecture.md`](core_architecture.md) for how the controller coordinates these services, and [`ui.md`](ui.md) for the overlay and waveform.
