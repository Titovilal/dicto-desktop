# Dicto

A minimalist desktop application that records your voice via a global hotkey, transcribes it using AI, and copies the result to your clipboard. Runs in the background with minimal resource usage.

## Features

- **Global Hotkey**: Press and hold a keyboard shortcut to record audio
- **AI Transcription**: Powered by OpenAI Whisper API
- **Instant Clipboard**: Transcribed text is automatically copied to clipboard
- **Visual Feedback**: Overlay window shows recording/processing status
- **Background Operation**: Lives in system tray with minimal resource usage
- **Cross-Platform**: Works on Windows 10/11 and Linux

## Prerequisites

### All Platforms

- Python 3.8 or higher
- OpenAI API key (get one at https://platform.openai.com/api-keys)

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

PyAudio will be installed automatically. No additional dependencies needed.

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

# Edit config.yaml and add your OpenAI API key
# Or set the OPENAI_API_KEY environment variable
export OPENAI_API_KEY="sk-your-api-key-here"
```

## Configuration

Edit `config.yaml` to customize the application:

```yaml
hotkey:
  modifiers: ["ctrl", "shift"]  # Modifier keys
  key: "space"                  # Main key

overlay:
  position: "top-right"         # top-left, top-right, bottom-left, bottom-right, center
  size: 100                     # Size in pixels
  opacity: 0.9                  # 0.0 to 1.0

transcription:
  provider: "openai"            # Currently only OpenAI is supported
  api_key: ""                   # Or use OPENAI_API_KEY env var
  language: "auto"              # auto, or ISO code like "es", "en"

audio:
  sample_rate: 16000            # 16kHz is optimal for speech
  max_duration: 120             # Maximum recording duration in seconds
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

### "No OpenAI API key found"

- Make sure you've set your API key in `config.yaml` or as an environment variable
- Get an API key at https://platform.openai.com/api-keys

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

- Check your internet connection (API requires internet)
- Verify your OpenAI API key is valid
- Check if you have API credits remaining
- Make sure the audio is clear and not too short

## Development

Project structure:

```
dicto-desktop/
├── src/
│   ├── main.py              # Application entry point
│   ├── controller.py        # Main controller
│   ├── ui/
│   │   ├── tray.py         # System tray manager
│   │   └── overlay.py      # Overlay window
│   ├── services/
│   │   ├── hotkey.py       # Global hotkey listener
│   │   ├── recorder.py     # Audio recording
│   │   ├── transcriber.py  # API transcription
│   │   └── clipboard.py    # Clipboard operations
│   └── config/
│       └── settings.py     # Configuration management
├── config.yaml.example      # Example configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Technology Stack

- **PySide6**: UI framework and system tray
- **pynput**: Global hotkey listener
- **pyaudio**: Audio recording
- **pyperclip**: Clipboard operations
- **httpx**: HTTP client for API calls
- **OpenAI Whisper API**: Speech-to-text transcription

## Resource Usage

- **Idle**: ~20-30 MB RAM
- **Recording**: ~50 MB RAM (audio buffer)
- **Processing**: Depends on audio length and API response time

## Privacy & Security

- Audio is recorded locally and only sent to OpenAI's API for transcription
- No audio is stored permanently (temporary files are deleted after transcription)
- Your OpenAI API key should be kept secure
- See OpenAI's privacy policy for how they handle audio data

## License

[Add your license here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Roadmap

Future improvements:
- [ ] Custom icons for tray and overlay
- [ ] Support for other transcription providers (local Whisper, Google, etc.)
- [ ] Audio device selection in UI
- [ ] Transcription history with search
- [ ] Configurable post-processing (punctuation, formatting)
- [ ] Packaging as standalone executable
- [ ] Auto-update functionality

## Support

If you encounter issues or have questions:
1. Check the Troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with details about your problem

---

Made with ❤️ for productivity enthusiasts
