# Config and Store

## What It Does
Manages the app's persistent configuration — API keys, hotkeys, overlay behavior, audio settings, and more. Config is saved to disk using the Tauri store plugin and loaded on startup, with defaults applied for any missing keys.

## Main Files
- `src/types/index.ts` — Defines the `AppConfig` interface and `DEFAULT_CONFIG` with all fields and their default values
- `src/hooks/useConfig.ts` — React hook that loads config from disk on mount, exposes it to components, and provides a `saveConfig` function for updates
- `src/store/configStore.ts` — Placeholder file reserved for future Zustand or global state management (currently empty)

## Flow
1. On app startup, `useConfig` creates a `LazyStore` backed by `config.json` (via `@tauri-apps/plugin-store`) and reads the saved `config` key from disk
2. The saved config is merged with `DEFAULT_CONFIG` so any new/missing fields always have a fallback value
3. When the user changes a setting (e.g. in `SettingsPage`), `saveConfig` merges the update into the current config, updates React state, and persists the new value to disk immediately

## Config Fields

| Field | Type | Default | Purpose |
|---|---|---|---|
| `apiKey` | string | `''` | API key for transcription/transform services |
| `language` | `es/en/de` | `'es'` | Language sent to the transcription API |
| `uiLanguage` | `es/en/de` | `'es'` | UI display language |
| `transcriptionModel` | `v3-turbo/v3` | `'v3-turbo'` | Transcription model to use |
| `transformModel` | string | `'qwen/qwen3-32b'` | LLM model for preset transformations |
| `editModel` | string | `'qwen/qwen3-32b'` | LLM model for voice edit feature |
| `hotkey` | string | `Ctrl+Shift+Space` | Global hotkey to start/stop recording |
| `editHotkey` | string | `Ctrl+Alt+Space` | Global hotkey for voice edit mode |
| `autoPaste` | boolean | `true` | Auto-paste transcription result after recording |
| `autoEnter` | boolean | `false` | Send Enter key after paste |
| `editAutoPaste` | boolean | `true` | Auto-paste after voice edit |
| `editAutoEnter` | boolean | `false` | Send Enter key after edit paste |
| `overlayPosition` | enum | `'bottom-right'` | Corner where the overlay window appears |
| `overlayPersistent` | boolean | `false` | Keep overlay visible at all times |
| `overlayOpacity` | number | `0.95` | Overlay window transparency |
| `alwaysOnTop` | boolean | `false` | Keep main window above other windows |
| `systemAudio` | boolean | `false` | Capture system audio instead of microphone |
| `microphoneDevice` | string | `''` | Specific microphone device ID (empty = default) |

---

See also: [`hooks.md`](hooks.md) for how `useConfig` integrates with the rest of the app state, and [`rust_backend.md`](rust_backend.md) for how config values like `hotkey` and `systemAudio` are used on the Rust side.
