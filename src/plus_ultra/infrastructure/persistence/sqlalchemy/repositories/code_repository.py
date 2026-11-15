"""SQLAlchemy repository implementation for CodeItem entities."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from plus_ultra.domain.entities.workspace import CodeItem
from plus_ultra.domain.repositories.workspace_repositories import (
    CodeRepositoryContract,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.mappers import (
    code_item_to_domain,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    CodeItemModel,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories.base import (
    SqlAlchemyRepositoryBase,
    _now_utc,
)


class SqlAlchemyCodeRepository(
    SqlAlchemyRepositoryBase, CodeRepositoryContract
):
    """SQLAlchemy repository for code snippets and problems."""

    def __init__(self, session: Session, autocommit: bool = True) -> None:
        super().__init__(session=session, autocommit=autocommit)

    def list_items(
        self,
        category: str | None = None,
        search_query: str | None = None,
        difficulty: str | None = None,
        done_filter: str = "all",
    ) -> list[CodeItem]:
        """List active code items with optional filters."""
        stmt = select(CodeItemModel).where(CodeItemModel.is_deleted == 0)

        if category and category != "All":
            stmt = stmt.where(CodeItemModel.category == category)

        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            stmt = stmt.where(
                or_(
                    CodeItemModel.title.ilike(term),
                    CodeItemModel.content.ilike(term),
                    CodeItemModel.notes.ilike(term),
                )
            )

        if difficulty and difficulty != "All":
            stmt = stmt.where(CodeItemModel.difficulty == difficulty)

        if done_filter == "done":
            stmt = stmt.where(CodeItemModel.is_done == 1)
        elif done_filter == "todo":
            stmt = stmt.where(CodeItemModel.is_done == 0)

        stmt = stmt.order_by(CodeItemModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [code_item_to_domain(m) for m in models]

    def get(self, item_id: str) -> CodeItem | None:
        """Fetch item by ID."""
        model = self.session.get(CodeItemModel, item_id)
        return code_item_to_domain(model) if model else None

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
        """Create a new code item."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Title cannot be empty.")

        item_id = str(uuid.uuid4())
        now = _now_utc()
        model = CodeItemModel(
            id=item_id,
            category=category,
            title=clean_title,
            content=content,
            language=language,
            difficulty=difficulty,
            is_done=is_done,
            url=url,
            notes=notes,
            created_at=now,
            updated_at=now,
            is_deleted=0,
        )
        self.session.add(model)
        self._commit_or_flush()
        return code_item_to_domain(model)

    def toggle_done(self, item_id: str) -> bool:
        """Toggle is_done status between 0 and 1."""
        model = self.session.get(CodeItemModel, item_id)
        if model is None or model.is_deleted:
            return False
        model.is_done = 0 if model.is_done else 1
        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

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
        model = self.session.get(CodeItemModel, item_id)
        if model is None or model.is_deleted:
            return False

        has_change = False
        if category is not None:
            model.category = category
            has_change = True
        if title is not None:
            clean = title.strip()
            if not clean:
                raise ValueError("Title cannot be empty.")
            model.title = clean
            has_change = True
        if content is not None:
            model.content = content
            has_change = True
        if language is not None:
            model.language = language
            has_change = True
        if difficulty is not None:
            model.difficulty = difficulty
            has_change = True
        if url is not None:
            model.url = url
            has_change = True
        if notes is not None:
            model.notes = notes
            has_change = True

        if not has_change:
            return False

        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

    def soft_delete(self, item_id: str) -> bool:
        """Soft-delete item."""
        model = self.session.get(CodeItemModel, item_id)
        if model is None or model.is_deleted:
            return False
        model.is_deleted = 1
        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

