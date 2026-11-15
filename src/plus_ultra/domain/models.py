"""Domain data models for PLUS-ULTRA.

Re-exports domain entities for clean architectural organization
and backward compatibility. Plain Python dataclasses with zero
database coupling.
"""

from __future__ import annotations

from plus_ultra.domain.entities import (
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
