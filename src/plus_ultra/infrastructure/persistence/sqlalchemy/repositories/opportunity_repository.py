"""SQLAlchemy repository implementation for Opportunity entities."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from plus_ultra.domain.entities.workspace import Opportunity
from plus_ultra.domain.repositories.workspace_repositories import (
    OpportunityRepositoryContract,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.mappers import (
    opportunity_to_domain,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    OpportunityModel,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories.base import (
    SqlAlchemyRepositoryBase,
    _now_utc,
)


class SqlAlchemyOpportunityRepository(
    SqlAlchemyRepositoryBase, OpportunityRepositoryContract
):
    """SQLAlchemy repository for career opportunities tracker."""

    def __init__(self, session: Session, autocommit: bool = True) -> None:
        super().__init__(session=session, autocommit=autocommit)

    def list_opportunities(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[Opportunity]:
        """List active opportunities matching optional filters."""
        stmt = select(OpportunityModel).where(OpportunityModel.is_deleted == 0)

        if kind and kind != "All":
            stmt = stmt.where(OpportunityModel.kind == kind)

        if status and status != "All":
            stmt = stmt.where(OpportunityModel.status == status)

        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            stmt = stmt.where(
                or_(
                    OpportunityModel.title.ilike(term),
                    OpportunityModel.organization.ilike(term),
                    OpportunityModel.notes.ilike(term),
                )
            )

        stmt = stmt.order_by(OpportunityModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [opportunity_to_domain(m) for m in models]

    def get(self, opp_id: str) -> Opportunity | None:
        """Fetch opportunity by ID."""
        model = self.session.get(OpportunityModel, opp_id)
        return opportunity_to_domain(model) if model else None

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
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Title cannot be empty.")

        opp_id = str(uuid.uuid4())
        now = _now_utc()
        model = OpportunityModel(
            id=opp_id,
            title=clean_title,
            organization=organization,
            kind=kind,
            url=url,
            deadline=deadline,
            status=status,
            notes=notes,
            created_at=now,
            updated_at=now,
            is_deleted=0,
        )
        self.session.add(model)
        self._commit_or_flush()
        return opportunity_to_domain(model)

    def update_status(self, opp_id: str, new_status: str) -> bool:
        """Update opportunity status."""
        model = self.session.get(OpportunityModel, opp_id)
        if model is None or model.is_deleted:
            return False
        model.status = new_status
        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

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
        model = self.session.get(OpportunityModel, opp_id)
        if model is None or model.is_deleted:
            return False

        has_change = False
        if title is not None:
            clean = title.strip()
            if not clean:
                raise ValueError("Title cannot be empty.")
            model.title = clean
            has_change = True
        if organization is not None:
            model.organization = organization
            has_change = True
        if kind is not None:
            model.kind = kind
            has_change = True
        if url is not None:
            model.url = url
            has_change = True
        if deadline is not None:
            model.deadline = deadline
            has_change = True
        if status is not None:
            model.status = status
            has_change = True
        if notes is not None:
            model.notes = notes
            has_change = True

        if not has_change:
            return False

        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

    def soft_delete(self, opp_id: str) -> bool:
        """Soft-delete opportunity."""
        model = self.session.get(OpportunityModel, opp_id)
        if model is None or model.is_deleted:
            return False
        model.is_deleted = 1
        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True
