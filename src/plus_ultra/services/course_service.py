"""Business operations for Course and certification tracking."""

from __future__ import annotations

from plus_ultra.models import Course
from plus_ultra.repositories import CourseRepository


class CourseService:
    """Business operations for Course and certification tracking."""

    def __init__(self, course_repo: CourseRepository) -> None:
        self.course_repo = course_repo

    def list_courses(
        self,
        platform: str | None = None,
        search_query: str | None = None,
    ) -> list[Course]:
        """List active courses."""
        return self.course_repo.list_courses(platform, search_query)

    def get_course(self, course_id: str) -> Course | None:
        """Get course by ID."""
        return self.course_repo.get(course_id)

    def create_course(
        self,
        title: str,
        platform: str = "Coursera",
        instructor: str = "",
        total_modules: int = 10,
        completed_modules: int = 0,
        url: str = "",
        notes: str = "",
    ) -> Course:
        """Validate and create course."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Course title cannot be empty.")
        if total_modules < 1:
            raise ValueError("Total modules must be at least 1.")
        return self.course_repo.create(
            title=clean_title,
            platform=platform,
            instructor=instructor,
            total_modules=total_modules,
            completed_modules=max(0, min(completed_modules, total_modules)),
            url=url,
            notes=notes,
        )

    def increment_module(self, course_id: str) -> bool:
        """Increment completed module count."""
        return self.course_repo.increment_module(course_id)

    def update_course(
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
        """Update course attributes."""
        clean_title = title.strip() if title is not None else None
        if clean_title is not None and not clean_title:
            raise ValueError("Course title cannot be empty.")
        if total_modules is not None and total_modules < 1:
            raise ValueError("Total modules must be at least 1.")
        return self.course_repo.update(
            course_id=course_id,
            title=clean_title,
            platform=platform,
            instructor=instructor,
            total_modules=total_modules,
            completed_modules=completed_modules,
            url=url,
            notes=notes,
        )

    def soft_delete_course(self, course_id: str) -> bool:
        """Soft delete course."""
        return self.course_repo.soft_delete(course_id)
