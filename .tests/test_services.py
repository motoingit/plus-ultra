"""Unit tests for TaskService and CategoryService.

Validates:
- Pure business logic and validation rules (empty title, invalid status/levels).
- Status toggling state transitions.
- Category lifecycle and cascading nullification to tasks.
- Advanced querying: filtering by category, status, priority, and text search.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from plus_ultra.database import get_connection, init_db
from plus_ultra.repositories import (
    CategoryRepository,
    ReminderRepository,
    TaskRepository,
)
from plus_ultra.services import (
    CategoryService,
    ReminderService,
    TaskService,
)


@pytest.fixture
def services(
    tmp_path: Path,
) -> tuple[TaskService, CategoryService]:
    """Provide initialized TaskService and CategoryService with a temp DB."""
    db_path = tmp_path / "test_services.db"
    init_db(db_path)
    conn = get_connection(db_path)
    cat_repo = CategoryRepository(conn)
    task_repo = TaskRepository(conn)
    return TaskService(task_repo, cat_repo), CategoryService(cat_repo)


def test_task_service_create_and_validation(
    services: tuple[TaskService, CategoryService],
) -> None:
    """Verify task creation and input validation rules."""
    task_svc, cat_svc = services
    cat = cat_svc.create_category("Academics")

    task = task_svc.create_task(
        title="Operating Systems Lab",
        category_id=cat.id,
        description="Paging & Virtual Memory",
        critical_level="High",
        pace_level="Short-term",
    )
    assert task.title == "Operating Systems Lab"
    assert task.category_id == cat.id
    assert task.status == "Pending"
    assert task.critical_level == "High"

    # Empty title raises ValueError
    with pytest.raises(ValueError, match="empty or whitespace-only"):
        task_svc.create_task("   ")

    # Invalid status raises ValueError
    with pytest.raises(ValueError, match="Invalid status"):
        task_svc.create_task("Valid Title", status="Unknown")

    # Invalid critical level raises ValueError
    with pytest.raises(ValueError, match="Invalid critical level"):
        task_svc.create_task("Valid Title", critical_level="Urgent")

    # Invalid pace level raises ValueError
    with pytest.raises(ValueError, match="Invalid pace level"):
        task_svc.create_task("Valid Title", pace_level="Infinite")

    # Non-existent category raises ValueError
    with pytest.raises(ValueError, match="does not exist"):
        task_svc.create_task("Valid Title", category_id="bad-uuid")


def test_task_service_toggle_status(
    services: tuple[TaskService, CategoryService],
) -> None:
    """Verify cycling status between Pending and Completed."""
    task_svc = services[0]
    task = task_svc.create_task("Review Code")
    assert task.status == "Pending"

    # Toggle to Completed
    toggled = task_svc.toggle_status(task.id)
    assert toggled is not None
    assert toggled.status == "Completed"

    # Toggle back to Pending
    toggled2 = task_svc.toggle_status(task.id)
    assert toggled2 is not None
    assert toggled2.status == "Pending"


def test_task_service_search_and_filters(
    services: tuple[TaskService, CategoryService],
) -> None:
    """Verify multi-criteria filtering and text search."""
    task_svc, cat_svc = services
    c_work = cat_svc.create_category("Work")
    c_study = cat_svc.create_category("Study")

    t1 = task_svc.create_task(
        "Build SQLite Layer",
        category_id=c_work.id,
        description="WAL mode and ACID",
        critical_level="High",
        status="Completed",
    )
    t2 = task_svc.create_task(
        "Study DBMS Normalization",
        category_id=c_study.id,
        description="1NF to BCNF",
        critical_level="Medium",
        status="Pending",
    )
    t3 = task_svc.create_task(
        "Prepare Resume",
        category_id=c_work.id,
        description="Tailor for internships",
        critical_level="High",
        status="Pending",
    )

    # Filter by category
    work_tasks = task_svc.list_tasks(category_id=c_work.id)
    assert {t.id for t in work_tasks} == {t1.id, t3.id}

    # Filter by status
    pending_tasks = task_svc.list_tasks(status="Pending")
    assert {t.id for t in pending_tasks} == {t2.id, t3.id}

    # Filter by critical level
    high_tasks = task_svc.list_tasks(critical_level="High")
    assert {t.id for t in high_tasks} == {t1.id, t3.id}

    # Text search on title
    search_sqlite = task_svc.list_tasks(search_query="sqlite")
    assert len(search_sqlite) == 1
    assert search_sqlite[0].id == t1.id

    # Text search on description (case-insensitive)
    search_bcnf = task_svc.list_tasks(search_query="bcnf")
    assert len(search_bcnf) == 1
    assert search_bcnf[0].id == t2.id


def test_category_service_lifecycle_and_cascade(
    services: tuple[TaskService, CategoryService],
) -> None:
    """Verify category creation, updating, and soft-delete nullification."""
    task_svc, cat_svc = services
    cat = cat_svc.create_category("Personal", color="#ec4899")
    task = task_svc.create_task("Workout", category_id=cat.id)
    assert task.category_id == cat.id

    # Update category
    updated = cat_svc.update_category(cat.id, "Health & Fitness", "#10b981")
    assert updated is not None
    assert updated.name == "Health & Fitness"

    # Soft delete category
    assert cat_svc.soft_delete_category(cat.id) is True
    assert cat_svc.get_category(cat.id) is None

    # Linked task must still exist, with category_id set to None
    reloaded_task = task_svc.get_task(task.id)
    assert reloaded_task is not None
    assert reloaded_task.category_id is None


def test_reminder_service_lifecycle_and_validation(tmp_path: Path) -> None:
    """Verify ReminderService validation, creation, and due querying."""
    db_path = tmp_path / "rem_svc_test.db"
    init_db(db_path)
    conn = get_connection(db_path)
    cat_repo = CategoryRepository(conn)
    task_repo = TaskRepository(conn)
    rem_repo = ReminderRepository(conn)
    task_svc = TaskService(task_repo, cat_repo)
    rem_svc = ReminderService(rem_repo, task_repo)

    task = task_svc.create_task("OS Scheduling Exam")

    # Empty task_id or non-existent task raises ValueError
    with pytest.raises(ValueError, match="does not exist or is deleted"):
        rem_svc.create_reminder("bad-uuid", "2026-10-16T10:00:00Z")

    # Empty remind_at raises ValueError
    with pytest.raises(ValueError, match="cannot be empty"):
        rem_svc.create_reminder(task.id, "   ")

    # Happy path creation
    rem = rem_svc.create_reminder(task.id, "2026-10-16T10:00:00Z")
    assert rem.task_id == task.id
    assert rem.remind_at == "2026-10-16T10:00:00Z"

    # Due query before 10:00:00Z
    assert len(rem_svc.get_due_reminders("2026-10-16T09:59:59Z")) == 0

    # Due query at or after 10:00:00Z
    due = rem_svc.get_due_reminders("2026-10-16T10:00:00Z")
    assert len(due) == 1
    assert due[0][0].id == rem.id
    assert due[0][1].id == task.id

    # Mark fired
    rem_svc.mark_fired(rem.id)
    assert rem_svc.is_fired(rem.id) is True

    # After firing, it is excluded from get_due_reminders
    assert len(rem_svc.get_due_reminders("2026-10-16T11:00:00Z")) == 0

    # Soft delete reminder
    rem2 = rem_svc.create_reminder(task.id, "2026-10-16T12:00:00Z")
    assert rem_svc.soft_delete_reminder(rem2.id) is True
    assert len(rem_svc.get_due_reminders("2026-10-16T13:00:00Z")) == 0
