"""Workspace tab domain entities."""

from __future__ import annotations

from dataclasses import dataclass


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
    status: str = "Idea"  # Idea / Planned / Completed / Resolved
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

