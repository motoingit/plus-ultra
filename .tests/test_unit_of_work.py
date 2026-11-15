"""Tests for the Unit of Work pattern implementation."""

from __future__ import annotations

import pytest

from plus_ultra.infrastructure.persistence.database_config import DatabaseConfig
from plus_ultra.infrastructure.persistence.database_factory import (
    DatabaseFactory,
)
from plus_ultra.infrastructure.persistence.database_initializer import (
    init_database,
)


@pytest.fixture
def memory_db_factory() -> DatabaseFactory:
    """Create in-memory DatabaseFactory with initialized schema."""
    config = DatabaseConfig(
        backend="sqlite",
        url="sqlite:///:memory:",
        echo=False,
    )
    factory = DatabaseFactory(config)
    init_database(engine=factory.engine)
    return factory


def test_unit_of_work_commits_atomically(
    memory_db_factory: DatabaseFactory,
) -> None:
    """Verify that multiple repository changes commit together on exit."""
    uow = memory_db_factory.create_unit_of_work()

    with uow:
        cat = uow.categories.create("Core Systems", color="#1e293b")
        task = uow.tasks.create(
            title="Implement Epoll Reactor",
            category_id=cat.id,
            critical_level="High",
        )
        uow.reminders.create(
            task_id=task.id,
            remind_at="2026-11-25T09:00:00Z",
        )
        uow.commit()

    # Verify data is committed and visible in a new session
    verify_uow = memory_db_factory.create_unit_of_work()
    with verify_uow:
        cats = verify_uow.categories.list_active()
        tasks = verify_uow.tasks.list_active()
        assert len(cats) == 1
        assert cats[0].name == "Core Systems"
        assert len(tasks) == 1
        assert tasks[0].title == "Implement Epoll Reactor"


def test_unit_of_work_rolls_back_on_exception(
    memory_db_factory: DatabaseFactory,
) -> None:
    """Verify that uncommitted changes roll back when an exception occurs."""
    uow = memory_db_factory.create_unit_of_work()

    with pytest.raises(RuntimeError, match="Simulation Failure"), uow:
        uow.categories.create("Doomed Category")
        uow.tasks.create(title="Doomed Task")
        raise RuntimeError("Simulation Failure")

    # Verify nothing was persisted
    verify_uow = memory_db_factory.create_unit_of_work()
    with verify_uow:
        assert len(verify_uow.categories.list_active()) == 0
        assert len(verify_uow.tasks.list_active()) == 0


def test_unit_of_work_explicit_rollback(
    memory_db_factory: DatabaseFactory,
) -> None:
    """Verify explicit rollback reverts uncommitted operations."""
    uow = memory_db_factory.create_unit_of_work()

    with uow:
        uow.categories.create("Rollback Target")
        uow.rollback()

    verify_uow = memory_db_factory.create_unit_of_work()
    with verify_uow:
        assert len(verify_uow.categories.list_active()) == 0
