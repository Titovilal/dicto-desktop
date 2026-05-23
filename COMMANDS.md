# Commands

## Dev

| Command | Description |
|---------|-------------|
| `uv run dicto` | Run the app |
| `uvx ruff format` | Format code |
| `uvx ruff check` | Lint code |
| `uvx ty check` | Type check |

## Clean

| Command | Description |
|---------|-------------|
| `rmdir /s /q build dist` | Clean build artifacts (Windows) |
| `rm -rf build dist *.spec` | Clean build artifacts (macOS/Linux) |

## Build — PyInstaller

| Command | Description |
|---------|-------------|
| `uv pip install -e ".[dev]"` | Install dev dependencies (required before building) |

### Windows

```powershell
# onefile — single exe, slow startup, more antivirus issues
uv run pyinstaller --name "Dicto" --onefile --windowed --noconfirm --add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" --icon "assets/icons/icon.ico" src/main.py

# onedir — folder with all files, fast startup (recommended for dev)
uv run pyinstaller --name "Dicto" --onedir --windowed --noconfirm --add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" --icon "assets/icons/icon.ico" src/main.py
```

### macOS / Linux

```bash
# onefile
uv run pyinstaller --name "Dicto" --onefile --windowed --noconfirm --add-data "assets:assets" --add-data "src/ui/assets:src/ui/assets" --icon "assets/icons/icon.svg" src/main.py

# onedir
uv run pyinstaller --name "Dicto" --onedir --windowed --noconfirm --add-data "assets:assets" --add-data "src/ui/assets:src/ui/assets" --icon "assets/icons/icon.svg" src/main.py
```

## Release

```bash
# Trigger GitHub Actions release workflow (version from pyproject.toml)
gh workflow run build.yml -f create_release=true
```
