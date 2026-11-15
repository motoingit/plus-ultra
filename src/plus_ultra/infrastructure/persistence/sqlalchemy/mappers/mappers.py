"""Mappers translating between SQLAlchemy models and domain entities."""

from __future__ import annotations

from plus_ultra.domain.entities import (
    AppState,
    Category,
    CodeItem,
    Course,
    IdeaDoubt,
    Opportunity,
    QuickLink,
    Reminder,
    Task,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    AppStateModel,
    CategoryModel,
    CodeItemModel,
    CourseModel,
    IdeaDoubtModel,
    OpportunityModel,
    QuickLinkModel,
    ReminderModel,
    TaskModel,
)


def category_to_domain(m: CategoryModel) -> Category:
    """Map CategoryModel ORM record to Category domain entity."""
    return Category(
        id=m.id,
        name=m.name,
        color=m.color,
        created_at=m.created_at,
        updated_at=m.updated_at,
        synced_at=m.synced_at,
        is_deleted=m.is_deleted,
    )


def task_to_domain(m: TaskModel) -> Task:
    """Map TaskModel ORM record to Task domain entity."""
    return Task(
        id=m.id,
        category_id=m.category_id,
        title=m.title,
        description=m.description,
        due_date=m.due_date,
        status=m.status,
        task_label=m.task_label,
        critical_level=m.critical_level,
        pace_level=m.pace_level,
        is_google_task=bool(m.is_google_task),
        created_at=m.created_at,
        updated_at=m.updated_at,
        synced_at=m.synced_at,
        is_deleted=m.is_deleted,
    )


def reminder_to_domain(m: ReminderModel) -> Reminder:
    """Map ReminderModel ORM record to Reminder domain entity."""
    return Reminder(
        id=m.id,
        task_id=m.task_id,
        remind_at=m.remind_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
        synced_at=m.synced_at,
        is_deleted=m.is_deleted,
    )


def app_state_to_domain(m: AppStateModel) -> AppState:
    """Map AppStateModel ORM record to AppState domain entity."""
    return AppState(key=m.key, value=m.value)


def code_item_to_domain(m: CodeItemModel) -> CodeItem:
    """Map CodeItemModel ORM record to CodeItem domain entity."""
    return CodeItem(
        id=m.id,
        category=m.category,
        title=m.title,
        content=m.content,
        language=m.language,
        difficulty=m.difficulty,
        is_done=m.is_done,
        url=m.url,
        notes=m.notes,
        created_at=m.created_at,
        updated_at=m.updated_at,
        synced_at=m.synced_at,
        is_deleted=m.is_deleted,
    )


def course_to_domain(m: CourseModel) -> Course:
    """Map CourseModel ORM record to Course domain entity."""
    return Course(
        id=m.id,
        title=m.title,
        platform=m.platform,
        instructor=m.instructor,
        total_modules=m.total_modules,
        completed_modules=m.completed_modules,
        url=m.url,
        notes=m.notes,
        created_at=m.created_at,
        updated_at=m.updated_at,
        synced_at=m.synced_at,
        is_deleted=m.is_deleted,
    )


def idea_doubt_to_domain(m: IdeaDoubtModel) -> IdeaDoubt:
    """Map IdeaDoubtModel ORM record to IdeaDoubt domain entity."""
    return IdeaDoubt(
        id=m.id,
        kind=m.kind,
        title=m.title,
        description=m.description,
        tech_stack_or_ref=m.tech_stack_or_ref,
        status=m.status,
        created_at=m.created_at,
        updated_at=m.updated_at,
        synced_at=m.synced_at,
        is_deleted=m.is_deleted,
    )


def opportunity_to_domain(m: OpportunityModel) -> Opportunity:
    """Map OpportunityModel ORM record to Opportunity domain entity."""
    return Opportunity(
        id=m.id,
        title=m.title,
        organization=m.organization,
        kind=m.kind,
        url=m.url,
        deadline=m.deadline,
        status=m.status,
        notes=m.notes,
        created_at=m.created_at,
        updated_at=m.updated_at,
        synced_at=m.synced_at,
        is_deleted=m.is_deleted,
    )


def quick_link_to_domain(m: QuickLinkModel) -> QuickLink:
    """Map QuickLinkModel ORM record to QuickLink domain entity."""
    return QuickLink(
        id=m.id,
        name=m.name,
        target_uri=m.target_uri,
        category=m.category,
        click_count=m.click_count,
        created_at=m.created_at,
        updated_at=m.updated_at,
        synced_at=m.synced_at,
        is_deleted=m.is_deleted,
    )
