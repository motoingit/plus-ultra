"""Business operations for quick launch URLs and local paths."""

from __future__ import annotations

from plus_ultra.models import QuickLink
from plus_ultra.repositories import QuickLinkRepository


class QuickLinkService:
    """Business operations for quick launch URLs and local paths."""

    def __init__(self, link_repo: QuickLinkRepository) -> None:
        self.link_repo = link_repo

    def list_links(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[QuickLink]:
        """List active quick links."""
        return self.link_repo.list_links(category, search_query)

    def get_link(self, link_id: str) -> QuickLink | None:
        """Get link by ID."""
        return self.link_repo.get(link_id)

    def create_link(
        self,
        name: str,
        target_uri: str,
        category: str = "Web",
    ) -> QuickLink:
        """Validate and create quick link."""
        clean_name = name.strip()
        clean_uri = target_uri.strip()
        if not clean_name:
            raise ValueError("Link name cannot be empty.")
        if not clean_uri:
            raise ValueError("Target URI cannot be empty.")
        return self.link_repo.create(
            name=clean_name,
            target_uri=clean_uri,
            category=category,
        )

    def record_click(self, link_id: str) -> bool:
        """Increment click count for link."""
        return self.link_repo.increment_click(link_id)

    def update_quick_link(
        self,
        link_id: str,
        name: str | None = None,
        target_uri: str | None = None,
        category: str | None = None,
    ) -> bool:
        """Update quick link details."""
        clean_name = name.strip() if name is not None else None
        clean_uri = target_uri.strip() if target_uri is not None else None
        if clean_name is not None and not clean_name:
            raise ValueError("Link name cannot be empty.")
        if clean_uri is not None and not clean_uri:
            raise ValueError("Target URI cannot be empty.")
        return self.link_repo.update(
            link_id=link_id,
            name=clean_name,
            target_uri=clean_uri,
            category=category,
        )

    def soft_delete_link(self, link_id: str) -> bool:
        """Soft delete link."""
        return self.link_repo.soft_delete(link_id)
