# Dicto

A minimalist desktop application that records your voice via a global hotkey, transcribes it using AI, and copies the result to your clipboard. Runs in the background with minimal resource usage.

## Features

- **Global Hotkey**: Press and hold a keyboard shortcut to record audio
- **AI Transcription**: Powered by the Dicto API (`https://dicto.up.railway.app`)
- **Instant Clipboard**: Transcribed text is automatically copied to clipboard
- **Visual Feedback**: Overlay window shows recording/processing status
- **Background Operation**: Lives in system tray with minimal resource usage
- **Cross-Platform**: Works on Windows 10/11 and Linux

## Prerequisites

### All Platforms

- Python 3.9 or higher (`requires-python` in `pyproject.toml`; CI builds on 3.11)
- A **Dicto API key**. Dicto talks to its own backend
  (`https://dicto.up.railway.app`, overridable with the `DICTO_API_URL` env var),
  **not** to OpenAI directly — there is no `platform.openai.com` key involved.
  Set it in the app's settings window, in `config.yaml`, or via the
  `DICTO_API_KEY` environment variable.

### Linux

Install PortAudio development files:

```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev python3-dev

# Fedora
sudo dnf install portaudio-devel python3-devel

# Arch Linux
sudo pacman -S portaudio
```

### Windows

No additional system dependencies. Audio capture uses `sounddevice` (which ships
its own PortAudio wheel on Windows) plus `soundcard` for optional system-audio
capture — the project does **not** use PyAudio.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dicto-desktop
```

2. Install dependencies (choose one method):

### Option A: Using uv (recommended - 10-100x faster)
```bash
# Install uv if you don't have it (one-time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
# Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Or use pyproject.toml (even cleaner):
uv sync
```

### Option B: Using traditional pip
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Why uv?** It's 10-100x faster than pip, written in Rust, and fully compatible with pip/PyPI. Learn more at [astral.sh/uv](https://astral.sh/uv)

3. Configure the application:
```bash
# Copy the example config
cp config.yaml.example config.yaml

# Edit config.yaml and add your Dicto API key
# Or set the DICTO_API_KEY environment variable
export DICTO_API_KEY="your-dicto-api-key"
```

## Configuration

Edit `config.yaml` to customize the application. Running from source it sits in
the project root; in an installed build it lives in the per-user config dir
(`~/.config/dicto/config.yaml` on Linux/macOS, `%APPDATA%\dicto\config.yaml` on
Windows) because the install dir is read-only. Most settings are also editable
from the app's settings window.

```yaml
hotkey:
  modifiers: ["ctrl", "shift"]  # Modifier keys
  key: "space"                  # Main key

overlay:
  position: "top-right"         # top-left, top-right, bottom-left, bottom-right, center
  size: 100                     # Size in pixels
  opacity: 0.9                  # 0.0 to 1.0

transcription:
  api_key: ""                   # Or use the DICTO_API_KEY env var
  language: "es"                # ISO code like "es", "en"
  model: "v3-turbo"

audio:
  sample_rate: 16000            # 16kHz is optimal for speech
  max_duration: 7200            # Maximum recording duration in seconds (2 hours)
  channels: 1                   # 1 for mono, 2 for stereo
```

## Usage

1. Start the application:
```bash
# If using uv:
uv run python -m src.main

# Or with traditional python:
python -m src.main

# Or if installed with pip install -e .:
dicto
```

2. The app will start in the background and show an icon in the system tray.

3. Use the hotkey to record:
   - **Press and hold** the hotkey (default: `Ctrl+Shift+Space`)
   - **Speak** your message
   - **Release** the hotkey to stop recording
   - The overlay will show "Transcribing..." while processing
   - When done, the text is automatically copied to your clipboard

4. Right-click the tray icon for options:
   - **Last Transcription**: View your most recent transcription
   - **Status**: See current application state
   - **Quit**: Exit the application

## Troubleshooting

### "No API key found"

- Make sure you've set your **Dicto** API key in the settings window, in
  `config.yaml`, or via the `DICTO_API_KEY` environment variable
- This is a Dicto API key, not an OpenAI one

### "Failed to initialize audio system"

**On Linux:**
- Install PortAudio: `sudo apt install portaudio19-dev`
- Check microphone permissions
- Verify your microphone works: `arecord -l`

**On Windows:**
- Check microphone permissions in Windows Settings > Privacy > Microphone
- Make sure no other application is exclusively using the microphone

### "Hotkey not working"

- Make sure the hotkey combination isn't already used by another application
- Try changing the hotkey in `config.yaml`
- On Linux, you may need to run with appropriate permissions

### "Transcription failed"

- Check your internet connection (the API requires internet)
- Verify your Dicto API key is valid and has credit remaining
- Make sure the audio is clear and not too short
- To point the app at a different backend, set `DICTO_API_URL`

## Development

Project structure:

```
dicto-desktop/
├── src/
│   ├── main.py                  # Application entry point
│   ├── controller.py            # Main controller
│   ├── ui/
│   │   ├── main_window*.py      # Settings window (split by concern)
│   │   ├── tray.py              # System tray manager
│   │   └── overlay.py           # Overlay window
│   ├── services/
│   │   ├── hotkey.py            # Global hotkey listener
│   │   ├── hotkey_wayland.py    # Wayland-specific hotkey path
│   │   ├── recorder.py          # Audio recording
│   │   ├── transcriber.py       # API transcription
│   │   ├── keyboard_actions.py  # Auto-paste / auto-enter
│   │   ├── clipboard.py         # Clipboard operations
│   │   ├── routes.py            # Dicto API endpoints
│   │   └── updater.py           # Self-update
│   ├── i18n/                    # Translations
│   └── config/
│       └── settings.py          # Configuration management
├── dicto.spec / dicto-linux.spec  # PyInstaller build specs
├── config.yaml.example          # Example configuration
└── README.md                    # This file
```

See `COMMANDS.md` for the full command reference, `RELEASING.md` for the release
process, and `.ctx/docs/` for design notes.

## Technology Stack

- **PySide6**: UI framework and system tray
- **pynput**: Global hotkey listener
- **sounddevice**: Audio recording (PortAudio bindings)
- **soundcard**: Optional system-audio (loopback) capture
- **pyperclip**: Clipboard operations
- **httpx**: HTTP client for API calls
- **Dicto API**: Speech-to-text transcription and text transformation

## Resource Usage

- **Idle**: ~20-30 MB RAM
- **Recording**: ~50 MB RAM (audio buffer)
- **Processing**: Depends on audio length and API response time

## Privacy & Security

- Audio is recorded locally and sent to the Dicto API for transcription
- No audio is stored permanently (temporary files are deleted after transcription)
- Your Dicto API key should be kept secure

## License

[Add your license here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Roadmap

Future improvements:
- [x] Audio device selection in UI
- [x] Packaging as standalone executable (Windows installer, Linux `.deb` / tarball — see `RELEASING.md`)
- [x] Auto-update functionality (`src/services/updater.py`)
- [ ] Support for other transcription providers (local Whisper, Google, etc.)
- [ ] Transcription history with search
- [ ] Configurable post-processing (punctuation, formatting)

## Support

If you encounter issues or have questions:
1. Check the Troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with details about your problem

---

Made with ❤️ for productivity enthusiasts
