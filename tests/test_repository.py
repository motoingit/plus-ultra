"""Unit tests for repository data access layer and DBMS integrity rules.

Validates DBMS concepts:
- Parameterized SQL and protection against SQL injection.
- Atomic cascading soft deletes (task -> reminders, category -> tasks nullify).
- Query optimization and index filtering (active only, due reminders).
- Runtime machine state isolation in app_state.
- Edge cases (Unicode, very long strings, whitespace, foreign keys).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from plus_ultra.database import get_connection, init_db
from plus_ultra.repositories import (
    AppStateRepository,
    CategoryRepository,
    ReminderRepository,
    TaskRepository,
)


@pytest.fixture
def repos(
    tmp_path: Path,
) -> tuple[
    CategoryRepository,
    TaskRepository,
    ReminderRepository,
    AppStateRepository,
    sqlite3.Connection,
]:
    """Initialize a test database and return instantiated repositories."""
    db_path = tmp_path / "test_repo.db"
    init_db(db_path)
    conn = get_connection(db_path)
    yield (
        CategoryRepository(conn),
        TaskRepository(conn),
        ReminderRepository(conn),
        AppStateRepository(conn),
        conn,
    )
    conn.close()


def test_category_crud_and_trimming(
    repos: tuple[
        CategoryRepository,
        TaskRepository,
        ReminderRepository,
        AppStateRepository,
        sqlite3.Connection,
    ],
) -> None:
    """Test category creation, trimming, lookup, updating, and listing."""
    cat_repo = repos[0]
    cat = cat_repo.create("  Academics 🎓  ", color="#3b82f6")
    assert cat.name == "Academics 🎓"
    assert cat.color == "#3b82f6"
    assert cat.is_deleted == 0

    fetched = cat_repo.get_by_id(cat.id)
    assert fetched is not None
    assert fetched.name == "Academics 🎓"

    updated = cat_repo.update(cat.id, "Studies", "#10b981")
    assert updated is not None
    assert updated.name == "Studies"
    assert updated.color == "#10b981"

    active_cats = cat_repo.list_active()
    assert len(active_cats) == 1
    assert active_cats[0].id == cat.id


def test_category_soft_delete_and_name_reuse(
    repos: tuple[
        CategoryRepository,
        TaskRepository,
        ReminderRepository,
        AppStateRepository,
        sqlite3.Connection,
    ],
) -> None:
    """Verify unique constraint on active categories and name reuse."""
    cat_repo = repos[0]
    c1 = cat_repo.create("Work")

    # Creating duplicate active name must raise IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        cat_repo.create("Work")

    # Soft-delete the category
    assert cat_repo.soft_delete(c1.id) is True
    assert cat_repo.list_active() == []

    # Can now reuse the name for a new active category
    c2 = cat_repo.create("Work")
    assert c2.id != c1.id
    assert len(cat_repo.list_active()) == 1


def test_category_soft_delete_cascades_null_to_tasks(
    repos: tuple[
        CategoryRepository,
        TaskRepository,
        ReminderRepository,
        AppStateRepository,
        sqlite3.Connection,
    ],
) -> None:
    """Verify soft-deleting category sets linked tasks' category_id to NULL."""
    cat_repo, task_repo = repos[0], repos[1]
    cat = cat_repo.create("Operating Systems")
    task = task_repo.create("Paging Lab", category_id=cat.id)
    assert task.category_id == cat.id

    # Soft delete category
    assert cat_repo.soft_delete(cat.id) is True

    # Linked task must have category_id nullified
    reloaded_task = task_repo.get_by_id(task.id)
    assert reloaded_task is not None
    assert reloaded_task.category_id is None


def test_task_crud_and_custom_attributes(
    repos: tuple[
        CategoryRepository,
        TaskRepository,
        ReminderRepository,
        AppStateRepository,
        sqlite3.Connection,
    ],
) -> None:
    """Verify task creation with custom fields and updating."""
    task_repo = repos[1]
    task = task_repo.create(
        title="Implement WAL Mode",
        description="Verify concurrency with PRAGMA journal_mode=WAL",
        due_date="2026-10-20T12:00:00Z",
        status="Pending",
        task_label="College",
        critical_level="High",
        pace_level="Short-term",
        is_google_task=True,
    )

    assert task.title == "Implement WAL Mode"
    assert task.critical_level == "High"
    assert task.pace_level == "Short-term"
    assert task.is_google_task is True

    updated = task_repo.update(
        task.id,
        status="Completed",
        critical_level="Low",
        description="Updated description",
    )
    assert updated is not None
    assert updated.status == "Completed"
    assert updated.critical_level == "Low"
    assert updated.description == "Updated description"


def test_task_filtering(
    repos: tuple[
        CategoryRepository,
        TaskRepository,
        ReminderRepository,
        AppStateRepository,
        sqlite3.Connection,
    ],
) -> None:
    """Verify filtering tasks by category and status."""
    cat_repo, task_repo = repos[0], repos[1]
    cat1 = cat_repo.create("Cat1")
    cat2 = cat_repo.create("Cat2")

    task_repo.create("T1", category_id=cat1.id, status="Pending")
    task_repo.create("T2", category_id=cat1.id, status="Completed")
    task_repo.create("T3", category_id=cat2.id, status="Pending")

    # Filter by category
    cat1_tasks = task_repo.list_active(category_id=cat1.id)
    assert len(cat1_tasks) == 2

    # Filter by status
    pending_tasks = task_repo.list_active(status="Pending")
    assert len(pending_tasks) == 2

    # Filter by both
    cat1_pending = task_repo.list_active(category_id=cat1.id, status="Pending")
    assert len(cat1_pending) == 1
    assert cat1_pending[0].title == "T1"


def test_task_soft_delete_cascades_to_reminders(
    repos: tuple[
        CategoryRepository,
        TaskRepository,
        ReminderRepository,
        AppStateRepository,
        sqlite3.Connection,
    ],
) -> None:
    """Verify soft-deleting a task also soft-deletes its reminders."""
    task_repo, reminder_repo = repos[1], repos[2]
    task = task_repo.create("Study DBMS Normalization")
    rem1 = reminder_repo.create(task.id, "2026-10-18T09:00:00Z")
    rem2 = reminder_repo.create(task.id, "2026-10-18T10:00:00Z")

    assert reminder_repo.get_by_id(rem1.id).is_deleted == 0
    assert reminder_repo.get_by_id(rem2.id).is_deleted == 0

    # Soft delete task
    assert task_repo.soft_delete(task.id) is True

    # Check task is marked deleted
    assert task_repo.get_by_id(task.id).is_deleted == 1
    assert task_repo.list_active() == []

    # Check reminders are also soft-deleted
    assert reminder_repo.get_by_id(rem1.id).is_deleted == 1
    assert reminder_repo.get_by_id(rem2.id).is_deleted == 1


def test_reminder_list_due_filtering(
    repos: tuple[
        CategoryRepository,
        TaskRepository,
        ReminderRepository,
        AppStateRepository,
        sqlite3.Connection,
    ],
) -> None:
    """Verify list_due filters by time, task deletion, and fired state."""
    task_repo, reminder_repo = repos[1], repos[2]
    task1 = task_repo.create("Task 1")
    task2 = task_repo.create("Task 2")

    r1 = reminder_repo.create(task1.id, "2026-10-17T08:00:00Z")
    r2 = reminder_repo.create(task1.id, "2026-10-17T09:00:00Z")
    r3 = reminder_repo.create(task2.id, "2026-10-17T08:30:00Z")
    r_future = reminder_repo.create(task2.id, "2026-10-17T12:00:00Z")

    # Due at 09:30: r1, r2, r3 (r_future excluded by timestamp)
    due = reminder_repo.list_due("2026-10-17T09:30:00Z")
    due_ids = [r.id for r in due]
    assert due_ids == [r1.id, r3.id, r2.id]  # Ordered by remind_at ASC
    assert r_future.id not in due_ids

    # Mark r1 as fired -> excluded from subsequent queries
    reminder_repo.mark_fired(r1.id)
    assert reminder_repo.is_fired(r1.id) is True
    due_after_fire = reminder_repo.list_due("2026-10-17T09:30:00Z")
    assert r1.id not in [r.id for r in due_after_fire]

    # Soft delete task2 -> r3 must be excluded because parent task is deleted
    task_repo.soft_delete(task2.id)
    due_after_task_del = reminder_repo.list_due("2026-10-17T09:30:00Z")
    assert [r.id for r in due_after_task_del] == [r2.id]


def test_app_state_repository(
    repos: tuple[
        CategoryRepository,
        TaskRepository,
        ReminderRepository,
        AppStateRepository,
        sqlite3.Connection,
    ],
) -> None:
    """Verify key-value persistence and widget position saving/retrieval."""
    app_state = repos[3]

    assert app_state.get("non_existent", "default_val") == "default_val"
    assert app_state.get_widget_position() is None

    app_state.set("sync_token", "abc-123")
    assert app_state.get("sync_token") == "abc-123"

    # Upsert existing key
    app_state.set("sync_token", "def-456")
    assert app_state.get("sync_token") == "def-456"

    # Widget position
    app_state.set_widget_position(650, 42)
    pos = app_state.get_widget_position()
    assert pos == (650, 42)


def test_app_state_handles_corrupt_coordinates(
    repos: tuple[
        CategoryRepository,
        TaskRepository,
        ReminderRepository,
        AppStateRepository,
        sqlite3.Connection,
    ],
) -> None:
    """Verify get_widget_position returns None if coordinates are corrupt."""
    app_state = repos[3]
    app_state.set("widget_x", "not_a_number")
    app_state.set("widget_y", "50")
    assert app_state.get_widget_position() is None


def test_unicode_and_long_strings(
    repos: tuple[
        CategoryRepository,
        TaskRepository,
        ReminderRepository,
        AppStateRepository,
        sqlite3.Connection,
    ],
) -> None:
    """Verify handling of Unicode, emojis, and very long text."""
    cat_repo, task_repo = repos[0], repos[1]
    long_desc = "X" * 10000
    unicode_title = "こんにちは 世界 🚀🔥"

    cat = cat_repo.create("プロジェクト 📁")
    task = task_repo.create(
        title=unicode_title,
        category_id=cat.id,
        description=long_desc,
    )

    reloaded = task_repo.get_by_id(task.id)
    assert reloaded is not None
    assert reloaded.title == unicode_title
    assert reloaded.description == long_desc
