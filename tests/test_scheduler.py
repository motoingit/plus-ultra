"""Unit tests for ReminderScheduler and ReminderService.

Validates:
- Pure reminder evaluation logic using deterministic fake clocks.
- Due reminder filtering excludes reminders due in the future.
- Due reminder filtering excludes reminders belonging to soft-deleted tasks.
- Atomic fire marking prevents duplicate dispatches (exactly-once semantics).
- Respects reminders_enabled configuration flag.
- Background thread lifecycle: start, thread execution, and clean shutdown.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from plus_ultra.db import get_connection, init_db
from plus_ultra.repository import (
    CategoryRepository,
    ReminderRepository,
    TaskRepository,
)
from plus_ultra.scheduler import ReminderScheduler
from plus_ultra.services import ReminderService, TaskService


@pytest.fixture
def test_setup(
    tmp_path: Path,
) -> tuple[TaskService, ReminderService]:
    """Initialize DB and return services for testing."""
    db_path = tmp_path / "scheduler_test.db"
    init_db(db_path)
    conn = get_connection(db_path)
    cat_repo = CategoryRepository(conn)
    task_repo = TaskRepository(conn)
    rem_repo = ReminderRepository(conn)
    task_svc = TaskService(task_repo, cat_repo)
    rem_svc = ReminderService(rem_repo, task_repo)
    return task_svc, rem_svc


def test_scheduler_evaluates_due_reminders(
    test_setup: tuple[TaskService, ReminderService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify reminders due at or before tick time are evaluated and fired."""
    task_svc, rem_svc = test_setup
    task = task_svc.create_task("OS Memory Lab", critical_level="High")

    # Schedule one past reminder and one future reminder
    r_past = rem_svc.create_reminder(task.id, "2026-10-16T10:00:00Z")
    r_future = rem_svc.create_reminder(task.id, "2026-10-16T12:00:00Z")

    mock_notify = MagicMock()
    monkeypatch.setattr(
        "plus_ultra.desktop.send_desktop_notification", mock_notify
    )

    mock_callback = MagicMock()
    scheduler = ReminderScheduler(
        reminder_service=rem_svc,
        on_reminder_due=mock_callback,
        desktop_notify=True,
    )

    # Evaluate at 11:00:00Z: only past reminder should fire
    fired = scheduler.tick(now_iso="2026-10-16T11:00:00Z")
    assert len(fired) == 1
    assert fired[0][0].id == r_past.id
    assert fired[0][1].id == task.id

    # Verify desktop notification called with task info
    mock_notify.assert_called_once()
    assert "OS Memory Lab" in mock_notify.call_args[1]["title"]
    assert mock_notify.call_args[1]["urgency"] == "critical"

    # Verify in-app UI callback called
    mock_callback.assert_called_once_with(task, r_past)

    # Verify fired reminder is recorded in reminder_fires
    assert rem_svc.is_fired(r_past.id) is True
    assert rem_svc.is_fired(r_future.id) is False

    # Second tick at 11:30:00Z: r_past must NOT fire again (exactly once)
    fired_second = scheduler.tick(now_iso="2026-10-16T11:30:00Z")
    assert len(fired_second) == 0


def test_scheduler_excludes_soft_deleted_tasks(
    test_setup: tuple[TaskService, ReminderService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify reminders for soft-deleted tasks are excluded from evaluation."""
    task_svc, rem_svc = test_setup
    task = task_svc.create_task("Dropped Course Project")
    reminder = rem_svc.create_reminder(task.id, "2026-10-16T09:00:00Z")

    # Soft delete the task
    assert task_svc.soft_delete_task(task.id) is True

    mock_notify = MagicMock()
    monkeypatch.setattr(
        "plus_ultra.desktop.send_desktop_notification", mock_notify
    )

    scheduler = ReminderScheduler(
        reminder_service=rem_svc,
        desktop_notify=True,
    )

    fired = scheduler.tick(now_iso="2026-10-16T10:00:00Z")
    assert len(fired) == 0
    mock_notify.assert_not_called()
    assert rem_svc.is_fired(reminder.id) is False


def test_scheduler_respects_settings_disabled(
    test_setup: tuple[TaskService, ReminderService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify tick skips firing when reminders_enabled is False in settings."""
    task_svc, rem_svc = test_setup
    task = task_svc.create_task("Study Compiler Pass")
    rem_svc.create_reminder(task.id, "2026-10-16T08:00:00Z")

    # Mock settings with reminders_enabled=False
    monkeypatch.setattr(
        "plus_ultra.settings.load_effective_settings",
        lambda: {"reminders_enabled": False},
    )

    mock_notify = MagicMock()
    monkeypatch.setattr(
        "plus_ultra.desktop.send_desktop_notification", mock_notify
    )

    scheduler = ReminderScheduler(
        reminder_service=rem_svc,
        desktop_notify=True,
    )

    fired = scheduler.tick(now_iso="2026-10-16T10:00:00Z")
    assert len(fired) == 0
    mock_notify.assert_not_called()


def test_scheduler_thread_lifecycle(
    test_setup: tuple[TaskService, ReminderService],
) -> None:
    """Verify background worker thread starts and shuts down cleanly."""
    _, rem_svc = test_setup
    scheduler = ReminderScheduler(
        reminder_service=rem_svc,
        poll_interval_s=0.05,
    )

    assert not scheduler.is_running
    scheduler.start()
    assert scheduler.is_running

    # Idempotent start
    scheduler.start()
    assert scheduler.is_running

    # Clean stop
    scheduler.stop(timeout=1.0)
    assert not scheduler.is_running
