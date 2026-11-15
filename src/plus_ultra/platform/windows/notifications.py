"""Windows desktop notification provider.

Applies OS concepts:
- Shell notifications via Windows Notification Area / Toast subsystem.
- Graceful degradation: Uses active tray notification when available, with
  PowerShell notification fallback.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any

from plus_ultra.platform.interfaces.notifications import NotificationRequest

logger = logging.getLogger(__name__)


class WindowsDesktopNotifier:
    """Dispatches native notifications on Windows."""

    def __init__(self, tray_instance: Any | None = None) -> None:
        self._tray = tray_instance

    def set_tray(self, tray_instance: Any) -> None:
        """Attach active system tray instance for in-tray notifications."""
        self._tray = tray_instance

    @property
    def is_available(self) -> bool:
        return True

    def send(self, request: NotificationRequest) -> bool:
        """Send notification via system tray balloon or PowerShell toast."""
        # 1. Prefer tray notification if tray is active
        if self._tray is not None and getattr(self._tray, "is_running", False):
            icon = getattr(self._tray, "_icon", None)
            if icon is not None and hasattr(icon, "notify"):
                try:
                    icon.notify(request.message, request.title)
                    logger.info(
                        "Windows tray notification dispatched: %s",
                        request.title,
                    )
                    return True
                except Exception as exc:
                    logger.debug("Tray notification failed: %s", exc)

        # 2. PowerShell Windows Toast Notification Fallback
        mgr = "[Windows.UI.Notifications.ToastNotificationManager"
        ps_script = (
            f"{mgr}, Windows.UI.Notifications, "
            "ContentType = WindowsRuntime] > $null; "
            f"$template = {mgr}]::GetTemplateContent("
            "[Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
            "$textNodes = $template.GetElementsByTagName('text'); "
            f"$t0 = $template.CreateTextNode('{request.title}'); "
            "$textNodes.Item(0).AppendChild($t0) > $null; "
            f"$t1 = $template.CreateTextNode('{request.message}'); "
            "$textNodes.Item(1).AppendChild($t1) > $null; "
            "$toast = [Windows.UI.Notifications.ToastNotification]"
            "::new($template); "
            f"{mgr}]::CreateToastNotifier('{request.app_name}').Show($toast);"
        )

        try:
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    ps_script,
                ],
                check=False,
                capture_output=True,
                timeout=3,
            )
            logger.info(
                "Windows PowerShell notification dispatched: %s", request.title
            )
            return True
        except Exception as exc:
            logger.debug("PowerShell notification fallback failed: %s", exc)
            return False
