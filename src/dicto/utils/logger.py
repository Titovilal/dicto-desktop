"""Logging setup with an in-memory ring buffer for bug reports.

Logs go to three places: stdout (dev), a rotating file under
``%APPDATA%\\dicto\\logs`` (installed), and a 500-line in-memory ring buffer the
bug-report panel reads from (``get_log_buffer``).
"""

from __future__ import annotations

import logging
import sys
from collections import deque
from logging.handlers import RotatingFileHandler

from dicto.utils.platform import get_logs_dir

# In-memory ring buffer of recent formatted log lines, surfaced in bug reports.
_log_buffer: deque[str] = deque(maxlen=500)

_FILE_FMT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_CONSOLE_FMT = "%(levelname)s:\t%(message)s"


class _MemoryHandler(logging.Handler):
    """Stores formatted log lines in the module-level ring buffer."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            _log_buffer.append(self.format(record))
        except Exception:  # noqa: BLE001 — logging must never raise
            pass


def get_log_buffer() -> list[str]:
    """Snapshot of recent log lines, oldest first."""
    return list(_log_buffer)


def get_log_text() -> str:
    """Recent log lines joined into one string, ready to send as a report."""
    return "\n".join(_log_buffer)


def setup_logging(level: int = logging.INFO, *, to_file: bool = True) -> None:
    """Configure the root logger. Idempotent — clears existing handlers first."""
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(_CONSOLE_FMT))
    root.addHandler(console)

    mem = _MemoryHandler()
    mem.setFormatter(logging.Formatter(_FILE_FMT))
    root.addHandler(mem)

    if to_file:
        try:
            log_path = get_logs_dir() / "dicto.log"
            file_handler = RotatingFileHandler(
                log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
            )
            file_handler.setFormatter(logging.Formatter(_FILE_FMT))
            root.addHandler(file_handler)
        except Exception:  # noqa: BLE001 — never let logging setup crash startup
            root.warning("could not attach file log handler", exc_info=True)


def get_logger(name: str) -> logging.Logger:
    """Module logger (pass ``__name__``)."""
    return logging.getLogger(name)
