"""Reminder domain entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Reminder:
    """Reminder alert entity scheduled for a specific task."""

    id: str
    task_id: str
    remind_at: str
    created_at: str = ""
    updated_at: str = ""
    synced_at: str | None = None
    is_deleted: int = 0

