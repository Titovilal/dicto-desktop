# Endpoints Used

## What It Does
This document is the HTTP contract for every endpoint the desktop app calls: what
each one sends, what it returns, and the status codes it can answer with. There are
two hosts:

- **Dicto API** - `https://dicto.up.railway.app` (overridable via `DICTO_API_URL`).
  Handles transcription, transformation, presets and bug reports. Every request
  authenticates with `Authorization: Bearer <api_key>`.
- **GitHub API** - `https://api.github.com` (repo overridable via `DICTO_UPDATE_REPO`).
  Used only by the self-updater to find the latest release.

---

## Dicto API

All Dicto endpoints authenticate with `Authorization: Bearer <api_key>` and share
the same error responses (see [Common errors](#common-errors)).

### POST `/api/v1/transcribe` - audio → text
- **Request** - `multipart/form-data`:
  ```
  file:     <recording.wav>   # wav/mp3/webm/m4a/ogg
  model:    v3-turbo
  source:   mic_app
  language: es                # optional; ISO 639-1 code or "auto" for server-side autodetection
  ```
- **Response (200):**
  ```json
  { "text": "hola qué tal" }
  ```

### POST `/api/v1/transform` - reformat text via LLM
- **Request (JSON):**
  ```json
  {
    "text": "hola qué tal",
    "instructions": "format as a polite email",
    "model": "qwen/qwen3-32b"
  }
  ```
- **Response (200):**
  ```json
  { "text": "Hola, ¿qué tal? Un saludo." }
  ```

### GET `/api/v1/presets` - fetch the user's favorite presets
- **Response (200):**
  ```json
  {
    "presets": [
      { "name": "Email", "instructions": "format as a polite email" }
    ]
  }
  ```

### POST `/api/v1/report` - send logs / bug report
- **Request (JSON):**
  ```json
  { "logs": "2026-05-31 12:00:00 INFO …", "source": "desktop_app" }
  ```
- **Response:** `200` or `201` on success.

### Common errors
The per-endpoint sections above only show the `200`/`201` success body. Every other
status is shared across all Dicto endpoints and answers with the same error shape:

| HTTP status | Meaning |
|-------------|---------|
| 200 / 201 | success |
| 401 | invalid or missing API key |
| 429 | rate / spending limit exceeded |
| 4xx / 5xx | other error |

Error body (any non-2xx status) always has the same shape:
```json
{ "error": { "message": "invalid api key" } }
```

---

## GitHub API (self-update)

### GET `/repos/{repo}/releases/latest`
- **Host:** `https://api.github.com` · repo defaults to `Titovilal/dicto-desktop`.
- **Headers:** `Accept: application/vnd.github+json`; `Authorization: Bearer <GITHUB_TOKEN>`
  sent only if the env var is set.
- **Response (200):** standard GitHub release object - `tag_name`/`name` is the
  latest version, `html_url` the release page, and `assets[]` carry the
  `browser_download_url` for each file (the `Dicto-<ver>-setup.exe` installer is
  the one consumed).

### GET `<browser_download_url>` (downloading the installer asset)
- Streamed download with redirects followed; returns the binary asset.

---

See [`services.md`](services.md) for how the transcriber/updater services wrap
these calls (timeouts, retries, error mapping, client-side validation), and
[`core_architecture.md`](core_architecture.md) for how the controller drives them.
