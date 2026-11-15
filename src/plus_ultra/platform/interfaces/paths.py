"""Path resolution and filesystem security interface.

Applies OS concepts:
- Filesystem hierarchy standards: XDG specifications on Linux vs %APPDATA%
  and %LOCALAPPDATA% on Windows.
- Directory permission isolation per operating system standards.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class PathProvider(Protocol):
    """Protocol for platform-specific directory and file path resolution."""

    @property
    def app_name(self) -> str:
        """Application namespace directory identifier."""
        ...

    def get_data_dir(self) -> Path:
        """Resolve persistent application data directory (SQLite DB, etc.)."""
        ...

    def get_state_dir(self) -> Path:
        """Resolve ephemeral state directory (logs, run-locks, etc.)."""
        ...

    def get_config_dir(self) -> Path:
        """Resolve user configuration directory (user-settings.json)."""
        ...

    def get_db_path(self) -> Path:
        """Resolve absolute path to the SQLite database file."""
        ...

    def get_log_path(self) -> Path:
        """Resolve absolute path to the application log file."""
        ...

    def get_user_settings_path(self) -> Path:
        """Resolve absolute path to user settings JSON file."""
        ...

    def ensure_private_directory(self, path: Path) -> Path:
        """Ensure directory exists with appropriate owner-only ACL/mode."""
        ...
