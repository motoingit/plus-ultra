"""Domain data models for PLUS-ULTRA (Facade).

Re-exports domain models from plus_ultra.domain.models for 100% backward
compatibility with legacy import paths.
"""

from __future__ import annotations

from plus_ultra.domain.models import (
    AppState,
    Category,
    CodeItem,
    Course,
    IdeaDoubt,
    Opportunity,
    QuickLink,
    Reminder,
    Task,
)

__all__ = [
    "AppState",
    "Category",
    "CodeItem",
    "Course",
    "IdeaDoubt",
    "Opportunity",
    "QuickLink",
    "Reminder",
    "Task",
]
