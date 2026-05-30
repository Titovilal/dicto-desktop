# Commands

## Make targets (shortcuts)

A `Makefile` wraps the commands below. Run `make help` to list them.

| Target | Equivalent | Notes |
|--------|------------|-------|
| `make run` | `uv run dicto` | |
| `make format` / `make lint` / `make typecheck` | ruff format / check, ty check | |
| `make dev-deps` | `uv pip install -e ".[dev]"` | |
| `make build` / `make build-onefile` | PyInstaller onedir / onefile | Linux/macOS |
| `make deb` | `bash scripts/build-deb.sh` | Linux `.deb` |
| `make exe` / `make exe-onefile` | PyInstaller onedir / onefile | **Windows only** (no cross-compile) |
| `make installer` | Inno Setup `ISCC.exe installer.iss` | **Windows only**, needs Inno Setup 6 |
| `make clean` / `make clean-deb` | `rm -rf build dist` / `rm -f dist/*.deb` | |
| `make release` | `gh workflow run build.yml -f create_release=true` | |

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
| `rm -rf build dist` | Clean build artifacts (macOS/Linux) — `Dicto.spec` is tracked, do not delete it |

## Build — PyInstaller

| Command | Description |
|---------|-------------|
| `uv pip install -e ".[dev]"` | Install dev dependencies (required before building) |

### Windows

```powershell
# onefile — single exe, slow startup, more antivirus issues
uv run pyinstaller --name "Dicto" --onefile --windowed --noconfirm --copy-metadata dicto --add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" --icon "assets/icons/icon.ico" src/main.py

# onedir — folder with all files, fast startup (recommended for dev)
uv run pyinstaller --name "Dicto" --onedir --windowed --noconfirm --copy-metadata dicto --add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" --icon "assets/icons/icon.ico" src/main.py
```

### macOS / Linux

```bash
# onefile — PyInstaller does not accept SVG icons on Linux/macOS, so no --icon here
uv run pyinstaller --name "Dicto" --onefile --windowed --noconfirm --copy-metadata dicto --add-data "assets:assets" --add-data "src/ui/assets:src/ui/assets" src/main.py

# onedir
uv run pyinstaller --name "Dicto" --onedir --windowed --noconfirm --copy-metadata dicto --add-data "assets:assets" --add-data "src/ui/assets:src/ui/assets" src/main.py
```

## Build — Linux `.deb`

Builds the PyInstaller onedir bundle and packages it into `dist/dicto_<version>_<arch>.deb`
(version read from `pyproject.toml`). System libs needed: `portaudio19-dev libasound2-dev fakeroot`.

```bash
# build PyInstaller + package .deb
bash scripts/build-deb.sh

# reuse an existing dist/dicto (skip the PyInstaller step)
SKIP_PYINSTALLER=1 bash scripts/build-deb.sh

# install / uninstall (resolves system deps via apt)
sudo apt install ./dist/dicto_2.5.1_amd64.deb
sudo apt remove dicto

# clean only the .deb artifacts
rm -f dist/*.deb
```

## Release

```bash
# Trigger GitHub Actions release workflow (version from pyproject.toml)
gh workflow run build.yml -f create_release=true
```
