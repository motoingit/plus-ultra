"""Domain data models for PLUS-ULTRA.

Applies DBMS concepts:
- Relational schema mapping: Strongly-typed dataclasses mirroring SQLite tables.
- Audit & Synchronization metadata: UUID primary keys, ISO-8601 timestamps,
  and soft-delete tracking flags for offline differential synchronization.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Category:
    """Category classification entity for organizing tasks and resources."""

    id: str
    name: str
    color: str = "#4a5568"
    created_at: str = ""
    updated_at: str = ""
    synced_at: str | None = None
    is_deleted: int = 0


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


@dataclass(slots=True)
class AppState:
    """Key-value pair for machine-written local runtime state."""

    key: str
    value: str
