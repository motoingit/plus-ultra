"""Main desktop workspace dashboard panel for PLUS-ULTRA.

Coordinates sidebar navigation, tab views, modal dialogs, and notification
streams in a responsive, modern dark aesthetic.
"""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from plus_ultra.models import Task
from plus_ultra.notifications import CapsuleNotificationQueue
from plus_ultra.services import (
    CategoryService,
    CodeService,
    CourseService,
    IdeaDoubtService,
    OpportunityService,
    QuickLinkService,
    ReminderService,
    TaskService,
)
from plus_ultra.ui.components import (
    NotificationsPanel,
    ScrollableFrame,
    Sidebar,
)
from plus_ultra.ui.dialogs import (
    CategoryDialog,
    CodeDialog,
    CourseDialog,
    IdeaDialog,
    OpportunityDialog,
    QuickLinkDialog,
    TaskDialog,
)
from plus_ultra.ui.theme import THEME, CapsuleTheme
from plus_ultra.ui.views import (
    CodeView,
    CoursesView,
    IdeasView,
    OpportunitiesView,
    QuickLinksView,
    SettingsView,
    TasksView,
)

logger = logging.getLogger(__name__)

__all__ = [
    "CategoryDialog",
    "CodeDialog",
    "CourseDialog",
    "DashboardPanel",
    "IdeaDialog",
    "OpportunityDialog",
    "QuickLinkDialog",
    "ScrollableFrame",
    "Sidebar",
    "TaskDialog",
    "TreeCompatibilityFacade",
]


class TreeCompatibilityFacade:
    """Facade for backward compatibility with tests expecting panel.tree."""

    def __init__(self, panel: DashboardPanel) -> None:
        self.panel = panel

    def get_children(self) -> list[str]:
        """Return task IDs of currently filtered and rendered tasks."""
        return [t.id for t in self.panel._filtered_tasks]


class DashboardPanel(tk.Toplevel):
    """Main desktop workspace panel with modern card UI and full CRUD."""

    def __init__(
        self,
        parent: tk.Tk,
        task_service: TaskService,
        category_service: CategoryService,
        notification_queue: CapsuleNotificationQueue,
        reminder_service: ReminderService | None = None,
        code_service: CodeService | None = None,
        course_service: CourseService | None = None,
        idea_doubt_service: IdeaDoubtService | None = None,
        opportunity_service: OpportunityService | None = None,
        quick_link_service: QuickLinkService | None = None,
        theme: CapsuleTheme = THEME,
        on_notifications_cleared: Callable[[], None] | None = None,
        on_open: Callable[[], None] | None = None,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.task_service = task_service
        self.category_service = category_service
        self.notification_queue = notification_queue
        self.reminder_service = reminder_service
        self.code_service = code_service
        self.course_service = course_service
        self.idea_doubt_service = idea_doubt_service
        self.opportunity_service = opportunity_service
        self.quick_link_service = quick_link_service
        self.theme = theme
        self.on_notifications_cleared = on_notifications_cleared
        self.on_open = on_open
        self.on_close = on_close

        self.active_tab: str = "Tasks"
        self.tab_containers: dict[str, tk.Widget] = {}
        self.tree = TreeCompatibilityFacade(self)

        self.title("PLUS-ULTRA Workspace")
        self.geometry("1280x800")
        self.minsize(1060, 680)
        self.configure(bg="#0f1218")
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self.bind("<Escape>", lambda _e: self.hide())

        self._setup_styles()
        self._build_layout()
        self._refresh_tasks()
        self.withdraw()

    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            fieldbackground="#1c212c",
            background="#2b3448",
            foreground="#f8fafc",
            arrowcolor="#00e5ff",
            relief="flat",
            borderwidth=0,
        )

    def _build_layout(self) -> None:
        self.main_container = tk.Frame(self, bg="#0f1218")
        self.main_container.pack(fill="both", expand=True)

        # 1. Left Sidebar (250px)
        self.sidebar_col = tk.Frame(
            self.main_container, bg="#12151c", width=250
        )
        self.sidebar_col.pack(side="left", fill="y")
        self.sidebar_col.pack_propagate(False)
        self.sidebar = Sidebar(
            self.sidebar_col,
            self.theme,
            on_switch_tab=self._switch_tab,
            on_close=self.hide,
        )

        # 2. Right Notification Stream (280px)
        self.notif_col = tk.Frame(self.main_container, bg="#12151c", width=280)
        self.notif_col.pack(side="right", fill="y")
        self.notif_col.pack_propagate(False)
        self._build_notifications_panel()

        # 3. Center Workspace Area
        self.center_col = tk.Frame(self.main_container, bg="#161922")
        self.center_col.pack(side="left", fill="both", expand=True)
        self._build_all_tab_containers()

    @property
    def tab_buttons(self) -> dict[str, tk.Button]:
        return self.sidebar.tab_buttons

    @property
    def settings_btn(self) -> tk.Button:
        return self.sidebar.settings_btn

    def _build_all_tab_containers(self) -> None:
        self.placeholder_container = tk.Frame(self.center_col, bg="#161922")

        # 1. Tasks
        self.tasks_container = tk.Frame(self.center_col, bg="#161922")
        self.tasks_view = TasksView(
            self.tasks_container,
            self,
            self.task_service,
            self.category_service,
            self.reminder_service,
            self.theme,
        )
        self.tab_containers["Tasks"] = self.tasks_container

        # 2. Code
        self.code_container = tk.Frame(self.center_col, bg="#161922")
        self.code_view = CodeView(
            self.code_container, self, self.code_service, self.theme
        )
        self.tab_containers["Code"] = self.code_container

        # 3. Courses
        self.courses_container = tk.Frame(self.center_col, bg="#161922")
        self.courses_view = CoursesView(
            self.courses_container, self, self.course_service, self.theme
        )
        self.tab_containers["Courses"] = self.courses_container

        # 4. Ideas-Doubt
        self.ideas_container = tk.Frame(self.center_col, bg="#161922")
        self.ideas_view = IdeasView(
            self.ideas_container, self, self.idea_doubt_service, self.theme
        )
        self.tab_containers["Ideas-Doubt"] = self.ideas_container

        # 5. Opportunities
        self.opps_container = tk.Frame(self.center_col, bg="#161922")
        self.opps_view = OpportunitiesView(
            self.opps_container, self, self.opportunity_service, self.theme
        )
        self.tab_containers["Opportunities"] = self.opps_container

        # 6. Quick Links
        self.links_container = tk.Frame(self.center_col, bg="#161922")
        self.links_view = QuickLinksView(
            self.links_container, self, self.quick_link_service, self.theme
        )
        self.tab_containers["Quick Links"] = self.links_container

        # 7. Settings
        self.settings_container = tk.Frame(self.center_col, bg="#161922")
        self.settings_view = SettingsView(
            self.settings_container,
            self,
            self.theme,
            on_reseed=self._refresh_tasks,
        )
        self.tab_containers["Settings"] = self.settings_container

        self.tasks_container.pack(fill="both", expand=True)

    def _build_notifications_panel(self) -> None:
        self.notif_panel = NotificationsPanel(
            self.notif_col,
            self.notification_queue,
            self.theme,
            self.on_notifications_cleared,
        )

    # -------------------------------------------------------------------------
    # Delegated View Properties & Methods (backward compatibility)
    # -------------------------------------------------------------------------

    @property
    def search_entry(self) -> tk.Entry:
        return self.tasks_view.search_entry

    @property
    def _filtered_tasks(self) -> list[Task]:
        return self.tasks_view.filtered_tasks

    @_filtered_tasks.setter
    def _filtered_tasks(self, value: list[Task]) -> None:
        self.tasks_view.filtered_tasks = value

    def _set_status_filter(self, status: str) -> None:
        self.tasks_view.set_status_filter(status)

    def _refresh_tasks(self) -> None:
        self.tasks_view.refresh()

    def _toggle_selected_status(self, task_id: str) -> None:
        self.tasks_view.toggle_selected_status(task_id)

    def _delete_task(self, task_id: str) -> None:
        self.tasks_view.delete_task(task_id)

    def _open_create_task(self) -> None:
        self.tasks_view.open_create_task()

    def _open_edit_task(self, task: Task) -> None:
        self.tasks_view.open_edit_task(task)

    def _open_create_category(self) -> None:
        self.tasks_view.open_create_category()

    def _set_code_filter(self, cat: str) -> None:
        self.code_view.set_code_filter(cat)

    def _refresh_code(self) -> None:
        self.code_view.refresh()

    def _toggle_dsa_done(self, item_id: str) -> None:
        self.code_view.toggle_dsa_done(item_id)

    def _copy_to_clipboard(self, text: str, btn: tk.Button) -> None:
        self.code_view.copy_to_clipboard(text, btn)

    def _set_course_filter(self, platform: str) -> None:
        self.courses_view.set_course_filter(platform)

    def _refresh_courses(self) -> None:
        self.courses_view.refresh()

    def _inc_course(self, course_id: str) -> None:
        self.courses_view.inc_course(course_id)

    def _set_idea_filter(self, kind: str) -> None:
        self.ideas_view.set_idea_filter(kind)

    def _refresh_ideas(self) -> None:
        self.ideas_view.refresh()

    def _advance_idea(self, item_id: str) -> None:
        self.ideas_view.advance_idea(item_id)

    def _set_opp_filter(self, kind: str) -> None:
        self.opps_view.set_opp_filter(kind)

    def _refresh_opportunities(self) -> None:
        self.opps_view.refresh()

    def _advance_opp(self, opp_id: str) -> None:
        self.opps_view.advance_opp(opp_id)

    def _set_link_filter(self, category: str) -> None:
        self.links_view.set_link_filter(category)

    def _refresh_quick_links(self) -> None:
        self.links_view.refresh()

    def _launch_quick_link(self, link: Any) -> None:
        self.links_view.launch_quick_link(link)

    def _refresh_settings(self) -> None:
        self.settings_view.refresh()

    @property
    def notif_listbox(self) -> tk.Listbox:
        return self.notif_panel.notif_listbox

    def _refresh_notifications(self) -> None:
        self.notif_panel.refresh()

    def _mark_all_notifications_read(self) -> None:
        self.notif_panel.mark_all_read()

    def _clear_all_notifications(self) -> None:
        self.notif_panel.clear_all()

    # -------------------------------------------------------------------------
    # Navigation & Tab Switching
    # -------------------------------------------------------------------------

    def _switch_tab(self, tab_name: str) -> None:
        self.active_tab = tab_name
        self._highlight_active_tab()

        # Hide all containers
        self.tasks_container.pack_forget()
        self.placeholder_container.pack_forget()
        for container in self.tab_containers.values():
            container.pack_forget()

        if tab_name == "Tasks":
            self.tasks_container.pack(fill="both", expand=True)
            self._refresh_tasks()
        elif tab_name == "Code":
            if self.code_service:
                self.code_container.pack(fill="both", expand=True)
                self._refresh_code()
            else:
                self.placeholder_container.pack(fill="both", expand=True)
        elif tab_name == "Courses":
            if self.course_service:
                self.courses_container.pack(fill="both", expand=True)
                self._refresh_courses()
            else:
                self.placeholder_container.pack(fill="both", expand=True)
        elif tab_name == "Ideas-Doubt":
            if self.idea_doubt_service:
                self.ideas_container.pack(fill="both", expand=True)
                self._refresh_ideas()
            else:
                self.placeholder_container.pack(fill="both", expand=True)
        elif tab_name == "Opportunities":
            if self.opportunity_service:
                self.opps_container.pack(fill="both", expand=True)
                self._refresh_opportunities()
            else:
                self.placeholder_container.pack(fill="both", expand=True)
        elif tab_name == "Quick Links":
            if self.quick_link_service:
                self.links_container.pack(fill="both", expand=True)
                self._refresh_quick_links()
            else:
                self.placeholder_container.pack(fill="both", expand=True)
        elif tab_name == "Settings":
            self.settings_container.pack(fill="both", expand=True)
            self._refresh_settings()

    def _highlight_active_tab(self) -> None:
        self.sidebar.highlight_tab(self.active_tab)

    # -------------------------------------------------------------------------
    # Window Visibility & Management
    # -------------------------------------------------------------------------

    def show(self) -> None:
        """Show workspace dashboard and notify pill to disappear."""
        self.deiconify()
        self.lift()
        self.focus_force()
        if self.on_open:
            self.on_open()
        self._refresh_tasks()
        self._refresh_notifications()

    def hide(self) -> None:
        """Hide workspace dashboard and notify pill to reappear."""
        self.withdraw()
        if self.on_close:
            self.on_close()

    def toggle(self) -> None:
        """Toggle workspace visibility."""
        if self.state() == "normal":
            self.hide()
        else:
            self.show()

    def destroy(self) -> None:
        """Cleanly destroy window and restore pill."""
        if self.on_close:
            self.on_close()
        super().destroy()
