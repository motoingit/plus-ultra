"""Business operations for Code snippets and DSA tracking."""

from __future__ import annotations

from plus_ultra.models import CodeItem
from plus_ultra.repositories import CodeRepository


class CodeService:
    """Business operations for Code snippets and DSA tracking."""

    def __init__(self, code_repo: CodeRepository) -> None:
        self.code_repo = code_repo

    def list_items(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[CodeItem]:
        """List active code items."""
        return self.code_repo.list_items(category, search_query)

    def get_item(self, item_id: str) -> CodeItem | None:
        """Get code item by ID."""
        return self.code_repo.get(item_id)

    def create_item(
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
        """Validate and create code item."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Title cannot be empty.")
        return self.code_repo.create(
            category=category,
            title=clean_title,
            content=content,
            language=language,
            difficulty=difficulty,
            is_done=is_done,
            url=url,
            notes=notes,
        )

    def toggle_done(self, item_id: str) -> bool:
        """Toggle DSA problem solved status."""
        return self.code_repo.toggle_done(item_id)

    def update_code_item(
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
        """Update code item attributes."""
        clean_title = title.strip() if title is not None else None
        if clean_title is not None and not clean_title:
            raise ValueError("Title cannot be empty.")
        return self.code_repo.update(
            item_id=item_id,
            category=category,
            title=clean_title,
            content=content,
            language=language,
            difficulty=difficulty,
            url=url,
            notes=notes,
        )

    def soft_delete_item(self, item_id: str) -> bool:
        """Soft delete code item."""
        return self.code_repo.soft_delete(item_id)
