"""Task domain entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Task:
    """Core task entity representing to-dos and deadlines."""

    id: str
    title: str
    category_id: str | None = None
    description: str = ""
    due_date: str | None = None
    status: str = "Pending"
    task_label: str = "College"
    critical_level: str = "Medium"
    pace_level: str = "Short-term"
    is_google_task: bool = False
    created_at: str = ""
    updated_at: str = ""
    synced_at: str | None = None
    is_deleted: int = 0

