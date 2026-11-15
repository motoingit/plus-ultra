"""Windows autostart manager using Windows Registry Run key.

Applies OS concepts:
- Windows User Session Autostart: Registers application executable path in
  HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run.
- Standard Library: Uses python standard-library `winreg` module.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "PLUS-ULTRA"


class WindowsStartupManager:
    """Manages Windows startup registry entry for the current user."""

    def __init__(self, app_name: str = APP_REG_NAME) -> None:
        self._app_name = app_name

    @property
    def is_supported(self) -> bool:
        return winreg is not None

    def is_autostart_enabled(self) -> bool:
        """Check if registry key value exists."""
        if winreg is None:
            return False
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_READ
            ) as key:
                winreg.QueryValueEx(key, self._app_name)
                return True
        except (FileNotFoundError, OSError):
            return False

    def enable_autostart(self) -> bool:
        """Add current Python executable / script to Run key."""
        if winreg is None:
            return False
        try:
            default_appdata = Path.home() / "AppData" / "Local"
            local_appdata = Path(
                os.environ.get("LOCALAPPDATA", default_appdata)
            )
            installed = (
                local_appdata / "Programs" / "plus-ultra" / "plus-ultra.exe"
            )
            if getattr(sys, "frozen", False):
                cmd = f'"{sys.executable}"'
            elif installed.is_file():
                cmd = f'"{installed}"'
            else:
                script = Path(__file__).resolve().parents[2] / "main.py"
                cmd = f'"{sys.executable}" "{script}"'

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REG_RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(key, self._app_name, 0, winreg.REG_SZ, cmd)
            logger.info("Enabled Windows autostart: %s", cmd)
            return True
        except OSError as exc:
            logger.error("Failed to enable Windows autostart: %s", exc)
            return False

    def disable_autostart(self) -> bool:
        """Remove entry from Run key."""
        if winreg is None:
            return False
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REG_RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.DeleteValue(key, self._app_name)
            logger.info("Disabled Windows autostart.")
            return True
        except FileNotFoundError:
            return True
        except OSError as exc:
            logger.error("Failed to disable Windows autostart: %s", exc)
            return False
