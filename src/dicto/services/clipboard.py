"""Clipboard service — write/read text, the fallback delivery path.

The clipboard is where a transcript lands when the user hasn't asked for cursor
injection, or when injection isn't possible (see ``services/injector`` and
``core/result_router``). It is also the mechanism injection uses under the hood
(copy → Ctrl+V).

Backends, tried in order:
- **win32** (``win32clipboard`` from pywin32) — direct, no extra dependency
  since PySide6 already pulls pywin32 on Windows; this is the production path;
- **Qt** (``QApplication.clipboard()``) — used when win32 isn't available but a
  QApplication exists;
- **noop** — headless/tests: a no-op that remembers the last value so logic that
  reads back what it wrote still works.

The backend is resolved lazily on first use, so importing this module never
requires Windows or a display — unit tests of the pure routing logic stay
headless.
"""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class _Backend(Protocol):
    def write(self, text: str) -> None: ...
    def read(self) -> str: ...


class _Win32Backend:
    """Direct Windows clipboard via pywin32."""

    def __init__(self) -> None:
        import win32clipboard  # noqa: F401 — probe availability at construction

        self._mod = win32clipboard

    def write(self, text: str) -> None:
        self._mod.OpenClipboard()
        try:
            self._mod.EmptyClipboard()
            self._mod.SetClipboardText(text, self._mod.CF_UNICODETEXT)
        finally:
            self._mod.CloseClipboard()

    def read(self) -> str:
        self._mod.OpenClipboard()
        try:
            try:
                return self._mod.GetClipboardData(self._mod.CF_UNICODETEXT) or ""
            except TypeError:
                return ""
        finally:
            self._mod.CloseClipboard()


class _QtBackend:
    """Qt clipboard — only usable when a QApplication is already running."""

    def __init__(self) -> None:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            raise RuntimeError("no QApplication")
        self._app: QApplication = app  # type: ignore[assignment]

    def write(self, text: str) -> None:
        self._app.clipboard().setText(text)

    def read(self) -> str:
        return self._app.clipboard().text() or ""


class _NoopBackend:
    """Headless fallback that just remembers the last written value."""

    def __init__(self) -> None:
        self._value = ""

    def write(self, text: str) -> None:
        self._value = text

    def read(self) -> str:
        return self._value


def _select_backend() -> _Backend:
    for factory in (_Win32Backend, _QtBackend):
        try:
            backend = factory()
            logger.debug("clipboard backend: %s", factory.__name__)
            return backend
        except Exception:  # noqa: BLE001 — try the next backend
            continue
    logger.warning("no real clipboard backend; using no-op")
    return _NoopBackend()


class Clipboard:
    """Thin clipboard wrapper with a lazily-resolved backend.

    Inject a ``backend`` to override selection (tests). All operations swallow
    backend errors and report success/failure so a clipboard hiccup never takes
    down a delivery.
    """

    def __init__(self, backend: _Backend | None = None) -> None:
        self._backend = backend

    def _ensure(self) -> _Backend:
        if self._backend is None:
            self._backend = _select_backend()
        return self._backend

    def copy(self, text: str) -> bool:
        """Put ``text`` on the clipboard. Returns True on success."""
        if not text:
            logger.debug("ignoring empty clipboard copy")
            return False
        try:
            self._ensure().write(text)
            preview = text[:50] + ("…" if len(text) > 50 else "")
            logger.info("copied to clipboard: %s", preview)
            return True
        except Exception:  # noqa: BLE001
            logger.error("failed to copy to clipboard", exc_info=True)
            return False

    def paste(self) -> str:
        """Read the clipboard text. Empty string on error."""
        try:
            return self._ensure().read()
        except Exception:  # noqa: BLE001
            logger.error("failed to read clipboard", exc_info=True)
            return ""
