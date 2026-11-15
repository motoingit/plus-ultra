"""Domain repository contracts package."""

from __future__ import annotations

from plus_ultra.domain.repositories.app_state_repository import (
    AppStateRepositoryContract,
)
from plus_ultra.domain.repositories.category_repository import (
    CategoryRepositoryContract,
)
from plus_ultra.domain.repositories.reminder_repository import (
    ReminderRepositoryContract,
)
from plus_ultra.domain.repositories.task_repository import (
    TaskRepositoryContract,
)
from plus_ultra.domain.repositories.workspace_repositories import (
    CodeRepositoryContract,
    CourseRepositoryContract,
    IdeaDoubtRepositoryContract,
    OpportunityRepositoryContract,
    QuickLinkRepositoryContract,
)

__all__ = [
    "AppStateRepositoryContract",
    "CategoryRepositoryContract",
    "CodeRepositoryContract",
    "CourseRepositoryContract",
    "IdeaDoubtRepositoryContract",
    "OpportunityRepositoryContract",
    "QuickLinkRepositoryContract",
    "ReminderRepositoryContract",
    "TaskRepositoryContract",
]

