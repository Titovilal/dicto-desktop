# Tauri Configuration

## What It Does
This covers how the Tauri 2 app is configured: window definitions, security capabilities, plugins, and the Rust dependency manifest. It controls what the app looks like, what system permissions it requests, and which Tauri plugins are available to the frontend.

## Main Files
- `src-tauri/tauri.conf.json` — Main Tauri config: app identity, window definitions, build commands, and bundle settings
- `src-tauri/capabilities/default.json` — Capability file that grants permissions to both windows (which Tauri plugin APIs are allowed)
- `src-tauri/Cargo.toml` — Rust package manifest listing all Tauri plugins and native dependencies

## Flow
1. On launch, Tauri reads `tauri.conf.json` to create the two windows: `main` (800×600, standard) and `overlay` (280×80, borderless, transparent, always-on-top, initially hidden)
2. Tauri enforces the capability defined in `capabilities/default.json`, which applies to both windows and grants access to plugins like store, global shortcuts, clipboard, notifications, and OS info
3. The Rust side loads all plugins declared in `Cargo.toml` and registers them at startup so the frontend can invoke their commands

## Windows
| Label | Size | Notes |
|-------|------|-------|
| `main` | 800×600 | Default decorated window, no fixed position |
| `overlay` | 280×80 | Borderless, transparent, always-on-top, hidden at start, routes to `#/overlay` |

## Plugins Used
- **store** — Persistent key-value storage for app config and history
- **global-shortcut** — Register/unregister system-wide hotkeys
- **clipboard-manager** — Read and write text to the system clipboard
- **shell** — Open external URLs via the OS default browser
- **notification** — Request permission and show desktop notifications
- **os** — Detect the current platform (Windows/macOS) for platform-specific behavior
- **opener** — Open files or URLs from within the app

## Key Capabilities Granted
The `default` capability applies to both `main` and `overlay` windows and includes:
- Window management: show, hide, set position, set focus, close, start dragging
- Full store read/write/save/load access
- Global shortcut register/unregister
- Clipboard read and write
- OS platform detection
- Notifications

## Bundle & Build
- **Identifier:** `com.dicto.desktop`
- **Targets:** all platforms
- **Dev:** `pnpm dev` → `http://localhost:1420`
- **Build:** `pnpm build` → `../dist`
- **CSP:** disabled (`null`) for development flexibility

---

See [`rust_backend.md`](rust_backend.md) for how Rust commands use these plugins, and [`config_and_store.md`](config_and_store.md) for how the store plugin is used to persist configuration.
