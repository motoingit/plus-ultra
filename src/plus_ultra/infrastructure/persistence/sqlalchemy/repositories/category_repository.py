"""SQLAlchemy implementation of CategoryRepositoryContract."""

from __future__ import annotations

import sqlite3
import uuid

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plus_ultra.domain.entities.category import Category
from plus_ultra.domain.repositories.category_repository import (
    CategoryRepositoryContract,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.mappers import (
    category_to_domain,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    CategoryModel,
    TaskModel,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories.base import (
    SqlAlchemyRepositoryBase,
    _now_utc,
)


class CategoryNameExistsError(sqlite3.IntegrityError, IntegrityError):
    """Exception raised when an active category with the same name exists."""

    def __init__(self, message: str) -> None:
        sqlite3.IntegrityError.__init__(self, message)
        IntegrityError.__init__(
            self,
            statement=message,
            params=None,
            orig=Exception(message),
        )


class SqlAlchemyCategoryRepository(
    SqlAlchemyRepositoryBase, CategoryRepositoryContract
):
    """SQLAlchemy repository for categories."""

    def __init__(self, session: Session, autocommit: bool = True) -> None:
        super().__init__(session=session, autocommit=autocommit)

    def create(self, name: str, color: str = "#4a5568") -> Category:
        """Create and persist a new category entity."""
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Category name cannot be empty.")

        # Check unique active category name constraint
        existing = self.session.scalars(
            select(CategoryModel).where(
                CategoryModel.name == clean_name,
                CategoryModel.is_deleted == 0,
            )
        ).first()
        if existing is not None:
            raise CategoryNameExistsError(
                f"UNIQUE constraint failed: category '{clean_name}' exists."
            )

        cat_id = str(uuid.uuid4())
        now = _now_utc()
        model = CategoryModel(
            id=cat_id,
            name=clean_name,
            color=color,
            created_at=now,
            updated_at=now,
            is_deleted=0,
        )
        self.session.add(model)
        self._commit_or_flush()
        return category_to_domain(model)

    def get_by_id(self, category_id: str) -> Category | None:
        """Fetch category by ID, including soft-deleted ones."""
        model = self.session.get(CategoryModel, category_id)
        return category_to_domain(model) if model else None

    get = get_by_id

    def list_active(self) -> list[Category]:
        """Return all active (non-deleted) categories ordered by name."""
        stmt = (
            select(CategoryModel)
            .where(CategoryModel.is_deleted == 0)
            .order_by(CategoryModel.name.asc())
        )
        models = self.session.scalars(stmt).all()
        return [category_to_domain(m) for m in models]

    def update(
        self, category_id: str, name: str, color: str
    ) -> Category | None:
        """Update category name and color; sets updated_at timestamp."""
        model = self.session.get(CategoryModel, category_id)
        if model is None or model.is_deleted:
            return None

        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Category name cannot be empty.")

        now = _now_utc()
        model.name = clean_name
        model.color = color
        model.updated_at = now
        self._commit_or_flush()
        return category_to_domain(model)

    def soft_delete(self, category_id: str) -> bool:
        """Soft-delete category and nullify linked tasks' category_id."""
        model = self.session.get(CategoryModel, category_id)
        if model is None or model.is_deleted:
            return False

        now = _now_utc()
        model.is_deleted = 1
        model.updated_at = now

        # Cascade: set tasks.category_id to NULL
        self.session.execute(
            update(TaskModel)
            .where(
                TaskModel.category_id == category_id,
                TaskModel.is_deleted == 0,
            )
            .values(category_id=None, updated_at=now)
        )
        self._commit_or_flush()
        return True
