"""Configuration and XDG base directory resolution for PLUS-ULTRA.

Applies OS concepts:
- XDG Base Directory specification for separating data, state, and runtime.
- POSIX filesystem security: private directories created with mode 0o700
  (rwx------) to protect sensitive user notes, tasks, and credentials.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path

# Shared application constants
APP_NAME = "plus-ultra"
DB_FILENAME = "plus-ultra.sqlite3"
LOG_FILENAME = "launcher.log"


def _ensure_private_directory(path: Path) -> Path:
    """Ensure directory exists and enforce private mode 0o700 (owner only).

    OS concept: Filesystem permissions. 0o700 ensures that other local users
    on a shared Linux workstation cannot read or modify user task data/logs.
    """
    path.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        path.chmod(0o700)
    return path


def get_data_dir() -> Path:
    """Resolve and create application data directory.

    Conforms to the XDG Base Directory specification:
    - $XDG_DATA_HOME/plus-ultra
    - Fallback: ~/.local/share/plus-ultra
    """
    raw_env = os.environ.get("XDG_DATA_HOME", "").strip()
    base_dir = Path(raw_env) if raw_env else Path.home() / ".local" / "share"
    target_dir = base_dir / APP_NAME
    return _ensure_private_directory(target_dir)


def get_state_dir() -> Path:
    """Resolve and create application state directory for logs.

    Conforms to the XDG Base Directory specification:
    - $XDG_STATE_HOME/plus-ultra
    - Fallback: ~/.local/state/plus-ultra
    """
    raw_env = os.environ.get("XDG_STATE_HOME", "").strip()
    base_dir = Path(raw_env) if raw_env else Path.home() / ".local" / "state"
    target_dir = base_dir / APP_NAME
    return _ensure_private_directory(target_dir)


def get_db_path() -> Path:
    """Return path to SQLite database file in data directory."""
    return get_data_dir() / DB_FILENAME


def get_log_path() -> Path:
    """Return path to launcher log file in state directory."""
    return get_state_dir() / LOG_FILENAME
