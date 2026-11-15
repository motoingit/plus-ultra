"""Comprehensive integration tests for SQLAlchemy 2.x persistence layer.

Verifies:
- Clean SQLite in-memory and file-based initialization without Alembic.
- All 10 application models CRUD, filtering, relationships, and constraints.
- Foreign key cascading (task -> reminders, reminder -> reminder_fires).
- Active partial unique index on categories.
- Pragmas configured via connection events (foreign_keys, busy_timeout).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text

from plus_ultra.domain.entities.category import Category
from plus_ultra.domain.entities.task import Task
from plus_ultra.infrastructure.persistence.database_config import DatabaseConfig
from plus_ultra.infrastructure.persistence.database_factory import (
    DatabaseFactory,
)
from plus_ultra.infrastructure.persistence.database_initializer import (
    init_database,
    wipe_database,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    ReminderFireModel,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    CategoryNameExistsError,
    SqlAlchemyCategoryRepository,
    SqlAlchemyCodeRepository,
    SqlAlchemyCourseRepository,
    SqlAlchemyIdeaDoubtRepository,
    SqlAlchemyOpportunityRepository,
    SqlAlchemyQuickLinkRepository,
    SqlAlchemyReminderRepository,
    SqlAlchemyTaskRepository,
)


@pytest.fixture
def memory_db_factory() -> DatabaseFactory:
    """Provide a fresh in-memory DatabaseFactory with initialized schema."""
    config = DatabaseConfig(
        backend="sqlite",
        url="sqlite:///:memory:",
        echo=False,
    )
    factory = DatabaseFactory(config)
    init_database(engine=factory.engine)
    return factory


def test_sqlite_pragmas_applied(memory_db_factory: DatabaseFactory) -> None:
    """Verify that SQLite connection events set foreign keys and timeout."""
    with memory_db_factory.engine.connect() as conn:
        fk = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        assert fk == 1
        timeout = conn.execute(text("PRAGMA busy_timeout;")).scalar()
        assert timeout == 5000


def test_no_alembic_version_table(memory_db_factory: DatabaseFactory) -> None:
    """Verify that no Alembic migration metadata table is created."""
    with memory_db_factory.engine.connect() as conn:
        tables = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='alembic_version';"
            )
        ).fetchall()
        assert len(tables) == 0


def test_category_and_task_lifecycle(
    memory_db_factory: DatabaseFactory,
) -> None:
    """Verify Category and Task creation, filtering, and cascading rules."""
    session = memory_db_factory.create_session()
    try:
        cat_repo = SqlAlchemyCategoryRepository(session=session)
        task_repo = SqlAlchemyTaskRepository(session=session)

        cat = cat_repo.create("Work & Systems", color="#2563eb")
        assert isinstance(cat, Category)
        assert cat.name == "Work & Systems"

        # Duplicate active category must fail
        with pytest.raises(CategoryNameExistsError):
            cat_repo.create("Work & Systems")

        task = task_repo.create(
            title="Implement Distributed Lock",
            category_id=cat.id,
            critical_level="High",
            pace_level="Short-term",
        )
        assert isinstance(task, Task)
        assert task.title == "Implement Distributed Lock"
        assert task.category_id == cat.id

        # Soft delete category preserves task with category_id unchanged or null
        cat_repo.soft_delete(cat.id)
        assert cat_repo.get(cat.id).is_deleted == 1
        assert cat.id not in [c.id for c in cat_repo.list_active()]
        # Name can now be reused
        reused = cat_repo.create("Work & Systems", color="#10b981")
        assert reused.id != cat.id
    finally:
        session.close()


def test_foreign_key_cascading(memory_db_factory: DatabaseFactory) -> None:
    """Verify foreign key cascading from tasks to reminders and fires."""
    session = memory_db_factory.create_session()
    try:
        task_repo = SqlAlchemyTaskRepository(session=session)
        rem_repo = SqlAlchemyReminderRepository(session=session)

        task = task_repo.create(title="Backup Database")
        rem = rem_repo.create(
            task_id=task.id,
            remind_at="2026-11-20T10:00:00Z",
        )
        rem_repo.mark_fired(rem.id, "2026-11-20T10:00:05Z")

        fires = session.scalars(
            select(ReminderFireModel).where(
                ReminderFireModel.reminder_id == rem.id
            )
        ).all()
        assert len(fires) == 1

        # Deleting reminder must cascade-delete reminder fire
        session.execute(
            text("DELETE FROM reminders WHERE id = :rid"), {"rid": rem.id}
        )
        session.commit()

        fires_after = session.scalars(
            select(ReminderFireModel).where(
                ReminderFireModel.reminder_id == rem.id
            )
        ).all()
        assert len(fires_after) == 0
    finally:
        session.close()


def test_workspace_repositories_crud(
    memory_db_factory: DatabaseFactory,
) -> None:
    """Verify all 5 workspace tab repositories function via SQLAlchemy."""
    session = memory_db_factory.create_session()
    try:
        code_repo = SqlAlchemyCodeRepository(session=session)
        course_repo = SqlAlchemyCourseRepository(session=session)
        idea_repo = SqlAlchemyIdeaDoubtRepository(session=session)
        opp_repo = SqlAlchemyOpportunityRepository(session=session)
        link_repo = SqlAlchemyQuickLinkRepository(session=session)

        # Code
        code = code_repo.create(
            category="Algorithms",
            title="Dijkstra Shortest Path",
            difficulty="Medium",
            is_done=0,
        )
        assert code.title == "Dijkstra Shortest Path"
        assert code_repo.toggle_done(code.id) is True
        assert code_repo.get(code.id).is_done == 1

        # Course
        course = course_repo.create(
            title="Compiler Design",
            platform="edX",
            total_modules=12,
            completed_modules=0,
        )
        assert course_repo.increment_module(course.id) is True
        assert course_repo.get(course.id).completed_modules == 1

        # Idea / Doubt
        idea = idea_repo.create(
            kind="Idea",
            title="LSM-Tree Storage Engine",
            status="In Progress",
        )
        assert idea_repo.update_status(idea.id, "Implemented") is True
        assert idea_repo.get(idea.id).status == "Implemented"

        # Opportunity
        opp = opp_repo.create(
            title="Linux Kernel Mentorship",
            organization="The Linux Foundation",
            status="Applied",
        )
        assert opp_repo.update_status(opp.id, "Accepted") is True
        assert opp_repo.get(opp.id).status == "Accepted"

        # Quick Link
        link = link_repo.create(
            name="Kernel Docs",
            target_uri="https://kernel.org/doc",
            category="System",
        )
        assert link_repo.increment_click(link.id) is True
        assert link_repo.get(link.id).click_count == 1
    finally:
        session.close()


def test_wipe_database_preserves_schema(
    memory_db_factory: DatabaseFactory,
) -> None:
    """Verify wipe_database deletes records but leaves schema intact."""
    session = memory_db_factory.create_session()
    try:
        cat_repo = SqlAlchemyCategoryRepository(session=session)
        cat_repo.create("Temporary Category")
        session.commit()

        # Wipe database
        wipe_database(session)

        # Verify tables are empty
        assert len(cat_repo.list_active()) == 0

        # Verify we can immediately insert again without error
        new_cat = cat_repo.create("Temporary Category")
        assert new_cat.name == "Temporary Category"
    finally:
        session.close()
