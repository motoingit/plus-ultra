"""Abstract repository contract for Category entities."""

from __future__ import annotations

from typing import Protocol

from plus_ultra.domain.entities.category import Category


class CategoryRepositoryContract(Protocol):
    """Abstract contract for Category repository operations."""

    def create(self, name: str, color: str = "#4a5568") -> Category:
        """Create and persist a new Category entity."""
        ...

    def get_by_id(self, category_id: str) -> Category | None:
        """Fetch category by its unique identifier."""
        ...

    def list_active(self) -> list[Category]:
        """Return all active (non-deleted) categories ordered by name."""
        ...

    def update(
        self, category_id: str, name: str, color: str
    ) -> Category | None:
        """Update category name and color."""
        ...

    def soft_delete(self, category_id: str) -> bool:
        """Mark category as deleted and dissociate attached items."""
        ...

