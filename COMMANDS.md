# Commands

## Make targets (shortcuts)

A `Makefile` wraps the commands below. Run `make help` to list them.

| Target | Equivalent | Notes |
|--------|------------|-------|
| `make run` | `uv run dicto` | |
| `make format` / `make lint` / `make typecheck` | ruff format / check, ty check | |
| `make dev-deps` | `uv pip install -e ".[dev]"` | |
| `make build` | `uv run pyinstaller --noconfirm dicto-linux.spec` | Linux/macOS (onedir) |
| `make deb` | `bash scripts/build-deb.sh` | Linux `.deb` |
| `make exe` | `uv run pyinstaller --noconfirm dicto.spec` | **Windows only** (no cross-compile) |
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
| `rm -rf build dist` | Clean build artifacts (macOS/Linux) |

The tracked specs are `dicto.spec` (Windows) and `dicto-linux.spec` (Linux) — both
lowercase, and neither lives under `build/` or `dist/`, so cleaning never touches
them. A capitalised `Dicto.spec` is **not** a real file: it was a byte-identical
duplicate that PyInstaller regenerated whenever it was called with `--name Dicto`.
It has been deleted and no build path creates it any more. If one reappears, some
command is bypassing the spec — fix that command rather than committing the file.

## Build — PyInstaller

| Command | Description |
|---------|-------------|
| `uv pip install -e ".[dev]"` | Install dev dependencies (required before building) |

**Always build through the committed spec — never with loose flags.** Every build
path (local `make`, and both CI jobs) runs the spec, so they cannot drift apart.

### Windows

```powershell
# onedir -> dist/Dicto/Dicto.exe (the layout installer.iss expects)
uv run pyinstaller --noconfirm dicto.spec
```

### macOS / Linux

```bash
# onedir -> dist/Dicto/Dicto
uv run pyinstaller --noconfirm dicto-linux.spec

# CI builds the same bundle as dist/dicto/dicto for the portable tarball:
DICTO_BUNDLE_NAME=dicto uv run pyinstaller --noconfirm dicto-linux.spec
```

> **Why the spec and not flags.** Passing `--name`/`--add-data`/`--icon` by hand
> *ignores the spec file entirely*. That is what shipped v2.8.2 with a dead
> microphone: the loose-flag command missed `dicto-linux.spec`'s exclusion of
> `libportaudio`/`libasound`/`libjack`, so the bundle overrode the system audio
> libs and every PCM except raw `hw:` disappeared. `--name Dicto` additionally
> regenerates the phantom `Dicto.spec`. If you need to change a build option,
> change it **in the spec**, where all paths inherit it.

## Build — Linux `.deb`

Builds the PyInstaller onedir bundle and packages it into `dist/dicto_<version>_<arch>.deb`
(version read from `pyproject.toml`). System libs needed: `portaudio19-dev libasound2-dev fakeroot`.

```bash
# build PyInstaller + package .deb
bash scripts/build-deb.sh

# reuse an existing dist/dicto (skip the PyInstaller step)
SKIP_PYINSTALLER=1 bash scripts/build-deb.sh

# install / uninstall (resolves system deps via apt)
# The version in the filename comes from pyproject.toml — check `ls dist/*.deb`.
sudo apt install ./dist/dicto_2.8.4_amd64.deb
sudo apt remove dicto

# clean only the .deb artifacts
rm -f dist/*.deb
```

The package declares `libc6 (>= 2.35)`, matching the `ubuntu-22.04` runner that
builds every published release. A `.deb` you build locally on a newer distro
carries binaries that really need a newer glibc than that, so it will install on
22.04 and then crash — the script prints a warning when it detects this. Local
builds are for testing; publish from CI.

## Release

```bash
# Trigger GitHub Actions release workflow (version from pyproject.toml)
gh workflow run build.yml -f create_release=true
```
