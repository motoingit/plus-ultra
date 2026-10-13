"""Tests for plus_ultra.config and initial application startup.

Validates:
- Happy paths: default XDG directory resolution and environment overrides.
- Security: directory permissions mode 0o700 (owner read, write, execute only).
- Edge cases: empty environment variables, unicode paths, and long paths.
- Integration: main() startup logging to launcher.log.
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from plus_ultra import config
from plus_ultra.main import main as app_main


def test_default_xdg_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When no XDG env vars are set, fallback to ~/.local/share and state."""
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)

    data_dir = config.get_data_dir()
    state_dir = config.get_state_dir()

    expected_data = fake_home / ".local" / "share" / config.APP_NAME
    expected_state = fake_home / ".local" / "state" / config.APP_NAME

    assert data_dir == expected_data
    assert state_dir == expected_state
    assert data_dir.is_dir()
    assert state_dir.is_dir()


def test_custom_xdg_env_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When XDG env vars are set, use them."""
    custom_data = tmp_path / "custom_data"
    custom_state = tmp_path / "custom_state"

    monkeypatch.setenv("XDG_DATA_HOME", str(custom_data))
    monkeypatch.setenv("XDG_STATE_HOME", str(custom_state))

    data_dir = config.get_data_dir()
    state_dir = config.get_state_dir()

    assert data_dir == custom_data / config.APP_NAME
    assert state_dir == custom_state / config.APP_NAME
    assert config.get_db_path() == data_dir / config.DB_FILENAME
    assert config.get_log_path() == state_dir / config.LOG_FILENAME


def test_directory_permissions_mode_0700(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Security check: Directories created with mode 0o700 (rwx------)."""
    target = tmp_path / "secure_env"
    monkeypatch.setenv("XDG_DATA_HOME", str(target / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(target / "state"))

    data_dir = config.get_data_dir()
    state_dir = config.get_state_dir()

    data_mode = stat.S_IMODE(data_dir.stat().st_mode)
    state_mode = stat.S_IMODE(state_dir.stat().st_mode)

    assert data_mode == 0o700, f"Expected 0o700, got {oct(data_mode)}"
    assert state_mode == 0o700, f"Expected 0o700, got {oct(state_mode)}"


@pytest.mark.parametrize("empty_val", ["", "   ", "\t"])
def test_edge_case_empty_env_vars_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, empty_val: str
) -> None:
    """Empty or whitespace-only env vars fallback to defaults safely."""
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.setenv("XDG_DATA_HOME", empty_val)
    monkeypatch.setenv("XDG_STATE_HOME", empty_val)

    expected_data = fake_home / ".local" / "share" / config.APP_NAME
    expected_state = fake_home / ".local" / "state" / config.APP_NAME

    assert config.get_data_dir() == expected_data
    assert config.get_state_dir() == expected_state


def test_edge_case_unicode_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unicode characters in path names (e.g. non-ASCII user home)."""
    unicode_dir = tmp_path / "ユーザー_über_tëst"
    monkeypatch.setenv("XDG_DATA_HOME", str(unicode_dir / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(unicode_dir / "state"))

    data_dir = config.get_data_dir()
    assert data_dir.exists()
    assert "ユーザー" in str(data_dir)


def test_edge_case_very_long_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Very long nested paths are handled properly."""
    long_nest = tmp_path / ("sub_" * 25)
    monkeypatch.setenv("XDG_DATA_HOME", str(long_nest))

    data_dir = config.get_data_dir()
    assert data_dir.is_dir()
    assert data_dir.exists()


def test_main_startup_logging(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Integration: main() writes startup lines to launcher.log."""
    fake_state = tmp_path / "test_state"
    monkeypatch.setenv("XDG_STATE_HOME", str(fake_state))

    app_main([])

    log_file = config.get_log_path()
    assert log_file.is_file(), f"Log file was not created at {log_file}"

    content = log_file.read_text(encoding="utf-8")
    assert "PLUS-ULTRA initializing..." in content
    assert "foundation initialized successfully." in content
