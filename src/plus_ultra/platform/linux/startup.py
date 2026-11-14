"""Linux autostart manager using XDG Autostart .desktop entries.

Applies OS concepts:
- FreeDesktop XDG Autostart Specification:
  - ~/.config/autostart/plus-ultra.desktop launched on session login.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

DESKTOP_ENTRY_TEMPLATE = """[Desktop Entry]
Type=Application
Version=1.0
Name=PLUS-ULTRA
Comment=Floating desktop assistant
Exec={exec_cmd}
Icon=plus-ultra
Terminal=false
Categories=Utility;ProjectManagement;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""


class LinuxStartupManager:
    """Manages XDG session autostart .desktop file in ~/.config/autostart."""

    def __init__(self, filename: str = "plus-ultra.desktop") -> None:
        self._filename = filename

    @property
    def is_supported(self) -> bool:
        return True

    def _get_autostart_file(self) -> Path:
        raw_config = os.environ.get("XDG_CONFIG_HOME", "").strip()
        base = Path(raw_config) if raw_config else Path.home() / ".config"
        autostart_dir = base / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        return autostart_dir / self._filename

    def is_autostart_enabled(self) -> bool:
        return self._get_autostart_file().is_file()

    def enable_autostart(self) -> bool:
        """Write .desktop file with valid executable command."""
        target = self._get_autostart_file()
        try:
            installed = Path.home() / ".local" / "bin" / "plus-ultra"
            if installed.is_file():
                cmd = str(installed)
            elif getattr(sys, "frozen", False):
                cmd = sys.executable
            else:
                cmd = f"{sys.executable} -m plus_ultra.main"

            content = DESKTOP_ENTRY_TEMPLATE.format(exec_cmd=cmd)
            target.write_text(content, encoding="utf-8")
            target.chmod(0o755)
            logger.info("Created Linux autostart desktop entry at %s", target)
            return True
        except OSError as exc:
            logger.error("Failed to enable Linux autostart: %s", exc)
            return False

    def disable_autostart(self) -> bool:
        """Delete .desktop autostart entry."""
        target = self._get_autostart_file()
        try:
            if target.is_file():
                target.unlink()
                logger.info("Removed Linux autostart desktop entry at %s",
                            target)
            return True
        except OSError as exc:
            logger.error("Failed to disable Linux autostart: %s", exc)
            return False
