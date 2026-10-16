"""Repository facade module for backward compatibility.

Re-exports repository classes and row mappers from `plus_ultra.repositories`.
"""

from __future__ import annotations

from plus_ultra.repositories import (
    AppStateRepository,
    CategoryRepository,
    CodeRepository,
    CourseRepository,
    IdeaDoubtRepository,
    OpportunityRepository,
    QuickLinkRepository,
    ReminderRepository,
    TaskRepository,
    _now_utc,
    _row_to_category,
    _row_to_code_item,
    _row_to_course,
    _row_to_idea_doubt,
    _row_to_opportunity,
    _row_to_quick_link,
    _row_to_reminder,
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
