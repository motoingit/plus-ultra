"""SQLAlchemy repository implementation for Course entities."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from plus_ultra.domain.entities.workspace import Course
from plus_ultra.domain.repositories.workspace_repositories import (
    CourseRepositoryContract,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.mappers import (
    course_to_domain,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    CourseModel,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories.base import (
    SqlAlchemyRepositoryBase,
    _now_utc,
)


class SqlAlchemyCourseRepository(
    SqlAlchemyRepositoryBase, CourseRepositoryContract
):
    """SQLAlchemy repository for tracked courses."""

    def __init__(self, session: Session, autocommit: bool = True) -> None:
        super().__init__(session=session, autocommit=autocommit)

    def list_courses(
        self,
        platform: str | None = None,
        search_query: str | None = None,
    ) -> list[Course]:
        """List active courses matching optional filters."""
        stmt = select(CourseModel).where(CourseModel.is_deleted == 0)

        if platform and platform != "All":
            stmt = stmt.where(CourseModel.platform == platform)

        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            stmt = stmt.where(
                or_(
                    CourseModel.title.ilike(term),
                    CourseModel.instructor.ilike(term),
                    CourseModel.notes.ilike(term),
                )
            )

        stmt = stmt.order_by(CourseModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [course_to_domain(m) for m in models]

    def get(self, course_id: str) -> Course | None:
        """Fetch course by ID."""
        model = self.session.get(CourseModel, course_id)
        return course_to_domain(model) if model else None

    def create(
        self,
        title: str,
        platform: str = "Coursera",
        instructor: str = "",
        total_modules: int = 10,
        completed_modules: int = 0,
        url: str = "",
        notes: str = "",
    ) -> Course:
        """Create new course."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Title cannot be empty.")

        course_id = str(uuid.uuid4())
        now = _now_utc()
        model = CourseModel(
            id=course_id,
            title=clean_title,
            platform=platform,
            instructor=instructor,
            total_modules=total_modules,
            completed_modules=completed_modules,
            url=url,
            notes=notes,
            created_at=now,
            updated_at=now,
            is_deleted=0,
        )
        self.session.add(model)
        self._commit_or_flush()
        return course_to_domain(model)

    def increment_module(self, course_id: str) -> bool:
        """Increment completed modules count up to total_modules."""
        model = self.session.get(CourseModel, course_id)
        if model is None or model.is_deleted:
            return False
        if model.completed_modules < model.total_modules:
            model.completed_modules += 1
            model.updated_at = _now_utc()
            self._commit_or_flush()
        return True

    def update(
        self,
        course_id: str,
        title: str | None = None,
        platform: str | None = None,
        instructor: str | None = None,
        total_modules: int | None = None,
        completed_modules: int | None = None,
        url: str | None = None,
        notes: str | None = None,
    ) -> bool:
        """Update course details."""
        model = self.session.get(CourseModel, course_id)
        if model is None or model.is_deleted:
            return False

        has_change = False
        if title is not None:
            clean = title.strip()
            if not clean:
                raise ValueError("Title cannot be empty.")
            model.title = clean
            has_change = True
        if platform is not None:
            model.platform = platform
            has_change = True
        if instructor is not None:
            model.instructor = instructor
            has_change = True
        if total_modules is not None:
            model.total_modules = total_modules
            has_change = True
        if completed_modules is not None:
            model.completed_modules = completed_modules
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

    def soft_delete(self, course_id: str) -> bool:
        """Soft-delete course."""
        model = self.session.get(CourseModel, course_id)
        if model is None or model.is_deleted:
            return False
        model.is_deleted = 1
        model.updated_at = _now_utc()
        self._commit_or_flush()
        return True

