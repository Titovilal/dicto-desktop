# Quick Start with uv

Get started with Voice to Clipboard in 3 minutes using `uv` (super fast Python package manager).

## Prerequisites

- Python 3.8+
- Linux: `sudo apt install portaudio19-dev python3-dev`
- OpenAI API key from https://platform.openai.com/api-keys

## Installation & Setup

```bash
# 1. Install uv (one-time, if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Clone and enter directory
git clone <repo-url>
cd voice-to-clipboard

# 3. Install dependencies (uv handles venv automatically)
uv sync

# 4. Configure API key
cp config.yaml.example config.yaml
# Edit config.yaml and add your OpenAI API key
# Or export OPENAI_API_KEY="sk-..."

# 5. Run!
uv run python -m src.main
```

## That's it!

- Press `Ctrl+Shift+Space` and speak
- Release to transcribe
- Text appears in your clipboard

## Alternative: Run without config file

```bash
# Set API key as environment variable and run
OPENAI_API_KEY="sk-your-key" uv run python -m src.main
```

## Why uv?

- **10-100x faster** than pip
- **No waiting** for dependency resolution
- **Built-in venv** management
- **100% compatible** with pip/PyPI
- **Zero config** needed

Learn more: https://astral.sh/uv
