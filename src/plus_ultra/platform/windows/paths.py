"""Windows platform path resolution.

Applies OS concepts:
- Windows Standard Filesystem Paths:
  - Persistent user data: Path.home() / "AppData" / "Local" / "plus-ultra"
  - Ephemeral state and logs: Path.home() / "AppData" / "Local" / "plus-ultra" / "state"
  - Roaming configuration: Path.home() / "AppData" / "Roaming" / "plus-ultra"
- Respects Path.home() virtualization (enabling isolated test environments).
- Respects explicit environment overrides (XDG_DATA_HOME, etc.).
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path


class WindowsPathProvider:
    """Resolves Windows paths following Microsoft application standards."""

    def __init__(self, app_name: str = "plus-ultra") -> None:
        self._app_name = app_name

    @property
    def app_name(self) -> str:
        return self._app_name

    def _get_local_appdata(self) -> Path:
        raw_xdg = os.environ.get("XDG_DATA_HOME", "").strip()
        if raw_xdg:
            return Path(raw_xdg)
        return Path.home() / "AppData" / "Local"

    def _get_state_base(self) -> Path:
        raw_xdg = os.environ.get("XDG_STATE_HOME", "").strip()
        if raw_xdg:
            return Path(raw_xdg)
        return self._get_local_appdata() / self._app_name / "state"

    def _get_roaming_appdata(self) -> Path:
        raw_xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
        if raw_xdg:
            return Path(raw_xdg)
        return Path.home() / "AppData" / "Roaming"

    def ensure_private_directory(self, path: Path) -> Path:
        """Create directory if not present, suppressing permission/sandbox errors."""
        with contextlib.suppress(OSError):
            path.mkdir(parents=True, exist_ok=True)
        return path

    def get_data_dir(self) -> Path:
        raw_xdg = os.environ.get("XDG_DATA_HOME", "").strip()
        if raw_xdg:
            target = Path(raw_xdg) / self._app_name
        else:
            target = self._get_local_appdata() / self._app_name
        return self.ensure_private_directory(target)

    def get_state_dir(self) -> Path:
        raw_xdg = os.environ.get("XDG_STATE_HOME", "").strip()
        if raw_xdg:
            target = Path(raw_xdg) / self._app_name
        else:
            target = self._get_state_base()
        return self.ensure_private_directory(target)

    def get_config_dir(self) -> Path:
        raw_xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
        if raw_xdg:
            target = Path(raw_xdg) / self._app_name
        else:
            target = self._get_roaming_appdata() / self._app_name
        return self.ensure_private_directory(target)

    def get_db_path(self) -> Path:
        return self.get_data_dir() / "plus-ultra.sqlite3"

    def get_log_path(self) -> Path:
        return self.get_state_dir() / "launcher.log"

    def get_user_settings_path(self) -> Path:
        return self.get_config_dir() / "user-settings.json"
