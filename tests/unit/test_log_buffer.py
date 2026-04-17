"""Unit tests for the in-memory log buffer."""

from __future__ import annotations

import logging

from src.utils.logger import setup_logging, get_log_buffer, _log_buffer


class TestLogBuffer:
    def setup_method(self):
        _log_buffer.clear()
        setup_logging(logging.DEBUG)

    def test_buffer_captures_log_lines(self):
        logger = logging.getLogger("test.buffer")
        logger.info("hello from test")
        lines = get_log_buffer()
        assert any("hello from test" in line for line in lines)

    def test_buffer_returns_list_copy(self):
        logger = logging.getLogger("test.copy")
        logger.warning("warn msg")
        buf1 = get_log_buffer()
        buf2 = get_log_buffer()
        assert buf1 == buf2
        assert buf1 is not buf2

    def test_buffer_respects_max_size(self):
        logger = logging.getLogger("test.max")
        for i in range(600):
            logger.debug(f"line {i}")
        lines = get_log_buffer()
        assert len(lines) == 500
        # Oldest lines should have been dropped
        assert "line 0" not in lines[-1]

    def test_buffer_empty_initially(self):
        assert get_log_buffer() == []

    def test_multiple_levels_captured(self):
        logger = logging.getLogger("test.levels")
        logger.debug("dbg")
        logger.info("inf")
        logger.warning("wrn")
        logger.error("err")
        lines = get_log_buffer()
        assert len(lines) >= 4
        texts = "\n".join(lines)
        assert "dbg" in texts
        assert "inf" in texts
        assert "wrn" in texts
        assert "err" in texts
