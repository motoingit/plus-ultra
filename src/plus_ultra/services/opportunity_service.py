"""Business operations for career and academic opportunities."""

from __future__ import annotations

from plus_ultra.models import Opportunity
from plus_ultra.repositories import OpportunityRepository


class OpportunityService:
    """Business operations for career and academic opportunities."""

    STATUSES = ("Saved", "Applied", "In Progress", "Accepted", "Rejected")

    def __init__(self, opp_repo: OpportunityRepository) -> None:
        self.opp_repo = opp_repo

    def list_opportunities(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[Opportunity]:
        """List active opportunities."""
        return self.opp_repo.list_opportunities(kind, status, search_query)

    def get_opportunity(self, opp_id: str) -> Opportunity | None:
        """Get opportunity by ID."""
        return self.opp_repo.get(opp_id)

    def create_opportunity(
        self,
        title: str,
        organization: str,
        kind: str = "Internship",
        url: str = "",
        deadline: str = "",
        status: str = "Saved",
        notes: str = "",
    ) -> Opportunity:
        """Validate and create opportunity."""
        clean_title = title.strip()
        clean_org = organization.strip()
        if not clean_title:
            raise ValueError("Title cannot be empty.")
        if not clean_org:
            raise ValueError("Organization cannot be empty.")
        return self.opp_repo.create(
            title=clean_title,
            organization=clean_org,
            kind=kind,
            url=url,
            deadline=deadline,
            status=status,
            notes=notes,
        )

    def advance_status(self, opp_id: str) -> bool:
        """Advance opportunity status through standard lifecycle."""
        item = self.opp_repo.get(opp_id)
        if not item:
            return False

        try:
            curr_idx = self.STATUSES.index(item.status)
            next_idx = (curr_idx + 1) % len(self.STATUSES)
            new_status = self.STATUSES[next_idx]
        except ValueError:
            new_status = "Applied"

        return self.opp_repo.update_status(opp_id, new_status)

    def update_opportunity(
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
        clean_title = title.strip() if title is not None else None
        clean_org = organization.strip() if organization is not None else None
        if clean_title is not None and not clean_title:
            raise ValueError("Title cannot be empty.")
        if clean_org is not None and not clean_org:
            raise ValueError("Organization cannot be empty.")
        return self.opp_repo.update(
            opp_id=opp_id,
            title=clean_title,
            organization=clean_org,
            kind=kind,
            url=url,
            deadline=deadline,
            status=status,
            notes=notes,
        )

    def soft_delete_opportunity(self, opp_id: str) -> bool:
        """Soft delete opportunity."""
        return self.opp_repo.soft_delete(opp_id)
