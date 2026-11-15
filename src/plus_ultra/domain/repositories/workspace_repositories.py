"""Abstract repository contracts for workspace tab features."""

from __future__ import annotations

from typing import Protocol

from plus_ultra.domain.entities.workspace import (
    CodeItem,
    Course,
    IdeaDoubt,
    Opportunity,
    QuickLink,
)


class CodeRepositoryContract(Protocol):
    """Abstract contract for code snippet / reference repository."""

    def list_items(
        self,
        category: str | None = None,
        search_query: str | None = None,
        difficulty: str | None = None,
        done_filter: str = "all",
    ) -> list[CodeItem]:
        """List code items matching optional filters."""
        ...

    def get(self, item_id: str) -> CodeItem | None:
        """Fetch code item by ID."""
        ...

    def create(
        self,
        category: str,
        title: str,
        content: str = "",
        language: str = "python",
        difficulty: str = "Easy",
        is_done: int = 0,
        url: str = "",
        notes: str = "",
    ) -> CodeItem:
        """Create new code item."""
        ...

    def toggle_done(self, item_id: str) -> bool:
        """Toggle completion status."""
        ...

    def update(
        self,
        item_id: str,
        category: str | None = None,
        title: str | None = None,
        content: str | None = None,
        language: str | None = None,
        difficulty: str | None = None,
        url: str | None = None,
        notes: str | None = None,
    ) -> bool:
        """Update code item details."""
        ...

    def soft_delete(self, item_id: str) -> bool:
        """Soft-delete code item."""
        ...


class CourseRepositoryContract(Protocol):
    """Abstract contract for course tracker repository."""

    def list_courses(
        self,
        platform: str | None = None,
        search_query: str | None = None,
    ) -> list[Course]:
        """List tracked courses."""
        ...

    def get(self, course_id: str) -> Course | None:
        """Fetch course by ID."""
        ...

    def create(
        self,
        title: str,
        platform: str = "Coursera",
        instructor: str = "",
        total_modules: int = 10,
        completed_modules: int = 0,
        url: str = "",
        notes: str = "",
    ) -> Course:
        """Create new course entry."""
        ...

    def increment_module(self, course_id: str) -> bool:
        """Increment completed module progress."""
        ...

    def update(
        self,
        course_id: str,
        title: str | None = None,
        platform: str | None = None,
        instructor: str | None = None,
        total_modules: int | None = None,
        completed_modules: int | None = None,
        url: str | None = None,
        notes: str | None = None,
    ) -> bool:
        """Update course details."""
        ...

    def soft_delete(self, course_id: str) -> bool:
        """Soft-delete course entry."""
        ...


class IdeaDoubtRepositoryContract(Protocol):
    """Abstract contract for ideas and doubts repository."""

    def list_items(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[IdeaDoubt]:
        """List idea and doubt items."""
        ...

    def get(self, item_id: str) -> IdeaDoubt | None:
        """Fetch item by ID."""
        ...

    def create(
        self,
        kind: str,
        title: str,
        description: str = "",
        tech_stack_or_ref: str = "",
        status: str = "Idea",
    ) -> IdeaDoubt:
        """Create new idea or doubt."""
        ...

    def update_status(self, item_id: str, new_status: str) -> bool:
        """Update status transition."""
        ...

    def update(
        self,
        item_id: str,
        title: str | None = None,
        description: str | None = None,
        tech_stack_or_ref: str | None = None,
        status: str | None = None,
    ) -> bool:
        """Update item details."""
        ...

    def soft_delete(self, item_id: str) -> bool:
        """Soft-delete item."""
        ...


class OpportunityRepositoryContract(Protocol):
    """Abstract contract for internship/job opportunities repository."""

    def list_opportunities(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[Opportunity]:
        """List tracked career opportunities."""
        ...

    def get(self, opp_id: str) -> Opportunity | None:
        """Fetch opportunity by ID."""
        ...

    def create(
        self,
        title: str,
        organization: str,
        kind: str = "Internship",
        url: str = "",
        deadline: str = "",
        status: str = "Saved",
        notes: str = "",
    ) -> Opportunity:
        """Create new opportunity."""
        ...

    def update_status(self, opp_id: str, new_status: str) -> bool:
        """Update opportunity status."""
        ...

    def update(
        self,
        opp_id: str,
        title: str | None = None,
        organization: str | None = None,
        kind: str | None = None,
        url: str | None = None,
        deadline: str | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> bool:
        """Update opportunity details."""
        ...

    def soft_delete(self, opp_id: str) -> bool:
        """Soft-delete opportunity."""
        ...


class QuickLinkRepositoryContract(Protocol):
    """Abstract contract for quick launcher links repository."""

    def list_links(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[QuickLink]:
        """List quick access links."""
        ...

    def get(self, link_id: str) -> QuickLink | None:
        """Fetch quick link by ID."""
        ...

    def create(
        self,
        name: str,
        target_uri: str,
        category: str = "Web",
    ) -> QuickLink:
        """Create new quick link."""
        ...

    def increment_click(self, link_id: str) -> bool:
        """Increment usage click counter."""
        ...

    def update(
        self,
        link_id: str,
        name: str | None = None,
        target_uri: str | None = None,
        category: str | None = None,
    ) -> bool:
        """Update quick link details."""
        ...

    def soft_delete(self, link_id: str) -> bool:
        """Soft-delete quick link."""
        ...


__all__ = [
    "CodeRepositoryContract",
    "CourseRepositoryContract",
    "IdeaDoubtRepositoryContract",
    "OpportunityRepositoryContract",
    "QuickLinkRepositoryContract",
]
