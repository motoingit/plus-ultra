"""Repositories package for PLUS-ULTRA.

Encapsulates data access and persistence operations for all domain models.
"""

from __future__ import annotations

from plus_ultra.repositories.app_state_repository import AppStateRepository
from plus_ultra.repositories.base import _now_utc
from plus_ultra.repositories.category_repository import (
    CategoryRepository,
    _row_to_category,
)
from plus_ultra.repositories.code_repository import (
    CodeRepository,
    _row_to_code_item,
)
from plus_ultra.repositories.course_repository import (
    CourseRepository,
    _row_to_course,
)
from plus_ultra.repositories.idea_doubt_repository import (
    IdeaDoubtRepository,
    _row_to_idea_doubt,
)
from plus_ultra.repositories.opportunity_repository import (
    OpportunityRepository,
    _row_to_opportunity,
)
from plus_ultra.repositories.quick_link_repository import (
    QuickLinkRepository,
    _row_to_quick_link,
)
from plus_ultra.repositories.reminder_repository import (
    ReminderRepository,
    _row_to_reminder,
)
from plus_ultra.repositories.task_repository import (
    TaskRepository,
    _row_to_task,
)

__all__ = [
    "AppStateRepository",
    "CategoryRepository",
    "CodeRepository",
    "CourseRepository",
    "IdeaDoubtRepository",
    "OpportunityRepository",
    "QuickLinkRepository",
    "ReminderRepository",
    "TaskRepository",
    "_now_utc",
    "_row_to_category",
    "_row_to_code_item",
    "_row_to_course",
    "_row_to_idea_doubt",
    "_row_to_opportunity",
    "_row_to_quick_link",
    "_row_to_reminder",
    "_row_to_task",
]
