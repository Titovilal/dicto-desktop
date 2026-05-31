# Endpoints Used

## What It Does
This document lists every HTTP endpoint the desktop app calls, what it sends, what
it expects back, and everything that can go wrong on each one. There are two hosts:

- **Dicto API** — `https://dicto.up.railway.app` (overridable via `DICTO_API_URL`).
  Handles transcription, transformation, presets and bug reports. All
  requests authenticate with `Authorization: Bearer <api_key>`.
- **GitHub API** — `https://api.github.com` (repo overridable via `DICTO_UPDATE_REPO`).
  Used only by the self-updater to find the latest release.

Code: `src/services/transcriber.py`, `src/services/updater.py`,
`src/ui/main_window.py` (report sending).

---

## Dicto API

All Dicto endpoints share the same auth and the same error mapping (see
[Common error handling](#common-error-handling)). The HTTP client timeout is
**30s** for transcribe/transform/presets and **15s** for report.

### POST `/api/transcribe` — audio → text
- **Auth:** `Authorization: Bearer <api_key>`
- **Body:** `multipart/form-data`
  - `file`: the audio file (MIME guessed from extension: wav/mp3/webm/m4a/ogg, defaults to `audio/wav`)
  - `model`: transcription model (e.g. `v3-turbo`)
  - `source`: `mic_app`
  - `language`: optional (omitted only if unset; `auto` is normalized to `es`)
- **Pre-flight validation (client-side, before the request):**
  - File missing → `TranscriptionError`
  - File > 25 MB → `AudioTooLongError`
  - File < 0.001 MB (~no audio recorded) → `AudioTooShortError`
- **Success (200):** JSON `{ text, id, language, duration }`. Empty `text` →
  `TranscriptionError("API returned empty transcription")`. `id` is stored as
  `last_transcription_id` for later linking in transform.
- **Retries:** up to 3 attempts with exponential backoff (2s, 4s) on
  `RateLimitError` and generic `TranscriptionError`. `APIKeyError` is **not** retried.

### POST `/api/transform` — reformat text via LLM
- **Auth:** `Authorization: Bearer <api_key>`, `Content-Type: application/json`
- **Body (JSON):**
  - `messages`: chat array (optional `system` instructions + `user` text)
  - `model`: the transformation model (default `qwen/qwen3-32b`)
  - `transcription_id`: optional, links the transform to a prior transcription
- **Success (200):** JSON `{ choices: [{ message: { content } }] }`. Missing/empty
  content → `TranscriptionError("Transform API returned empty result")`.
- **Retries:** none (single attempt).

### GET `/api/presets` — fetch the user's favorite presets
- **Auth:** `Authorization: Bearer <api_key>`
- **Success (200):** JSON `{ presets: [{ id, name, instructions }] }`.
- **Failure behavior:** best-effort — any non-200 status or exception is logged
  as a warning and returns an **empty list** (never raises).

### POST `/api/report` — send logs / bug report
- **Auth:** `Authorization: Bearer <api_key>`, `Content-Type: application/json`
- **Body (JSON):** `{ logs, source: "desktop_app" }` — `logs` is the in-memory
  console log buffer.
- **Success (200 or 201):** UI shows "report sent".
- **Failure behavior:** any other status or exception → UI shows "report failed";
  no exception propagates.

### Common error handling
Applies to transcribe / transform (and is the basis for presets/report
status). Mapped in `Transcriber._handle_error_response`:

| HTTP status | Raised exception | Notes |
|-------------|------------------|-------|
| 200 | — | success |
| 401 | `APIKeyError` | invalid or missing API key; **not retried** |
| 429 | `RateLimitError` | spending/rate limit; retried (transcribe only) |
| other | `TranscriptionError(f"API error ({status}): {msg}")` | `msg` parsed from JSON `error.message` / `error`, falling back to first 200 chars of body |

Transport-level failures (all Dicto endpoints):
- `httpx.TimeoutException` → `TranscriptionError("… request timeout …")`
- `httpx.RequestError` → `TranscriptionError(f"Network error: {e}")`
- any other exception → `TranscriptionError(f"Unexpected error …: {e}")`

---

## GitHub API (self-update)

### GET `/repos/{repo}/releases/latest`
- **Host:** `https://api.github.com` · repo defaults to `Titovilal/dicto-desktop`.
- **Headers:** `Accept: application/vnd.github+json`; `Authorization: Bearer <GITHUB_TOKEN>`
  added only if the env var is set.
- **Timeout:** 15s (default).
- **Success:** parses `tag_name` (or `name`) as the latest version, `html_url` as
  the release page, and scans `assets` for the first `.deb` to get its
  `browser_download_url`. Compares against the running version via `is_newer`.
- **Failures:**
  - Network / HTTP error (`raise_for_status`) or JSON parse error →
    `UpdateError("Could not reach update server: …")`
  - No version tag in payload → `UpdateError("Release metadata did not include a version tag")`

### GET `<browser_download_url>` (downloading the `.deb` asset)
- Streamed download (64 KB chunks) to a temp file, `follow_redirects=True`,
  timeout 120s.
- Any failure → `UpdateError("Failed to download update: …")`.
- Note: the install step (`pkexec apt-get install`) is local, not an endpoint —
  see [`services.md`](services.md).

---

**Best practices:** keep it short, focus on the big picture, use plain language.
See [`services.md`](services.md) for the surrounding transcriber/updater services
and [`core_architecture.md`](core_architecture.md) for how the controller drives them.
