"""Business operations for category management."""

from __future__ import annotations

from plus_ultra.models import Category
from plus_ultra.repositories import CategoryRepository


class CategoryService:
    """Business operations for category management."""

    def __init__(self, category_repo: CategoryRepository) -> None:
        self.category_repo = category_repo

    def create_category(self, name: str, color: str = "#4a5568") -> Category:
        """Create a new category."""
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Category name cannot be empty.")
        return self.category_repo.create(name=clean_name, color=color)

    def get_category(self, category_id: str) -> Category | None:
        """Fetch category by ID if active."""
        cat = self.category_repo.get_by_id(category_id)
        return cat if cat and not cat.is_deleted else None

    def update_category(
        self, category_id: str, name: str, color: str
    ) -> Category | None:
        """Update category name and color."""
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Category name cannot be empty.")
        return self.category_repo.update(
            category_id=category_id, name=clean_name, color=color
        )

    def soft_delete_category(self, category_id: str) -> bool:
        """Soft-delete category and nullify linked tasks' category_id."""
        return self.category_repo.soft_delete(category_id)

    def list_active(self) -> list[Category]:
        """List all active categories ordered alphabetically."""
        return self.category_repo.list_active()

    def list_categories(self) -> list[Category]:
        """Alias for list_active."""
        return self.list_active()
