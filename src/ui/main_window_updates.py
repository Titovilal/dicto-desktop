"""Self-update flow and error reporting for the main window.

`UpdatesMixin` handles the "Check for updates" / install-in-place flow plus the
"Send report" action. The background `QThread` workers used by the flow live
here too. Mixed into `MainWindow`.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot, QUrl, QThread
from PySide6.QtGui import QDesktopServices

from src.i18n import t
from src.services import routes
from src.ui.main_window_styles import TEXT_DIM, RED


class UpdatesMixin:
    """Updates + error-report actions for MainWindow."""

    # ── Report ──────────────────────────────────────────────

    def _refresh_report_log_view(self):
        """Show the current console log buffer (what gets sent with the report)."""
        from src.utils.logger import get_log_buffer

        logs = "\n".join(get_log_buffer())
        self.report_log_view.setPlainText(logs)
        # Scroll to the latest log line
        sb = self.report_log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _copy_logs(self):
        """Copy the current console log buffer to the clipboard."""
        from PySide6.QtWidgets import QApplication
        from src.utils.logger import get_log_buffer

        logs = "\n".join(get_log_buffer())
        self.report_log_view.setPlainText(logs)
        QApplication.clipboard().setText(logs)
        self.report_status_label.setText(t("logs_copied"))
        self.report_status_label.setStyleSheet("color: #4ade80; font-size: 11px;")
        self.report_status_label.show()

    def _send_report(self):
        import httpx
        from src.utils.logger import get_log_buffer

        self.send_report_button.setEnabled(False)
        self.report_status_label.hide()
        logs = "\n".join(get_log_buffer())
        self.report_log_view.setPlainText(logs)

        try:
            api_key = self.settings.transcription_api_key if self.settings else ""
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            response = httpx.post(
                routes.report(),
                headers=headers,
                json={"logs": logs, "source": "desktop_app"},
                timeout=15.0,
            )
            if response.status_code in (200, 201):
                self.report_status_label.setText(t("report_sent"))
                self.report_status_label.setStyleSheet(
                    "color: #4ade80; font-size: 11px;"
                )
            else:
                self.report_status_label.setText(t("report_send_failed"))
                self.report_status_label.setStyleSheet(
                    f"color: {RED}; font-size: 11px;"
                )
        except Exception:
            self.report_status_label.setText(t("report_send_failed"))
            self.report_status_label.setStyleSheet(f"color: {RED}; font-size: 11px;")

        self.report_status_label.show()
        self.send_report_button.setEnabled(True)

    # ── Updates ─────────────────────────────────────────────

    def _set_update_status(self, text: str, color: str = TEXT_DIM):
        self.update_status_label.setText(text)
        self.update_status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.update_status_label.show()

    @staticmethod
    def _set_button_busy(button, busy: bool):
        """Toggle a button's busy state: disable it and drop the hand cursor so
        it visibly stops inviting clicks while work is in progress."""
        button.setEnabled(not busy)
        button.setCursor(
            Qt.CursorShape.ArrowCursor if busy else Qt.CursorShape.PointingHandCursor
        )

    @Slot()
    def _on_check_updates(self):
        """Check GitHub for a newer release in a background thread."""
        self._set_button_busy(self.check_updates_button, True)
        self.check_updates_button.setText(t("checking_updates"))
        self.update_action_button.hide()
        self._pending_update = None
        self._set_update_status(t("checking_updates"))

        self._update_check_thread = _UpdateCheckThread(self)
        self._update_check_thread.finished_ok.connect(self._on_update_check_done)
        self._update_check_thread.failed.connect(self._on_update_check_failed)
        self._update_check_thread.start()

    @Slot(object)
    def _on_update_check_done(self, info):
        self._set_button_busy(self.check_updates_button, False)
        self.check_updates_button.setText(t("check_for_updates"))
        if not info.available:
            self._set_update_status(t("up_to_date"), "#4ade80")
            return

        self._pending_update = info
        self._set_update_status(
            t("update_available", version=info.latest_version), "#4ade80"
        )

        from src.services.updater import can_self_install

        if can_self_install() and info.asset_url:
            self.update_action_button.setText(t("download_install_update"))
        else:
            self.update_action_button.setText(t("open_release_page"))
        self.update_action_button.show()

    @Slot(str)
    def _on_update_check_failed(self, _msg: str):
        self._set_button_busy(self.check_updates_button, False)
        self.check_updates_button.setText(t("check_for_updates"))
        self._set_update_status(t("update_check_failed"), RED)

    @Slot()
    def _on_update_action(self):
        """Either install the .deb in place or open the release page."""
        info = self._pending_update
        if info is None:
            return

        from src.services.updater import can_self_install

        if not (can_self_install() and info.asset_url):
            QDesktopServices.openUrl(QUrl(info.release_url))
            return

        # In-place download + install via pkexec, on a background thread.
        # Both buttons go busy so the install can't be triggered twice or
        # interrupted by a concurrent re-check.
        self._set_button_busy(self.update_action_button, True)
        self._set_button_busy(self.check_updates_button, True)
        self._set_update_status(t("downloading_update"))

        self._update_install_thread = _UpdateInstallThread(info, self)
        self._update_install_thread.progress.connect(self._set_update_status)
        self._update_install_thread.installed.connect(self._on_update_installed)
        self._update_install_thread.failed.connect(self._on_update_install_failed)
        self._update_install_thread.start()

    @Slot()
    def _on_update_installed(self):
        self._set_update_status(t("update_installed"), "#4ade80")
        self.update_action_button.setText(t("restart_now"))
        self._set_button_busy(self.update_action_button, False)
        # The re-check button stays disabled: the running build is now stale,
        # so checking again would be misleading until the user restarts.
        # Repurpose the action button to restart.
        try:
            self.update_action_button.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass
        self.update_action_button.clicked.connect(self._on_restart_after_update)

    @Slot()
    def _on_restart_after_update(self):
        from src.services.updater import restart_app

        restart_app()

    @Slot(str)
    def _on_update_install_failed(self, _msg: str):
        self._set_button_busy(self.check_updates_button, False)
        self._set_button_busy(self.update_action_button, False)
        self._set_update_status(t("update_failed"), RED)


class _UpdateCheckThread(QThread):
    """Runs the GitHub release check off the UI thread."""

    finished_ok = Signal(object)  # emits UpdateInfo
    failed = Signal(str)

    def run(self):
        from src.services.updater import check_for_update, UpdateError

        try:
            info = check_for_update()
            self.finished_ok.emit(info)
        except UpdateError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class _UpdateInstallThread(QThread):
    """Downloads the release asset and installs it in place, off the UI thread.

    Linux: installs the .deb via pkexec and emits ``installed`` so the UI can
    offer a restart. Windows: ``install_windows_setup`` launches the installer
    and exits the process, so no signal fires in the success case.
    """

    progress = Signal(str)  # status text key already resolved
    installed = Signal()
    failed = Signal(str)

    def __init__(self, info, parent=None):
        super().__init__(parent)
        self._info = info

    def run(self):
        import sys

        from src.services.updater import (
            download_asset,
            install_deb,
            install_windows_setup,
            UpdateError,
        )

        try:
            asset_path = download_asset(self._info.asset_url, self._info.asset_name)
            self.progress.emit(t("installing_update"))
            if sys.platform == "win32":
                # Hands off to the installer and terminates this process.
                install_windows_setup(asset_path)
            else:
                install_deb(asset_path)
                self.installed.emit()
        except UpdateError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
