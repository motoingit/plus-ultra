"""SQLAlchemy repository implementation for QuickLink entities."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from plus_ultra.domain.entities.workspace import QuickLink
from plus_ultra.domain.repositories.workspace_repositories import (
    QuickLinkRepositoryContract,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.mappers import (
    quick_link_to_domain,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    QuickLinkModel,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories.base import (
    SqlAlchemyRepositoryBase,
    _now_utc,
)


class SqlAlchemyQuickLinkRepository(
    SqlAlchemyRepositoryBase, QuickLinkRepositoryContract
):
    """SQLAlchemy repository for quick launcher links."""

    def __init__(self, session: Session, autocommit: bool = True) -> None:
        super().__init__(session=session, autocommit=autocommit)

    def list_links(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[QuickLink]:
        """List active quick links matching optional filters."""
        stmt = select(QuickLinkModel).where(QuickLinkModel.is_deleted == 0)

        if category and category != "All":
            stmt = stmt.where(QuickLinkModel.category == category)

        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            stmt = stmt.where(
                or_(
                    QuickLinkModel.name.ilike(term),
                    QuickLinkModel.target_uri.ilike(term),
                )
            )

        stmt = stmt.order_by(
            QuickLinkModel.click_count.desc(),
            QuickLinkModel.created_at.desc(),
        )
        models = self.session.scalars(stmt).all()
        return [quick_link_to_domain(m) for m in models]

    def get(self, link_id: str) -> QuickLink | None:
        """Fetch quick link by ID."""
        model = self.session.get(QuickLinkModel, link_id)
        return quick_link_to_domain(model) if model else None

    def create(
        self,
        name: str,
        target_uri: str,
        category: str = "Web",
    ) -> QuickLink:
        """Create new quick link."""
        clean_name = name.strip()
        clean_uri = target_uri.strip()
        if not clean_name:
            raise ValueError("Name cannot be empty.")
        if not clean_uri:
            raise ValueError("Target URI cannot be empty.")

        link_id = str(uuid.uuid4())
        now = _now_utc()
        model = QuickLinkModel(
            id=link_id,
            name=clean_name,
            target_uri=clean_uri,
            category=category,
            click_count=0,
            created_at=now,
            updated_at=now,
            is_deleted=0,
        )
        self.session.add(model)
        self._commit_or_flush()
        return quick_link_to_domain(model)

    def increment_click(self, link_id: str) -> bool:
        """Increment usage click counter."""
        model = self.session.get(QuickLinkModel, link_id)
        if model is None or model.is_deleted:
            return False
        model.click_count += 1
        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

    def update(
        self,
        link_id: str,
        name: str | None = None,
        target_uri: str | None = None,
        category: str | None = None,
    ) -> bool:
        """Update quick link details."""
        model = self.session.get(QuickLinkModel, link_id)
        if model is None or model.is_deleted:
            return False

        has_change = False
        if name is not None:
            clean = name.strip()
            if not clean:
                raise ValueError("Name cannot be empty.")
            model.name = clean
            has_change = True
        if target_uri is not None:
            clean_uri = target_uri.strip()
            if not clean_uri:
                raise ValueError("Target URI cannot be empty.")
            model.target_uri = clean_uri
            has_change = True
        if category is not None:
            model.category = category
            has_change = True

        if not has_change:
            return False

        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

    def soft_delete(self, link_id: str) -> bool:
        """Soft-delete quick link."""
        model = self.session.get(QuickLinkModel, link_id)
        if model is None or model.is_deleted:
            return False
        model.is_deleted = 1
        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

