"""Abstract Unit of Work contract."""

from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from plus_ultra.domain.repositories import (
    AppStateRepositoryContract,
    CategoryRepositoryContract,
    CodeRepositoryContract,
    CourseRepositoryContract,
    IdeaDoubtRepositoryContract,
    OpportunityRepositoryContract,
    QuickLinkRepositoryContract,
    ReminderRepositoryContract,
    TaskRepositoryContract,
)


class UnitOfWork(Protocol):
    """Abstract Unit of Work coordinating atomic multi-repository changes."""

    categories: CategoryRepositoryContract
    tasks: TaskRepositoryContract
    reminders: ReminderRepositoryContract
    app_state: AppStateRepositoryContract
    code_items: CodeRepositoryContract
    courses: CourseRepositoryContract
    ideas_doubts: IdeaDoubtRepositoryContract
    opportunities: OpportunityRepositoryContract
    quick_links: QuickLinkRepositoryContract

    def __enter__(self) -> Self:
        """Begin transaction / unit-of-work scope."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close unit-of-work scope, rolling back on error."""
        ...

    def commit(self) -> None:
        """Commit current transactional changes."""
        ...

    def rollback(self) -> None:
        """Rollback uncommitted changes."""
        ...


UnitOfWorkFactory = Callable[[], UnitOfWork]
