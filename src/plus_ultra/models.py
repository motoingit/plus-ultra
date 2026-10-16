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


@dataclass(slots=True)
class CodeItem:
    """Snippet, CLI command, syntax reference, or DSA problem."""

    id: str
    category: str  # Snippets, CLI Commands, Syntax Reference, DSA Tracker
    title: str
    content: str = ""
    language: str = "python"
    difficulty: str = "Easy"
    is_done: int = 0
    url: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    synced_at: str | None = None
    is_deleted: int = 0


@dataclass(slots=True)
class Course:
    """Tracked academic course, tutorial, or certification."""

    id: str
    title: str
    platform: str = "Coursera"
    instructor: str = ""
    total_modules: int = 10
    completed_modules: int = 0
    url: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    synced_at: str | None = None
    is_deleted: int = 0


@dataclass(slots=True)
class IdeaDoubt:
    """Project idea or conceptual academic doubt."""

    id: str
    kind: str  # Idea or Doubt
    title: str
    description: str = ""
    tech_stack_or_ref: str = ""
    status: str = "Idea"  # Lifecycle status (Idea/Planned/Completed/Resolved)
    created_at: str = ""
    updated_at: str = ""
    synced_at: str | None = None
    is_deleted: int = 0


@dataclass(slots=True)
class Opportunity:
    """Career or academic opportunity (internship, job, hackathon)."""

    id: str
    title: str
    organization: str
    kind: str = "Internship"  # Internship, Job, Hackathon, Scholarship
    url: str = ""
    deadline: str = ""
    status: str = "Saved"  # Saved, Applied, In Progress, Accepted, Rejected
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    synced_at: str | None = None
    is_deleted: int = 0


@dataclass(slots=True)
class QuickLink:
    """Quick access launcher for web URL or local file/folder."""

    id: str
    name: str
    target_uri: str
    category: str = "Web"  # Web, Local Folder, Local File, Tool
    click_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    synced_at: str | None = None
    is_deleted: int = 0
