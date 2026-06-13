# Audio

## What It Does
Captures microphone input (and optionally system audio) while the user is recording, writes the stream to rotating WAV chunks on disk, and trims silence before the chunks are handed off for transcription. The pipeline is designed to avoid unbounded RAM usage and keep each piece of audio as a standalone, valid file.

## Main Files
- `src/dicto/audio/capture.py` - Streams audio from the microphone on a background thread using `sounddevice`; handles resampling, live RMS callbacks, and pause/resume
- `src/dicto/audio/monitor.py` - `AudioMonitor`: opens an input stream purely to surface the live RMS level for the mic-test panel; writes nothing to disk, shares the level math with `capture.py`
- `src/dicto/audio/devices.py` - Enumerates and selects input devices; negotiates sample rates; detects WASAPI loopback for system audio on Windows
- `src/dicto/audio/loopback.py` - `LoopbackCapture`: records system audio (WASAPI loopback via `soundcard`, Stereo Mix fallback) to chunks as a selectable source
- `src/dicto/audio/session_writer.py` - Writes int16 PCM to rotating WAV chunks using `ChunkPolicy` to decide when to start a new file
- `src/dicto/core/pipeline.py` - `Pipeline`: pure orchestrator that turns each on-disk chunk into a retryable transcription `Job` and re-stitches the result
- `src/dicto/core/chunking.py` - Pure chunk-rotation policy (`ChunkPolicy`): rotates when a chunk exceeds the max duration (5 min) or max size (20 MB)
- `src/dicto/core/vad.py` - `trim_silence()`: removes non-speech regions from a chunk using `webrtcvad`; pure function, returns original audio on any error
- `src/dicto/config/defaults.py` - Default audio values: 16 kHz sample rate, mono, 2-hour max session duration
- `src/dicto/config/settings.py` - `AudioSettings` Pydantic model (sample_rate, channels, max_duration, input_device, include_system_audio)

## Flow
1. When the user triggers a recording (via the global hotkey), `AudioCapture` opens the selected input device and starts streaming audio blocks to a background thread.
2. Each block is forwarded to `SessionWriter`, which appends it to the current WAV chunk. `ChunkPolicy` tracks accumulated bytes and duration; when either limit is hit, the current chunk is closed and a new one is opened.
3. When recording stops, `Pipeline` makes one retryable `Job` per chunk and transcribes them in order, retrying network failures from the audio still on disk. Silence is trimmed best-effort with `trim_silence()` just before each chunk is uploaded (in `services/api/factory.py`); progress and partial text are published on the event bus.

---

See `core.md` for the state machine and event bus, `services.md` for how chunks are consumed by the transcription service, and `config.md` for persisted audio settings.
