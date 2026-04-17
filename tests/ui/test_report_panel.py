"""UI tests for the Report Error panel."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from src.config.settings import Settings
from src.i18n import t
from src.ui.main_window import MainWindow
from src.ui.main_window_styles import HEADER_BUTTON, HEADER_BUTTON_ACTIVE


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


class TestReportButton:
    def test_report_button_exists(self, win):
        assert hasattr(win, "report_button")
        assert win.report_button.toolTip() == t("report_error")

    def test_toggle_report_opens_panel(self, win):
        win._toggle_report()
        assert win._report_open
        assert win.content_stack.currentIndex() == 5

    def test_toggle_report_closes_panel(self, win):
        win._toggle_report()  # open
        win._toggle_report()  # close
        assert not win._report_open
        assert win.content_stack.currentIndex() != 5

    def test_report_closes_settings_first(self, win):
        win._toggle_settings()
        assert win._settings_open
        win._toggle_report()
        assert not win._settings_open
        assert win._report_open

    def test_report_closes_models_first(self, win):
        win._toggle_models()
        assert win._models_open
        win._toggle_report()
        assert not win._models_open
        assert win._report_open

    def test_settings_closes_report_first(self, win):
        win._toggle_report()
        assert win._report_open
        win._toggle_settings()
        assert not win._report_open
        assert win._settings_open

    def test_report_button_style_active(self, win):
        win._toggle_report()
        assert win.report_button.styleSheet() == HEADER_BUTTON_ACTIVE

    def test_report_button_style_reset_on_close(self, win):
        win._toggle_report()
        win._toggle_report()
        assert win.report_button.styleSheet() == HEADER_BUTTON


class TestReportPage:
    def test_logs_text_populated(self, win):
        import logging
        logger = logging.getLogger("test.report")
        logger.info("test log line for report")
        win._toggle_report()
        assert "test log line for report" in win.report_logs_text.toPlainText()

    def test_send_button_exists(self, win):
        assert win.send_report_button.text() == t("send_report")

    def test_send_report_success(self, win, monkeypatch):
        import httpx

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        monkeypatch.setattr(httpx, "post", MagicMock(return_value=mock_resp))

        win._toggle_report()
        win._send_report()

        assert win.report_status_label.text() == t("report_sent")
        assert not win.report_status_label.isHidden()

    def test_send_report_failure(self, win, monkeypatch):
        import httpx

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        monkeypatch.setattr(httpx, "post", MagicMock(return_value=mock_resp))

        win._toggle_report()
        win._send_report()

        assert win.report_status_label.text() == t("report_send_failed")

    def test_send_report_network_error(self, win, monkeypatch):
        import httpx

        monkeypatch.setattr(httpx, "post", MagicMock(side_effect=Exception("network error")))

        win._toggle_report()
        win._send_report()

        assert win.report_status_label.text() == t("report_send_failed")



class TestReportDuringStates:
    def test_report_during_recording_returns_to_recording(self, win):
        win.set_recording_state()
        assert win.content_stack.currentIndex() == 1
        win._toggle_report()
        assert win.content_stack.currentIndex() == 5
        win._toggle_report()
        assert win.content_stack.currentIndex() == 1
