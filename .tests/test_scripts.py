"""Unit tests for standalone helper scripts in .scripts/."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

# Add .scripts and src to sys.path
_root = Path(__file__).resolve().parents[1]
_scripts_dir = _root / ".scripts"
_src_dir = _root / "src"
for p in (str(_scripts_dir), str(_src_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

import clear_db  # noqa: E402
import notify  # noqa: E402
import seed_data  # noqa: E402

from plus_ultra.database import get_connection, init_db  # noqa: E402


def _setup_isolated_db(tmp_path: Path) -> sqlite3.Connection:
    db_file = tmp_path / "test_scripts.db"
    init_db(db_file)
    return get_connection(db_file)


def test_seed_and_unseed_workflow(tmp_path: Path) -> None:
    """Test seeding demo data and unseeding it selectively."""
    conn = _setup_isolated_db(tmp_path)
    try:
        # Initial seed
        counts = seed_data.seed_demo_workspace_data(conn)
        assert counts["tasks"] > 0
        assert counts["code_items"] > 0
        assert counts["courses"] > 0
        assert counts["ideas_doubts"] > 0
        assert counts["opportunities"] > 0
        assert counts["quick_links"] > 0

        # Verify items exist
        cur = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_deleted = 0;")
        assert cur.fetchone()[0] == counts["tasks"]

        # Second seed without force should be no-op
        second_counts = seed_data.seed_demo_workspace_data(conn, force=False)
        assert second_counts == {}

        # Unseed demo data
        unseed_counts = seed_data.unseed_demo_workspace_data(
            conn, hard_delete=True
        )
        assert unseed_counts["tasks"] == counts["tasks"]
        assert unseed_counts["code_items"] == counts["code_items"]

        # Check tables are empty
        cur = conn.execute("SELECT COUNT(*) FROM tasks;")
        assert cur.fetchone()[0] == 0
        cur = conn.execute("SELECT COUNT(*) FROM code_items;")
        assert cur.fetchone()[0] == 0
    finally:
        conn.close()


def test_clear_database_hard_and_soft(tmp_path: Path) -> None:
    """Test clearing database tables with hard and soft delete modes."""
    conn = _setup_isolated_db(tmp_path)
    try:
        seed_data.seed_demo_workspace_data(conn)

        # Soft delete mode
        soft_counts = clear_db.clear_database(
            conn, tables=["tasks"], hard_delete=False, clear_app_state=False
        )
        assert soft_counts["tasks"] > 0

        # Still in DB with is_deleted = 1
        cur = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_deleted = 1;")
        assert cur.fetchone()[0] == soft_counts["tasks"]

        # Hard delete mode
        clear_db.clear_database(
            conn,
            tables=["tasks", "courses"],
            hard_delete=True,
            vacuum=False,
        )
        cur = conn.execute("SELECT COUNT(*) FROM tasks;")
        assert cur.fetchone()[0] == 0
        cur = conn.execute("SELECT COUNT(*) FROM courses;")
        assert cur.fetchone()[0] == 0
    finally:
        conn.close()


def test_clear_database_with_app_state(tmp_path: Path) -> None:
    """Test clearing runtime machine state."""
    conn = _setup_isolated_db(tmp_path)
    try:
        conn.execute("INSERT INTO app_state (key, value) VALUES ('x', '100');")
        conn.commit()

        counts = clear_db.clear_database(
            conn, tables=[], hard_delete=True, clear_app_state=True
        )
        assert counts.get("app_state", 0) == 1

        cur = conn.execute("SELECT COUNT(*) FROM app_state;")
        assert cur.fetchone()[0] == 0
    finally:
        conn.close()


def test_notify_script_dispatch_and_args() -> None:
    """Test notify script CLI parsing and notification dispatch."""
    args = notify.parse_args(["1.5", "--title", "Hello", "--message", "World"])
    assert args.delay_minutes == 1.5
    assert args.title == "Hello"
    assert args.message == "World"

    sec_args = notify.parse_args(["-s", "10", "-u", "critical"])
    assert sec_args.seconds == 10.0
    assert sec_args.urgency == "critical"

    with patch("notify.send_desktop_notification", return_value=True) as mock_n:
        res = notify.dispatch_notification(
            title="T", message="M", delay_seconds=0, urgency="normal"
        )
        assert res is True
        mock_n.assert_called_once_with(title="T", message="M", urgency="normal")


def test_cli_argument_parsers() -> None:
    """Test argument parsing across clear_db and seed_data."""
    c_args = clear_db.parse_args(["--table", "tasks", "--soft", "--force"])
    assert c_args.table == ["tasks"]
    assert c_args.soft is True
    assert c_args.force is True

    s_args = seed_data.parse_args(["--unseed", "--soft"])
    assert s_args.unseed is True
    assert s_args.soft is True
