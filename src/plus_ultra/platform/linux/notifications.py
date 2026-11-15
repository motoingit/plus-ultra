"""Linux desktop notification provider using notify-send.

Applies OS concepts:
- Invokes FreeDesktop notification server via notify-send utility.
- Security: Always uses argument list with subprocess (never shell=True).
- Graceful degradation if notify-send binary is missing or times out.
"""

from __future__ import annotations

import logging
import shutil
import subprocess

from plus_ultra.platform.interfaces.notifications import NotificationRequest

logger = logging.getLogger(__name__)


class LinuxDesktopNotifier:
    """Dispatches notifications via FreeDesktop notify-send on Linux."""

    @property
    def is_available(self) -> bool:
        return shutil.which("notify-send") is not None

    def send(self, request: NotificationRequest) -> bool:
        """Execute notify-send with arguments."""
        executable = shutil.which("notify-send")
        if not executable:
            logger.warning(
                "notify-send executable not found; notification skipped."
            )
            return False

        cmd = [
            executable,
            "-a",
            request.app_name,
            "-u",
            request.urgency.value,
            "-t",
            str(request.timeout_ms),
            request.title,
            request.message,
        ]
        if request.icon_path:
            cmd.extend(["-i", request.icon_path])

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=3,
            )
            logger.info(
                "Linux desktop notification dispatched: %s", request.title
            )
            return True
        except (subprocess.SubprocessError, OSError) as exc:
            logger.warning(
                "Failed to dispatch Linux desktop notification: %s", exc
            )
            return False
