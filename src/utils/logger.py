"""
Logging configuration for Dicto application.
"""

import logging
import sys
from collections import deque

# In-memory ring buffer for recent log records
_log_buffer: deque[str] = deque(maxlen=500)


class _MemoryHandler(logging.Handler):
    """Handler that stores formatted log lines in a ring buffer."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            _log_buffer.append(self.format(record))
        except Exception:
            pass


def get_log_buffer() -> list[str]:
    """Return a snapshot of the recent log lines."""
    return list(_log_buffer)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (default: INFO)
    """
    # Format: LEVEL - filename - message
    formatter = logging.Formatter(fmt="%(levelname)s:\t%(message)s")

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Memory handler
    mem_handler = _MemoryHandler()
    mem_handler.setFormatter(
        logging.Formatter(fmt="%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.addHandler(mem_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
