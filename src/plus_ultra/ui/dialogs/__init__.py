"""Modal dialogs for entity creation and editing in PLUS-ULTRA."""

from __future__ import annotations

from plus_ultra.ui.dialogs.base import center_modal
from plus_ultra.ui.dialogs.category_dialog import CategoryDialog
from plus_ultra.ui.dialogs.code_dialog import CodeDialog
from plus_ultra.ui.dialogs.course_dialog import CourseDialog
from plus_ultra.ui.dialogs.idea_dialog import IdeaDialog
from plus_ultra.ui.dialogs.opportunity_dialog import OpportunityDialog
from plus_ultra.ui.dialogs.quick_link_dialog import QuickLinkDialog
from plus_ultra.ui.dialogs.task_dialog import TaskDialog

__all__ = [
    "CategoryDialog",
    "CodeDialog",
    "CourseDialog",
    "IdeaDialog",
    "OpportunityDialog",
    "QuickLinkDialog",
    "TaskDialog",
    "center_modal",
]
