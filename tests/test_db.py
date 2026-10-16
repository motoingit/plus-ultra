"""Tests for database initialization, pragmas, transactions, and constraints.

Validates DBMS concepts:
- Concurrency and durability via WAL mode and busy timeout pragmas.
- ACID transaction atomicity and automatic rollback on failure.
- Schema constraints (check constraints, foreign key enforcement).
- Partial indexes and migration idempotency.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from plus_ultra.db import (
    CURRENT_SCHEMA_VERSION,
    get_connection,
    get_schema_version,
    init_db,
    set_schema_version,
    transaction,
)


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Provide a path to a temporary SQLite database."""
    return tmp_path / "test_plus_ultra.db"


def test_init_db_creates_schema_and_version(test_db_path: Path) -> None:
    """Verify init_db initializes tables and updates user_version."""
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        assert get_schema_version(conn) == CURRENT_SCHEMA_VERSION

        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        table_names = {row[0] for row in cur.fetchall()}
        expected_tables = {
            "categories",
            "tasks",
            "reminders",
            "reminder_fires",
            "app_state",
        }
        assert expected_tables.issubset(table_names)
    finally:
        conn.close()


def test_init_db_is_idempotent(test_db_path: Path) -> None:
    """Verify init_db can run repeatedly without error or schema loss."""
    init_db(test_db_path)
    # Second run
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        assert get_schema_version(conn) == CURRENT_SCHEMA_VERSION
    finally:
        conn.close()


def test_connection_pragmas(test_db_path: Path) -> None:
    """Verify foreign_keys, journal_mode, and busy_timeout pragmas."""
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert fk == 1

        journal = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert journal.lower() == "wal"

        timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        assert timeout == 5000

        # Verify row_factory returns dict-accessible rows
        row = conn.execute("SELECT 1 AS num, 'alpha' AS text;").fetchone()
        assert row["num"] == 1
        assert row["text"] == "alpha"
    finally:
        conn.close()


def test_transaction_commits_atomically(test_db_path: Path) -> None:
    """Verify transaction context manager commits successfully on exit."""
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        with transaction(conn) as cur:
            cur.execute(
                "INSERT INTO app_state (key, value) VALUES (?, ?);",
                ("theme", "dracula"),
            )

        cur2 = conn.execute("SELECT value FROM app_state WHERE key = 'theme';")
        assert cur2.fetchone()["value"] == "dracula"
    finally:
        conn.close()


def test_transaction_rolls_back_on_exception(test_db_path: Path) -> None:
    """Verify transaction rolls back all changes when an exception is raised."""
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        with (
            pytest.raises(RuntimeError, match="Simulated crash"),
            transaction(conn) as cur,
        ):
            cur.execute(
                "INSERT INTO app_state (key, value) VALUES (?, ?);",
                ("temp_flag", "should_rollback"),
            )
            raise RuntimeError("Simulated crash")

        cur = conn.execute(
            "SELECT value FROM app_state WHERE key = 'temp_flag';"
        )
        assert cur.fetchone() is None
    finally:
        conn.close()


def test_task_title_check_constraint(test_db_path: Path) -> None:
    """Verify CHECK constraint rejects empty or whitespace-only task titles."""
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        # Empty title
        with pytest.raises(sqlite3.IntegrityError), transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO tasks (
                    id, title, created_at, updated_at
                ) VALUES ('t1', '', '2026-10-16', '2026-10-16');
                """
            )

        # Whitespace-only title
        with pytest.raises(sqlite3.IntegrityError), transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO tasks (
                    id, title, created_at, updated_at
                ) VALUES ('t2', '   ', '2026-10-16', '2026-10-16');
                """
            )
    finally:
        conn.close()


def test_task_status_check_constraint(test_db_path: Path) -> None:
    """Verify CHECK constraint rejects invalid task statuses."""
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError), transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO tasks (
                    id, title, status, created_at, updated_at
                ) VALUES ('t1', 'Valid', 'InvalidStatus', '2026', '2026');
                """
            )
    finally:
        conn.close()


def test_task_critical_level_check_constraint(test_db_path: Path) -> None:
    """Verify CHECK constraint rejects invalid critical levels."""
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError), transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO tasks (
                    id, title, critical_level, created_at, updated_at
                ) VALUES ('t1', 'Valid', 'Urgent', '2026', '2026');
                """
            )
    finally:
        conn.close()


def test_foreign_key_enforcement(test_db_path: Path) -> None:
    """Verify foreign key constraint blocks orphaned reminders."""
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError), transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO reminders (
                    id, task_id, remind_at, created_at, updated_at
                ) VALUES (
                    'r1', 'non_existent_task', '2026-10-17', '2026', '2026'
                );
                """
            )
    finally:
        conn.close()


def test_partial_unique_index_categories_active(test_db_path: Path) -> None:
    """Verify categories unique index only applies when is_deleted = 0."""
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        with transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO categories (
                    id, name, created_at, updated_at, is_deleted
                ) VALUES ('c1', 'Work', '2026', '2026', 0);
                """
            )

        # Attempt duplicate active category name -> must fail
        with pytest.raises(sqlite3.IntegrityError), transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO categories (
                    id, name, created_at, updated_at, is_deleted
                ) VALUES ('c2', 'Work', '2026', '2026', 0);
                """
            )

        # Soft-delete the first category
        with transaction(conn) as cur:
            cur.execute("UPDATE categories SET is_deleted = 1 WHERE id = 'c1';")

        # Now creating another active category with the same name must succeed
        with transaction(conn) as cur:
            cur.execute(
                """
                INSERT INTO categories (
                    id, name, created_at, updated_at, is_deleted
                ) VALUES ('c3', 'Work', '2026', '2026', 0);
                """
            )

        row = conn.execute(
            "SELECT COUNT(*) FROM categories WHERE name = 'Work';"
        ).fetchone()
        assert row[0] == 2
    finally:
        conn.close()


def test_explain_query_plan_uses_index(test_db_path: Path) -> None:
    """Verify idx_reminders_due index is utilized by SQLite query planner."""
    init_db(test_db_path)
    conn = get_connection(test_db_path)
    try:
        cur = conn.execute(
            """
            EXPLAIN QUERY PLAN
            SELECT * FROM reminders
            WHERE is_deleted = 0 AND remind_at <= '2026-10-17T00:00:00Z';
            """
        )
        plan = " ".join(row[3] for row in cur.fetchall())
        assert "idx_reminders_due" in plan
    finally:
        conn.close()


def test_set_schema_version(test_db_path: Path) -> None:
    """Verify setting and reading arbitrary schema version."""
    conn = get_connection(test_db_path)
    try:
        assert get_schema_version(conn) == 0
        set_schema_version(conn, 42)
        assert get_schema_version(conn) == 42
    finally:
        conn.close()
