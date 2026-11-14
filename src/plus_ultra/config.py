"""Configuration and platform directory resolution for PLUS-ULTRA.

Applies OS concepts:
- Platform Abstraction Layer delegation: Resolves paths according to host OS
  (Windows %LOCALAPPDATA% / %APPDATA% vs Linux XDG Base Directory specification).
- Backward compatibility: Preserves public config functions while delegating
  underlying resolution to PlatformServices.
"""

from __future__ import annotations

import importlib.metadata
import importlib.resources
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from plus_ultra.platform.factory import PlatformServices

# Shared application constants
APP_NAME = "plus-ultra"
DB_FILENAME = "plus-ultra.sqlite3"
LOG_FILENAME = "launcher.log"
USER_SETTINGS_FILENAME = "user-settings.json"

_platform_services: PlatformServices | None = None


def get_platform_services() -> PlatformServices:
    """Return cached singleton platform services."""
    global _platform_services
    if _platform_services is None:
        from plus_ultra.platform.factory import create_platform_services

        _platform_services = create_platform_services()
    return _platform_services


def get_data_dir() -> Path:
    """Resolve and return persistent application data directory."""
    return get_platform_services().paths.get_data_dir()


def get_state_dir() -> Path:
    """Resolve and return application state directory for logs and locks."""
    return get_platform_services().paths.get_state_dir()


def get_config_dir() -> Path:
    """Resolve and return application configuration directory."""
    return get_platform_services().paths.get_config_dir()


def get_db_path() -> Path:
    """Return path to SQLite database file in data directory."""
    return get_platform_services().paths.get_db_path()


def get_log_path() -> Path:
    """Return path to launcher log file in state directory."""
    return get_platform_services().paths.get_log_path()


def get_user_settings_path() -> Path:
    """Return path to user settings JSON file in configuration directory."""
    return get_platform_services().paths.get_user_settings_path()


def get_app_version() -> str:
    """Return installed application package version with fallback."""
    try:
        return importlib.metadata.version(APP_NAME)
    except importlib.metadata.PackageNotFoundError:
        return "0.1.0"


def get_metadata() -> dict[str, Any]:
    """Load static application metadata from packaged resources."""
    resources = importlib.resources.files("plus_ultra.resources")
    ref = resources.joinpath("data", "metadata.json")
    if not ref.is_file():
        ref = resources.joinpath("metadata.json")
    with ref.open("r", encoding="utf-8") as f:
        return json.load(f)
