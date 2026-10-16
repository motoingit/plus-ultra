"""Business operations for Ideas and Doubts tracking."""

from __future__ import annotations

from plus_ultra.models import IdeaDoubt
from plus_ultra.repositories import IdeaDoubtRepository


class IdeaDoubtService:
    """Business operations for Ideas and Doubts tracking."""

    IDEA_STATUSES = ("Idea", "Planned", "In Progress", "Completed")
    DOUBT_STATUSES = ("Open", "Resolved")

    def __init__(self, idea_doubt_repo: IdeaDoubtRepository) -> None:
        self.idea_doubt_repo = idea_doubt_repo

    def list_items(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[IdeaDoubt]:
        """List active ideas and doubts."""
        return self.idea_doubt_repo.list_items(kind, status, search_query)

    def get_item(self, item_id: str) -> IdeaDoubt | None:
        """Get item by ID."""
        return self.idea_doubt_repo.get(item_id)

    def create_item(
        self,
        kind: str,
        title: str,
        description: str = "",
        tech_stack_or_ref: str = "",
        status: str = "Idea",
    ) -> IdeaDoubt:
        """Validate and create idea or doubt."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Title cannot be empty.")
        return self.idea_doubt_repo.create(
            kind=kind,
            title=clean_title,
            description=description,
            tech_stack_or_ref=tech_stack_or_ref,
            status=status,
        )

    def advance_status(self, item_id: str) -> bool:
        """Advance status to next stage or toggle open/resolved."""
        item = self.idea_doubt_repo.get(item_id)
        if not item:
            return False

        if item.kind == "Idea":
            try:
                curr_idx = self.IDEA_STATUSES.index(item.status)
                next_idx = (curr_idx + 1) % len(self.IDEA_STATUSES)
                new_status = self.IDEA_STATUSES[next_idx]
            except ValueError:
                new_status = "In Progress"
        else:
            new_status = "Resolved" if item.status == "Open" else "Open"

        return self.idea_doubt_repo.update_status(item_id, new_status)

    def update_idea_doubt(
        self,
        item_id: str,
        title: str | None = None,
        kind: str | None = None,
        description: str | None = None,
        tech_stack_or_ref: str | None = None,
        status: str | None = None,
    ) -> bool:
        """Update idea or doubt details."""
        clean_title = title.strip() if title is not None else None
        if clean_title is not None and not clean_title:
            raise ValueError("Title cannot be empty.")
        return self.idea_doubt_repo.update(
            item_id=item_id,
            title=clean_title,
            kind=kind,
            description=description,
            tech_stack_or_ref=tech_stack_or_ref,
            status=status,
        )

    def soft_delete_item(self, item_id: str) -> bool:
        """Soft delete item."""
        return self.idea_doubt_repo.soft_delete(item_id)
