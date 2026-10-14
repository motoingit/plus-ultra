"""Configuration and XDG base directory resolution for PLUS-ULTRA.

Applies OS concepts:
- XDG Base Directory specification for separating data, state, and runtime.
- POSIX filesystem security: private directories created with mode 0o700
  (rwx------) to protect sensitive user notes, tasks, and credentials.
"""

from __future__ import annotations

import contextlib
import importlib.metadata
import importlib.resources
import json
import os
from pathlib import Path
from typing import Any

# Shared application constants
APP_NAME = "plus-ultra"
DB_FILENAME = "plus-ultra.sqlite3"
LOG_FILENAME = "launcher.log"
USER_SETTINGS_FILENAME = "user-settings.json"


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


def get_config_dir() -> Path:
    """Resolve and create application configuration directory.

    Conforms to the XDG Base Directory specification:
    - $XDG_CONFIG_HOME/plus-ultra
    - Fallback: ~/.config/plus-ultra
    """
    raw_env = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base_dir = Path(raw_env) if raw_env else Path.home() / ".config"
    target_dir = base_dir / APP_NAME
    return _ensure_private_directory(target_dir)


def get_user_settings_path() -> Path:
    """Return path to user settings JSON file in configuration directory."""
    return get_config_dir() / USER_SETTINGS_FILENAME


def get_app_version() -> str:
    """Return installed application package version with fallback."""
    try:
        return importlib.metadata.version(APP_NAME)
    except importlib.metadata.PackageNotFoundError:
        return "0.1.0"


def get_metadata() -> dict[str, Any]:
    """Load static application metadata from packaged resources."""
    ref = importlib.resources.files("plus_ultra.resources").joinpath(
        "metadata.json"
    )
    with ref.open("r", encoding="utf-8") as f:
        return json.load(f)
