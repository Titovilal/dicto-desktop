"""UI tests for the Report Error section (lives inside the Settings panel)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.config.settings import Settings
from src.i18n import t
from src.ui.main_window import MainWindow


@pytest.fixture
def settings(tmp_path):
    s = Settings(config_path=str(tmp_path / "config.yaml"))
    s.transcription_api_key = "sk-test"
    return s


@pytest.fixture
def win(settings, qtbot):
    w = MainWindow(settings=settings)
    qtbot.addWidget(w)
    return w


class TestReportWidgets:
    def test_report_widgets_exist(self, win):
        assert hasattr(win, "report_log_view")
        assert hasattr(win, "send_report_button")
        assert hasattr(win, "report_status_label")

    def test_send_button_label(self, win):
        assert win.send_report_button.text() == t("send_report")

    def test_copy_logs_button_exists(self, win):
        assert hasattr(win, "copy_logs_button")
        assert win.copy_logs_button.text() == t("copy_logs")


class TestCopyLogs:
    def test_copy_logs_puts_buffer_on_clipboard(self, win):
        import logging
        from src.utils.logger import setup_logging
        from PySide6.QtWidgets import QApplication

        setup_logging()
        logging.getLogger("test.copy").info("copy me to clipboard")
        win._copy_logs()
        assert "copy me to clipboard" in QApplication.clipboard().text()
        assert win.report_status_label.text() == t("logs_copied")
        assert not win.report_status_label.isHidden()

    def test_report_lives_in_settings_page(self, win):
        # Opening settings shows the page that contains the report section
        win._toggle_settings()
        assert win._settings_open
        assert win.content_stack.currentIndex() == 3


class TestReportLogView:
    def test_logs_populated_on_open(self, win):
        import logging
        from src.utils.logger import setup_logging

        # Install the in-memory log handler that feeds the report log view.
        setup_logging()
        logger = logging.getLogger("test.report")
        logger.info("test log line for report")
        win._toggle_settings()
        assert "test log line for report" in win.report_log_view.toPlainText()


class TestSendReport:
    def test_send_report_success(self, win, monkeypatch):
        import httpx

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        monkeypatch.setattr(httpx, "post", MagicMock(return_value=mock_resp))

        win._toggle_settings()
        win._send_report()

        assert win.report_status_label.text() == t("report_sent")
        assert not win.report_status_label.isHidden()

    def test_send_report_failure(self, win, monkeypatch):
        import httpx

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        monkeypatch.setattr(httpx, "post", MagicMock(return_value=mock_resp))

        win._toggle_settings()
        win._send_report()

        assert win.report_status_label.text() == t("report_send_failed")

    def test_send_report_network_error(self, win, monkeypatch):
        import httpx

        monkeypatch.setattr(
            httpx, "post", MagicMock(side_effect=Exception("network error"))
        )

        win._toggle_settings()
        win._send_report()

        assert win.report_status_label.text() == t("report_send_failed")
