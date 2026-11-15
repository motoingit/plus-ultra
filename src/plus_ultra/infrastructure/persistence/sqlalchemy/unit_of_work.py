"""SQLAlchemy Unit of Work implementation."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from plus_ultra.application.interfaces.unit_of_work import UnitOfWork
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyAppStateRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyCodeRepository,
    SqlAlchemyCourseRepository,
    SqlAlchemyIdeaDoubtRepository,
    SqlAlchemyOpportunityRepository,
    SqlAlchemyQuickLinkRepository,
    SqlAlchemyReminderRepository,
    SqlAlchemyTaskRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy Unit of Work coordinating transactions across repositories."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory
        self.session: Session | None = None

        self.categories: SqlAlchemyCategoryRepository
        self.tasks: SqlAlchemyTaskRepository
        self.reminders: SqlAlchemyReminderRepository
        self.app_state: SqlAlchemyAppStateRepository
        self.code_items: SqlAlchemyCodeRepository
        self.courses: SqlAlchemyCourseRepository
        self.ideas_doubts: SqlAlchemyIdeaDoubtRepository
        self.opportunities: SqlAlchemyOpportunityRepository
        self.quick_links: SqlAlchemyQuickLinkRepository

    def __enter__(self) -> Self:
        """Create session and initialize transactional repositories."""
        self.session = self.session_factory()

        # Repositories run with autocommit=False within a Unit of Work
        self.categories = SqlAlchemyCategoryRepository(
            self.session, autocommit=False
        )
        self.tasks = SqlAlchemyTaskRepository(self.session, autocommit=False)
        self.reminders = SqlAlchemyReminderRepository(
            self.session, autocommit=False
        )
        self.app_state = SqlAlchemyAppStateRepository(
            self.session, autocommit=False
        )
        self.code_items = SqlAlchemyCodeRepository(
            self.session, autocommit=False
        )
        self.courses = SqlAlchemyCourseRepository(
            self.session, autocommit=False
        )
        self.ideas_doubts = SqlAlchemyIdeaDoubtRepository(
            self.session, autocommit=False
        )
        self.opportunities = SqlAlchemyOpportunityRepository(
            self.session, autocommit=False
        )
        self.quick_links = SqlAlchemyQuickLinkRepository(
            self.session, autocommit=False
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit unit of work scope, rolling back on error and closing."""
        if self.session is not None:
            try:
                if exc_type is not None:
                    self.rollback()
            finally:
                self.session.close()
                self.session = None

    def commit(self) -> None:
        """Commit current transaction."""
        if self.session is not None:
            self.session.commit()

    def rollback(self) -> None:
        """Roll back current transaction."""
        if self.session is not None:
            self.session.rollback()
