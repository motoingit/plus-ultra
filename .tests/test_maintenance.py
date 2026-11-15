"""Tests for data maintenance, config reset, and factory reset workflows.

Validates:
- wipe_database: Transactionally clears all 10 SQLite application tables.
- reset_config_settings: Restores user preferences while preserving data.
- factory_reset: Clears all application data, resets settings, and refreshes UI.
- User cancellation: Aborting confirmation prompts leaves state untouched.
"""

from __future__ import annotations

import contextlib
import sqlite3
import tkinter as tk
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from plus_ultra import config, settings
from plus_ultra.database import (
    get_connection,
    init_db,
    seed_demo_workspace_data,
    wipe_database,
)
from plus_ultra.ui.views.settings_view import SettingsView


@pytest.fixture
def isolated_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Generator[tuple[Path, sqlite3.Connection], None, None]:
    """Provide isolated configuration directory and SQLite database."""
    cfg_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg_dir))
    monkeypatch.setenv("XDG_DATA_HOME", str(data_dir))
    settings.reload()

    db_path = config.get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)
    yield db_path, conn
    conn.close()


def test_wipe_database_clears_all_application_tables(
    isolated_env: tuple[Path, sqlite3.Connection],
) -> None:
    """Verify wipe_database empties all 10 application tables."""
    _, conn = isolated_env
    seed_demo_workspace_data(conn)

    tables = [
        "tasks",
        "categories",
        "code_items",
        "courses",
        "ideas_doubts",
        "opportunities",
        "quick_links",
    ]
    for tbl in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {tbl};").fetchone()[0]
        assert count > 0, f"Expected {tbl} to contain seeded demo data"

    wipe_database(conn)

    all_tables = [
        "reminder_fires",
        "reminders",
        "tasks",
        "categories",
        "app_state",
        "code_items",
        "courses",
        "ideas_doubts",
        "opportunities",
        "quick_links",
    ]
    for tbl in all_tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {tbl};").fetchone()[0]
        assert count == 0, f"Expected {tbl} to be empty after wipe_database"


def test_reset_config_settings_preserves_database(
    isolated_env: tuple[Path, sqlite3.Connection],
) -> None:
    """Reset config settings resets preferences without touching user data."""
    _, conn = isolated_env
    seed_demo_workspace_data(conn)

    settings.update_user_setting("always_on_top", False)
    settings.update_user_setting("glow_enabled", False)
    assert settings.load_effective_settings()["always_on_top"] is False

    root = tk.Tk()
    try:
        frame = tk.Frame(root)
        view = SettingsView(frame, root)

        with (
            patch("tkinter.messagebox.askyesno", return_value=True),
            patch("tkinter.messagebox.showinfo"),
        ):
            view.reset_config_settings()

        eff = settings.load_effective_settings()
        assert eff["always_on_top"] is True
        assert eff["glow_enabled"] is True

        task_count = conn.execute("SELECT COUNT(*) FROM tasks;").fetchone()[0]
        assert task_count > 0, "Tasks should be preserved on config reset"
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_factory_reset_wipes_both_data_and_settings(
    isolated_env: tuple[Path, sqlite3.Connection],
) -> None:
    """Factory reset wipes all database tables and resets user preferences."""
    _, conn = isolated_env
    seed_demo_workspace_data(conn)

    settings.update_user_setting("always_on_top", False)
    reseed_called = False

    def _on_reseed() -> None:
        nonlocal reseed_called
        reseed_called = True

    root = tk.Tk()
    try:
        frame = tk.Frame(root)
        view = SettingsView(frame, root, on_reseed=_on_reseed)

        with (
            patch("tkinter.messagebox.askyesno", return_value=True),
            patch("tkinter.messagebox.showinfo"),
        ):
            view.factory_reset()

        assert reseed_called is True

        eff = settings.load_effective_settings()
        assert eff["always_on_top"] is True

        for tbl in ["tasks", "categories", "code_items", "courses"]:
            count = conn.execute(f"SELECT COUNT(*) FROM {tbl};").fetchone()[0]
            assert count == 0, f"Expected {tbl} to be empty after factory reset"
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_factory_reset_cancelled_by_user(
    isolated_env: tuple[Path, sqlite3.Connection],
) -> None:
    """Cancelling factory reset leaves preferences and database untouched."""
    _, conn = isolated_env
    seed_demo_workspace_data(conn)
    settings.update_user_setting("always_on_top", False)

    mock_reseed = MagicMock()
    root = tk.Tk()
    try:
        frame = tk.Frame(root)
        view = SettingsView(frame, root, on_reseed=mock_reseed)

        with patch("tkinter.messagebox.askyesno", return_value=False):
            view.factory_reset()

        mock_reseed.assert_not_called()
        assert settings.load_effective_settings()["always_on_top"] is False

        count = conn.execute("SELECT COUNT(*) FROM tasks;").fetchone()[0]
        assert count > 0, "Tasks should not be wiped when cancelled"
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_terminate_application_calls_callback() -> None:
    """Terminate application invokes callback when confirmed by user."""
    mock_terminate = MagicMock()
    root = tk.Tk()
    try:
        frame = tk.Frame(root)
        view = SettingsView(frame, root, on_terminate=mock_terminate)

        with patch("tkinter.messagebox.askyesno", return_value=True):
            view.terminate_application()

        mock_terminate.assert_called_once()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_terminate_application_cancelled() -> None:
    """Terminate application does nothing when cancelled by user."""
    mock_terminate = MagicMock()
    root = tk.Tk()
    try:
        frame = tk.Frame(root)
        view = SettingsView(frame, root, on_terminate=mock_terminate)

        with patch("tkinter.messagebox.askyesno", return_value=False):
            view.terminate_application()

        mock_terminate.assert_not_called()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()
