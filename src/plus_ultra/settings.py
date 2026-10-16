"""Settings management for PLUS-ULTRA.

Applies OS concepts:
- Defense in depth and filesystem security: User settings stored in private
  XDG config directory with mode 0o600 (owner read/write only).
- Crash consistency and atomic file updates: Writing via temporary file in
  the same filesystem directory followed by atomic replace (POSIX rename).
- Fault tolerance and defensive recovery: Corrupted settings files are
  quarantined with a timestamped suffix (.bad-<timestamp>) rather than
  crashing or silently deleting user data.
"""

from __future__ import annotations

import contextlib
import importlib.resources
import json
import logging
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from plus_ultra import config

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_cached_effective: dict[str, Any] | None = None


def load_default_settings() -> dict[str, Any]:
    """Load default settings packaged with the application."""
    res = importlib.resources.files("plus_ultra.resources")
    data_ref = res.joinpath("data", "default-settings.json")
    if data_ref.is_file():
        ref = data_ref
    else:
        ref = res.joinpath("default-settings.json")
    with ref.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
        return data


def _quarantine_corrupt_file(path: Path) -> Path | None:
    """Quarantine a corrupted settings file by renaming with timestamp."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    bad_path = path.with_name(f"{path.name}.bad-{timestamp}")
    if bad_path.exists():
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
        bad_path = path.with_name(f"{path.name}.bad-{timestamp}")

    try:
        path.rename(bad_path)
        logger.warning("Corrupt settings file quarantined to %s", bad_path)
        return bad_path
    except OSError as err:
        logger.error("Failed to quarantine corrupt file %s: %s", path, err)
        return None


def _load_user_overrides() -> dict[str, Any]:
    """Read user overrides from disk, recovering safely on error."""
    path = config.get_user_settings_path()
    if not path.is_file():
        return {}

    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("Settings content is not a JSON object")
        return data
    except Exception as exc:
        logger.error("Failed to read user settings from %s: %s", path, exc)
        _quarantine_corrupt_file(path)
        return {}


def _merge_settings(
    defaults: dict[str, Any], overrides: dict[str, Any]
) -> dict[str, Any]:
    """Merge user overrides onto defaults with strict type checking."""
    effective = dict(defaults)
    for key, val in overrides.items():
        if key not in defaults:
            logger.warning("Ignoring unknown user setting key: %s", key)
            continue

        default_val = defaults[key]
        if type(val) is not type(default_val):
            logger.warning(
                "Ignoring setting '%s' due to type mismatch: "
                "expected %s, got %s",
                key,
                type(default_val).__name__,
                type(val).__name__,
            )
            continue

        effective[key] = val
    return effective


def _save_user_overrides(overrides: dict[str, Any]) -> None:
    """Write user overrides atomically with mode 0o600."""
    path = config.get_user_settings_path()
    config.get_config_dir()  # Ensures parent exists with 0o700
    parent = path.parent
    temp_path = parent / f".{path.name}.tmp.{os.getpid()}"

    payload = json.dumps(overrides, indent=2) + "\n"
    try:
        fd = os.open(
            temp_path,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600,
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())

        temp_path.replace(path)
        with contextlib.suppress(OSError):
            path.chmod(0o600)
    except Exception:
        with contextlib.suppress(OSError):
            temp_path.unlink()
        raise


def reload() -> dict[str, Any]:
    """Force reload settings from disk and return effective settings."""
    global _cached_effective
    with _lock:
        defaults = load_default_settings()
        overrides = _load_user_overrides()
        _cached_effective = _merge_settings(defaults, overrides)
        return dict(_cached_effective)


def load_effective_settings() -> dict[str, Any]:
    """Return effective settings (defaults merged with user overrides)."""
    global _cached_effective
    with _lock:
        if _cached_effective is None:
            defaults = load_default_settings()
            overrides = _load_user_overrides()
            _cached_effective = _merge_settings(defaults, overrides)
        return dict(_cached_effective)


def update_user_setting(key: str, value: Any) -> dict[str, Any]:
    """Update a setting, persist atomically to disk, and return effective."""
    global _cached_effective
    defaults = load_default_settings()
    if key not in defaults:
        raise KeyError(f"Unknown setting key: {key}")

    expected_type = type(defaults[key])
    if type(value) is not expected_type:
        raise TypeError(
            f"Type mismatch for setting '{key}': "
            f"expected {expected_type.__name__}, got {type(value).__name__}"
        )

    with _lock:
        overrides = _load_user_overrides()
        overrides[key] = value
        _save_user_overrides(overrides)
        _cached_effective = _merge_settings(defaults, overrides)
        return dict(_cached_effective)


def reset_setting(key: str) -> None:
    """Reset a single setting back to its default value."""
    global _cached_effective
    defaults = load_default_settings()
    if key not in defaults:
        raise KeyError(f"Unknown setting key: {key}")

    with _lock:
        overrides = _load_user_overrides()
        if key in overrides:
            del overrides[key]
            _save_user_overrides(overrides)
        _cached_effective = _merge_settings(defaults, overrides)


def reset_all_settings() -> None:
    """Reset all settings to default values and remove user overrides."""
    global _cached_effective
    path = config.get_user_settings_path()
    with _lock:
        if path.is_file():
            with contextlib.suppress(OSError):
                path.unlink()
        _cached_effective = dict(load_default_settings())
