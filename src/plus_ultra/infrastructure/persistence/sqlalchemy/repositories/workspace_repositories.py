"""SQLAlchemy workspace tab repository implementations facade."""

from __future__ import annotations

from .code_repository import SqlAlchemyCodeRepository
from .course_repository import SqlAlchemyCourseRepository
from .idea_doubt_repository import SqlAlchemyIdeaDoubtRepository
from .opportunity_repository import SqlAlchemyOpportunityRepository
from .quick_link_repository import SqlAlchemyQuickLinkRepository

__all__ = [
    "SqlAlchemyCodeRepository",
    "SqlAlchemyCourseRepository",
    "SqlAlchemyIdeaDoubtRepository",
    "SqlAlchemyOpportunityRepository",
    "SqlAlchemyQuickLinkRepository",
]
