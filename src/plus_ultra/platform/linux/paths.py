"""Linux platform path resolution conforming to XDG standards.

Applies OS concepts:
- FreeDesktop XDG Base Directory Specification:
  - Data: $XDG_DATA_HOME/plus-ultra (fallback ~/.local/share/plus-ultra)
  - State/Logs: $XDG_STATE_HOME/plus-ultra (fallback ~/.local/state/plus-ultra)
  - Config: $XDG_CONFIG_HOME/plus-ultra (fallback ~/.config/plus-ultra)
- POSIX Security: Enforces private mode 0o700 (owner-only rwx) on directories.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path


class LinuxPathProvider:
    """Resolves Linux paths adhering to XDG spec and POSIX permissions."""

    def __init__(self, app_name: str = "plus-ultra") -> None:
        self._app_name = app_name

    @property
    def app_name(self) -> str:
        return self._app_name

    def ensure_private_directory(self, path: Path) -> Path:
        """Create directory and enforce mode 0o700 (owner-only access)."""
        with contextlib.suppress(OSError):
            path.mkdir(parents=True, exist_ok=True)
            path.chmod(0o700)
        return path

    def get_data_dir(self) -> Path:
        raw = os.environ.get("XDG_DATA_HOME", "").strip()
        base = Path(raw) if raw else Path.home() / ".local" / "share"
        return self.ensure_private_directory(base / self._app_name)

    def get_state_dir(self) -> Path:
        raw = os.environ.get("XDG_STATE_HOME", "").strip()
        base = Path(raw) if raw else Path.home() / ".local" / "state"
        return self.ensure_private_directory(base / self._app_name)

    def get_config_dir(self) -> Path:
        raw = os.environ.get("XDG_CONFIG_HOME", "").strip()
        base = Path(raw) if raw else Path.home() / ".config"
        return self.ensure_private_directory(base / self._app_name)

    def get_db_path(self) -> Path:
        return self.get_data_dir() / "plus-ultra.sqlite3"

    def get_log_path(self) -> Path:
        return self.get_state_dir() / "launcher.log"

    def get_user_settings_path(self) -> Path:
        return self.get_config_dir() / "user-settings.json"
