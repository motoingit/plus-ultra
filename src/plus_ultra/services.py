"""Business services layer for PLUS-ULTRA.

Applies architectural separation:
- Zero Tkinter code: pure Python business logic orchestrating repositories.
- Input validation, query composition, status state machine, search filtering.
- Fully decoupled for headless testing and CLI/API integration.
"""

from __future__ import annotations

import logging

from plus_ultra.models import (
    Category,
    CodeItem,
    Course,
    IdeaDoubt,
    Opportunity,
    QuickLink,
    Reminder,
    Task,
)
from plus_ultra.repository import (
    CategoryRepository,
    CodeRepository,
    CourseRepository,
    IdeaDoubtRepository,
    OpportunityRepository,
    QuickLinkRepository,
    ReminderRepository,
    TaskRepository,
)

logger = logging.getLogger(__name__)


VALID_STATUSES = ("Pending", "In Progress", "Completed", "Overdue")
VALID_CRITICAL_LEVELS = ("High", "Medium", "Low")
VALID_PACE_LEVELS = ("Long-term", "Short-term")


class TaskService:
    """Business operations for task management."""

    def __init__(
        self,
        task_repo: TaskRepository,
        category_repo: CategoryRepository,
    ) -> None:
        self.task_repo = task_repo
        self.category_repo = category_repo

    def create_task(
        self,
        title: str,
        category_id: str | None = None,
        description: str = "",
        due_date: str | None = None,
        status: str = "Pending",
        task_label: str = "College",
        critical_level: str = "Medium",
        pace_level: str = "Short-term",
        is_google_task: bool = False,
    ) -> Task:
        """Validate input and create a new active task."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Task title cannot be empty or whitespace-only.")

        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status: {status}. Expected {VALID_STATUSES}"
            )

        if critical_level not in VALID_CRITICAL_LEVELS:
            raise ValueError(
                f"Invalid critical level: {critical_level}. Expected "
                f"{VALID_CRITICAL_LEVELS}"
            )

        if pace_level not in VALID_PACE_LEVELS:
            raise ValueError(
                f"Invalid pace level: {pace_level}. Expected "
                f"{VALID_PACE_LEVELS}"
            )

        # Verify category exists if provided
        if category_id is not None:
            cat = self.category_repo.get_by_id(category_id)
            if not cat or cat.is_deleted:
                raise ValueError(f"Category '{category_id}' does not exist.")

        return self.task_repo.create(
            title=clean_title,
            category_id=category_id,
            description=description.strip(),
            due_date=due_date,
            status=status,
            task_label=task_label.strip(),
            critical_level=critical_level,
            pace_level=pace_level,
            is_google_task=is_google_task,
        )

    def get_task(self, task_id: str) -> Task | None:
        """Fetch task by ID if not deleted."""
        task = self.task_repo.get_by_id(task_id)
        return task if task and not task.is_deleted else None

    def update_task(
        self,
        task_id: str,
        title: str | None = None,
        category_id: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        status: str | None = None,
        task_label: str | None = None,
        critical_level: str | None = None,
        pace_level: str | None = None,
        is_google_task: bool | None = None,
    ) -> Task | None:
        """Validate updates and persist changes."""
        clean_title = title.strip() if title is not None else None
        if clean_title is not None and not clean_title:
            raise ValueError("Task title cannot be empty.")

        if status is not None and status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}.")

        if (
            critical_level is not None
            and critical_level not in VALID_CRITICAL_LEVELS
        ):
            raise ValueError(f"Invalid critical level: {critical_level}.")

        if pace_level is not None and pace_level not in VALID_PACE_LEVELS:
            raise ValueError(f"Invalid pace level: {pace_level}.")

        if category_id is not None:
            cat = self.category_repo.get_by_id(category_id)
            if not cat or cat.is_deleted:
                raise ValueError(f"Category '{category_id}' does not exist.")

        return self.task_repo.update(
            task_id=task_id,
            title=clean_title,
            category_id=category_id,
            description=description.strip() if description else None,
            due_date=due_date,
            status=status,
            task_label=task_label.strip() if task_label else None,
            critical_level=critical_level,
            pace_level=pace_level,
            is_google_task=is_google_task,
        )

    def toggle_status(self, task_id: str) -> Task | None:
        """Toggle task status between Pending and Completed."""
        task = self.get_task(task_id)
        if not task:
            return None

        new_status = "Pending" if task.status == "Completed" else "Completed"
        return self.update_task(task_id, status=new_status)

    def soft_delete_task(self, task_id: str) -> bool:
        """Soft delete a task and cascade to its reminders."""
        return self.task_repo.soft_delete(task_id)

    def list_tasks(
        self,
        category_id: str | None = None,
        status: str | None = None,
        critical_level: str | None = None,
        search_query: str | None = None,
    ) -> list[Task]:
        """List active tasks with filters and search query."""
        tasks = self.task_repo.list_active(
            category_id=category_id, status=status
        )

        if critical_level:
            tasks = [t for t in tasks if t.critical_level == critical_level]

        if search_query:
            query = search_query.strip().lower()
            tasks = [
                t
                for t in tasks
                if query in t.title.lower() or query in t.description.lower()
            ]

        return tasks


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


class ReminderService:
    """Business operations for reminder scheduling and due evaluation."""

    def __init__(
        self,
        reminder_repo: ReminderRepository,
        task_repo: TaskRepository,
    ) -> None:
        self.reminder_repo = reminder_repo
        self.task_repo = task_repo

    def create_reminder(self, task_id: str, remind_at: str) -> Reminder:
        """Create and schedule a reminder for an active task."""
        clean_task_id = task_id.strip()
        task = self.task_repo.get_by_id(clean_task_id)
        if not task or task.is_deleted:
            raise ValueError(f"Task '{task_id}' does not exist or is deleted.")

        clean_remind_at = remind_at.strip()
        if not clean_remind_at:
            raise ValueError("remind_at timestamp cannot be empty.")

        return self.reminder_repo.create(clean_task_id, clean_remind_at)

    def get_due_reminders(
        self, before_timestamp: str
    ) -> list[tuple[Reminder, Task]]:
        """Query active due reminders and pair with active tasks.

        Excludes reminders where the linked task is deleted or the reminder
        has already been dispatched in reminder_fires.
        """
        reminders = self.reminder_repo.list_due(before_timestamp)
        result: list[tuple[Reminder, Task]] = []
        for rem in reminders:
            task = self.task_repo.get_by_id(rem.task_id)
            if task and not task.is_deleted:
                result.append((rem, task))
        return result

    def mark_fired(self, reminder_id: str) -> None:
        """Record reminder dispatch in reminder_fires table."""
        self.reminder_repo.mark_fired(reminder_id)

    def is_fired(self, reminder_id: str) -> bool:
        """Check if reminder was already dispatched on this device."""
        return self.reminder_repo.is_fired(reminder_id)

    def soft_delete_reminder(self, reminder_id: str) -> bool:
        """Soft delete a reminder."""
        return self.reminder_repo.soft_delete(reminder_id)


class CodeService:
    """Business operations for Code snippets and DSA tracking."""

    def __init__(self, code_repo: CodeRepository) -> None:
        self.code_repo = code_repo

    def list_items(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[CodeItem]:
        """List active code items."""
        return self.code_repo.list_items(category, search_query)

    def get_item(self, item_id: str) -> CodeItem | None:
        """Get code item by ID."""
        return self.code_repo.get(item_id)

    def create_item(
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
        """Validate and create code item."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Title cannot be empty.")
        return self.code_repo.create(
            category=category,
            title=clean_title,
            content=content,
            language=language,
            difficulty=difficulty,
            is_done=is_done,
            url=url,
            notes=notes,
        )

    def toggle_done(self, item_id: str) -> bool:
        """Toggle DSA problem solved status."""
        return self.code_repo.toggle_done(item_id)

    def soft_delete_item(self, item_id: str) -> bool:
        """Soft delete code item."""
        return self.code_repo.soft_delete(item_id)


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

    def soft_delete_course(self, course_id: str) -> bool:
        """Soft delete course."""
        return self.course_repo.soft_delete(course_id)


class IdeaDoubtService:
    """Business operations for Ideas and Doubts tracking."""

    IDEA_STATUSES = ("Idea", "Planned", "In Progress", "Completed")
    DOUBT_STATUSES = ("Open", "Resolved")

    def __init__(self, idea_doubt_repo: IdeaDoubtRepository) -> None:
        self.idea_doubt_repo = idea_doubt_repo

    def list_items(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[IdeaDoubt]:
        """List active ideas and doubts."""
        return self.idea_doubt_repo.list_items(kind, status, search_query)

    def get_item(self, item_id: str) -> IdeaDoubt | None:
        """Get item by ID."""
        return self.idea_doubt_repo.get(item_id)

    def create_item(
        self,
        kind: str,
        title: str,
        description: str = "",
        tech_stack_or_ref: str = "",
        status: str = "Idea",
    ) -> IdeaDoubt:
        """Validate and create idea or doubt."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Title cannot be empty.")
        return self.idea_doubt_repo.create(
            kind=kind,
            title=clean_title,
            description=description,
            tech_stack_or_ref=tech_stack_or_ref,
            status=status,
        )

    def advance_status(self, item_id: str) -> bool:
        """Advance status to next stage or toggle open/resolved."""
        item = self.idea_doubt_repo.get(item_id)
        if not item:
            return False

        if item.kind == "Idea":
            try:
                curr_idx = self.IDEA_STATUSES.index(item.status)
                next_idx = (curr_idx + 1) % len(self.IDEA_STATUSES)
                new_status = self.IDEA_STATUSES[next_idx]
            except ValueError:
                new_status = "In Progress"
        else:
            new_status = "Resolved" if item.status == "Open" else "Open"

        return self.idea_doubt_repo.update_status(item_id, new_status)

    def soft_delete_item(self, item_id: str) -> bool:
        """Soft delete item."""
        return self.idea_doubt_repo.soft_delete(item_id)


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

    def soft_delete_opportunity(self, opp_id: str) -> bool:
        """Soft delete opportunity."""
        return self.opp_repo.soft_delete(opp_id)


class QuickLinkService:
    """Business operations for quick launch URLs and local paths."""

    def __init__(self, link_repo: QuickLinkRepository) -> None:
        self.link_repo = link_repo

    def list_links(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[QuickLink]:
        """List active quick links."""
        return self.link_repo.list_links(category, search_query)

    def get_link(self, link_id: str) -> QuickLink | None:
        """Get link by ID."""
        return self.link_repo.get(link_id)

    def create_link(
        self,
        name: str,
        target_uri: str,
        category: str = "Web",
    ) -> QuickLink:
        """Validate and create quick link."""
        clean_name = name.strip()
        clean_uri = target_uri.strip()
        if not clean_name:
            raise ValueError("Link name cannot be empty.")
        if not clean_uri:
            raise ValueError("Target URI cannot be empty.")
        return self.link_repo.create(
            name=clean_name,
            target_uri=clean_uri,
            category=category,
        )

    def record_click(self, link_id: str) -> bool:
        """Increment click count for link."""
        return self.link_repo.increment_click(link_id)

    def soft_delete_link(self, link_id: str) -> bool:
        """Soft delete link."""
        return self.link_repo.soft_delete(link_id)
