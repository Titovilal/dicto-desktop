# Commands

## Make targets (shortcuts)

A `Makefile` wraps the commands below. Run `make help` to list them.

| Target | Equivalent | Notes |
|--------|------------|-------|
| `make run` | `uv run dicto` | |
| `make format` / `make lint` / `make typecheck` | ruff format / check, ty check | |
| `make dev-deps` | `uv pip install -e ".[dev]"` | |
| `make exe` / `make exe-onefile` | PyInstaller onedir / onefile | needs Windows |
| `make installer` | Inno Setup `ISCC.exe installer.iss` | needs Inno Setup 6 |
| `make clean` | `rmdir /s /q build dist` | |
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
| `rmdir /s /q build dist` | Clean build artifacts — `Dicto.spec` is tracked, do not delete it |

## Build — PyInstaller

| Command | Description |
|---------|-------------|
| `uv pip install -e ".[dev]"` | Install dev dependencies (required before building) |

```powershell
# onefile — single exe, slow startup, more antivirus issues
uv run pyinstaller --name "Dicto" --onefile --windowed --noconfirm --copy-metadata dicto --add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" --icon "assets/icons/icon.ico" src/main.py

# onedir — folder with all files, fast startup (recommended for dev)
uv run pyinstaller --name "Dicto" --onedir --windowed --noconfirm --copy-metadata dicto --add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" --icon "assets/icons/icon.ico" src/main.py
```

## Release

```bash
# Trigger GitHub Actions release workflow (version from pyproject.toml)
gh workflow run build.yml -f create_release=true
```
