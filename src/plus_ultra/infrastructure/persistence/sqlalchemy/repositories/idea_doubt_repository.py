"""SQLAlchemy repository implementation for IdeaDoubt entities."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from plus_ultra.domain.entities.workspace import IdeaDoubt
from plus_ultra.domain.repositories.workspace_repositories import (
    IdeaDoubtRepositoryContract,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.mappers import (
    idea_doubt_to_domain,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    IdeaDoubtModel,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories.base import (
    SqlAlchemyRepositoryBase,
    _now_utc,
)


class SqlAlchemyIdeaDoubtRepository(
    SqlAlchemyRepositoryBase, IdeaDoubtRepositoryContract
):
    """SQLAlchemy repository for ideas and doubts tracker."""

    def __init__(self, session: Session, autocommit: bool = True) -> None:
        super().__init__(session=session, autocommit=autocommit)

    def list_items(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[IdeaDoubt]:
        """List active ideas and doubts matching optional filters."""
        stmt = select(IdeaDoubtModel).where(IdeaDoubtModel.is_deleted == 0)

        if kind and kind != "All":
            stmt = stmt.where(IdeaDoubtModel.kind == kind)

        if status and status != "All":
            stmt = stmt.where(IdeaDoubtModel.status == status)

        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            stmt = stmt.where(
                or_(
                    IdeaDoubtModel.title.ilike(term),
                    IdeaDoubtModel.description.ilike(term),
                    IdeaDoubtModel.tech_stack_or_ref.ilike(term),
                )
            )

        stmt = stmt.order_by(IdeaDoubtModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [idea_doubt_to_domain(m) for m in models]

    def get(self, item_id: str) -> IdeaDoubt | None:
        """Fetch item by ID."""
        model = self.session.get(IdeaDoubtModel, item_id)
        return idea_doubt_to_domain(model) if model else None

    def create(
        self,
        kind: str,
        title: str,
        description: str = "",
        tech_stack_or_ref: str = "",
        status: str = "Idea",
    ) -> IdeaDoubt:
        """Create new idea or doubt."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Title cannot be empty.")

        item_id = str(uuid.uuid4())
        now = _now_utc()
        model = IdeaDoubtModel(
            id=item_id,
            kind=kind,
            title=clean_title,
            description=description,
            tech_stack_or_ref=tech_stack_or_ref,
            status=status,
            created_at=now,
            updated_at=now,
            is_deleted=0,
        )
        self.session.add(model)
        self._commit_or_flush()
        return idea_doubt_to_domain(model)

    def update_status(self, item_id: str, new_status: str) -> bool:
        """Update status transition."""
        model = self.session.get(IdeaDoubtModel, item_id)
        if model is None or model.is_deleted:
            return False
        model.status = new_status
        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

    def update(
        self,
        item_id: str,
        title: str | None = None,
        description: str | None = None,
        tech_stack_or_ref: str | None = None,
        status: str | None = None,
    ) -> bool:
        """Update item details."""
        model = self.session.get(IdeaDoubtModel, item_id)
        if model is None or model.is_deleted:
            return False

        has_change = False
        if title is not None:
            clean = title.strip()
            if not clean:
                raise ValueError("Title cannot be empty.")
            model.title = clean
            has_change = True
        if description is not None:
            model.description = description
            has_change = True
        if tech_stack_or_ref is not None:
            model.tech_stack_or_ref = tech_stack_or_ref
            has_change = True
        if status is not None:
            model.status = status
            has_change = True

        if not has_change:
            return False

        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

    def soft_delete(self, item_id: str) -> bool:
        """Soft-delete item."""
        model = self.session.get(IdeaDoubtModel, item_id)
        if model is None or model.is_deleted:
            return False
        model.is_deleted = 1
        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

