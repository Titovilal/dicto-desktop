# Config

## What It Does
Manages all user-editable preferences for the app — hotkey, audio, transcription, appearance, and behavior — persisted as a YAML file under `%APPDATA%\dicto\config.yaml`. On startup the settings are loaded once into a process-wide singleton and made available to every layer of the app.

## Main Files
- `src/dicto/config/settings.py` - Pydantic `Settings` model with nested sections; handles load, save, env overrides, and the module-level singleton (`get_settings()`)
- `src/dicto/config/defaults.py` - All default values in one place (language, hotkey, audio, models, recording mode)
- `src/dicto/utils/platform.py` - OS path helpers that locate `%APPDATA%\dicto\` and its sub-directories (config, logs, audio)

## Flow
1. `DictoApp` calls `get_settings()` at boot; on first call it reads `%APPDATA%\dicto\config.yaml` via `Settings.load()`.
2. Missing or corrupt files fall back silently to defaults; the `DICTO_API_KEY` environment variable overrides the stored API key after loading.
3. When the user changes a preference in the UI, the app mutates the `Settings` object and calls `settings.save()`, which writes the full model back to YAML.

---

**Best practices:** only local machine preferences live here — library, dictionary, transforms, and account data are stored in the user's backend. See `services.md` for the API layer.
