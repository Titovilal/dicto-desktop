# Dicto

Minimalist Windows desktop app for voice-to-text transcription with a global hotkey.

> **Rebuild in progress.** This branch is a from-scratch rewrite following
> [`REBUILD_PLAN.md`](REBUILD_PLAN.md), keeping the proven stack
> (PySide6 + httpx + sounddevice/soundcard + pynput + pywin32 + PyInstaller/Inno)
> with a clean layered architecture. The previous codebase lives, git-ignored,
> in `Antiguo/` for reference and on the `windows-only` / `to-the-moon-all-in-windows`
> branches.

## Architecture

Layers, not types — the core is pure and Qt-free:

```
core      pure domain logic (state, events, models, pipeline) — no Qt, no network, no OS
audio     audio capture (stream → chunks on disk)
services  external effects (API client, hotkey, injector, clipboard, updater)
transform declarative AI presets
config    typed settings (pydantic) persisted to %APPDATA%\dicto\config.yaml
i18n      t() + JSON locales + live languageChanged
ui        Qt widgets (tray, overlay, main window) — consume theme tokens, never raw colour
utils     logging (+ ring buffer for bug reports), Windows paths
```

## Develop

```powershell
uv pip install -e ".[dev]"
python -m dicto          # launch the app
pytest                   # run the test suite
```

See [`AGENTS.md`](AGENTS.md) and `REBUILD_PLAN.md` for the phased plan.

## License

MIT
