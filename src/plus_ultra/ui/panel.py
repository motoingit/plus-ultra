"""Main dashboard workspace window for PLUS-ULTRA.

Applies architectural separation:
- MVC Architecture: UI layer interacts exclusively with services and models.
- Zero SQL/SQLite imports: all data operations go through dedicated services.
- 3-Column Layout: Left Navigation Sidebar, Main Workspace Panel with
  Option A styled Treeview and interactive feature cards, and Right
  Notification Panel.
- Live two-way synchronization with floating capsule unread bell indicator.
- 100% interactive tabs for Code, Courses, Ideas-Doubt, Opportunities,
  Quick Links, Tasks, and Settings.
"""

from __future__ import annotations

import logging
import os
import subprocess
import tkinter as tk
import webbrowser
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra import config
from plus_ultra.desktop import send_desktop_notification
from plus_ultra.models import (
    Category,
    QuickLink,
    Task,
)
from plus_ultra.notifications import CapsuleNotificationQueue
from plus_ultra.services import (
    CategoryService,
    CodeService,
    CourseService,
    IdeaDoubtService,
    OpportunityService,
    QuickLinkService,
    TaskService,
)
from plus_ultra.ui.theme import THEME, CapsuleTheme

logger = logging.getLogger(__name__)

WORKSPACE_TABS = [
    ("Tasks", "📌"),
    ("Code", "💻"),
    ("Courses", "🎓"),
    ("Ideas-Doubt", "💡"),
    ("Opportunities", "🚀"),
    ("Quick Links", "⚡"),
]


class ScrollableFrame(tk.Frame):
    """Reusable scrollable dark frame for card-based sub-views."""

    def __init__(self, parent: tk.Widget, bg: str = "#161922") -> None:
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.interior = tk.Frame(self.canvas, bg=bg)

        self.canvas_win = self.canvas.create_window(
            (0, 0), window=self.interior, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.interior.bind("<Configure>", self._on_interior_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.bind_all("<Button-4>", self._on_mousewheel_up, add="+")
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_down, add="+")

    def _on_interior_configure(self, _event: tk.Event[Any]) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event[Any]) -> None:
        self.canvas.itemconfig(self.canvas_win, width=event.width)

    def _on_mousewheel_up(self, _event: tk.Event[Any]) -> None:
        if self.winfo_ismapped():
            self.canvas.yview_scroll(-1, "units")

    def _on_mousewheel_down(self, _event: tk.Event[Any]) -> None:
        if self.winfo_ismapped():
            self.canvas.yview_scroll(1, "units")


class TaskDialog(tk.Toplevel):
    """Modal dialog for creating or editing tasks."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        categories: list[Category],
        task: Task | None = None,
        on_save: Callable[[dict[str, Any]], None] | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        super().__init__(parent)
        self.task = task
        self.categories = categories
        self.on_save = on_save
        self.theme = theme

        self.title("Edit Task" if task else "Create New Task")
        self.geometry("460x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_form()
        self._center_window(parent)

    def _center_window(self, parent: tk.Tk | tk.Toplevel) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        w = self.winfo_width()
        h = self.winfo_height()
        x = max(10, px + (pw - w) // 2)
        y = max(10, py + (ph - h) // 2)
        self.geometry(f"+{x}+{y}")

    def _build_form(self) -> None:
        self.configure(bg="#151922")
        frame = tk.Frame(self, bg="#151922", padx=20, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="Task Title *",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9, "bold"),
        ).pack(anchor="w")
        self.title_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            insertbackground="#00e5ff",
            relief="flat",
            font=(self.theme.font_family, 10),
        )
        self.title_entry.pack(fill="x", pady=(4, 10), ipady=3)
        if self.task:
            self.title_entry.insert(0, self.task.title)

        row1 = tk.Frame(frame, bg="#151922")
        row1.pack(fill="x", pady=(0, 10))

        cat_box = tk.Frame(row1, bg="#151922")
        cat_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            cat_box,
            text="Category",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        cat_names = [c.name for c in self.categories] or ["General"]
        self.cat_combo = ttk.Combobox(
            cat_box, values=cat_names, state="readonly"
        )
        current_cat_name = "General"
        if self.task and self.task.category_id:
            for c in self.categories:
                if c.id == self.task.category_id:
                    current_cat_name = c.name
                    break
        self.cat_combo.set(current_cat_name)
        self.cat_combo.pack(fill="x", pady=(4, 0))

        prio_box = tk.Frame(row1, bg="#151922")
        prio_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            prio_box,
            text="Priority",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        self.prio_combo = ttk.Combobox(
            prio_box, values=["High", "Medium", "Low"], state="readonly"
        )
        self.prio_combo.set(self.task.critical_level if self.task else "Medium")
        self.prio_combo.pack(fill="x", pady=(4, 0))

        row2 = tk.Frame(frame, bg="#151922")
        row2.pack(fill="x", pady=(0, 10))

        pace_box = tk.Frame(row2, bg="#151922")
        pace_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            pace_box,
            text="Pace",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        self.pace_combo = ttk.Combobox(
            pace_box, values=["Short-term", "Long-term"], state="readonly"
        )
        self.pace_combo.set(self.task.pace_level if self.task else "Short-term")
        self.pace_combo.pack(fill="x", pady=(4, 0))

        due_box = tk.Frame(row2, bg="#151922")
        due_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            due_box,
            text="Due Date (optional)",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        self.due_entry = tk.Entry(
            due_box,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 10),
        )
        self.due_entry.pack(fill="x", pady=(4, 0), ipady=2)
        if self.task and self.task.due_date:
            self.due_entry.insert(0, self.task.due_date)

        tk.Label(
            frame,
            text="Description / Notes",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        self.desc_text = tk.Text(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            height=4,
            font=(self.theme.font_family, 9),
        )
        self.desc_text.pack(fill="both", expand=True, pady=(4, 14))
        if self.task and self.task.description:
            self.desc_text.insert("1.0", self.task.description)

        btn_frame = tk.Frame(frame, bg="#151922")
        btn_frame.pack(fill="x")

        save_btn = tk.Button(
            btn_frame,
            text="Save Task",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9, "bold"),
            command=self._handle_save,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        save_btn.pack(side="right", padx=(8, 0))

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            bg="#2b3448",
            fg="#e2e8f0",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9),
            command=self.destroy,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        cancel_btn.pack(side="right")

    def _handle_save(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror(
                "Validation Error", "Task title cannot be empty.", parent=self
            )
            return

        cat_name = self.cat_combo.get()
        cat_id = None
        for c in self.categories:
            if c.name == cat_name:
                cat_id = c.id
                break

        critical = self.prio_combo.get()
        pace = self.pace_combo.get()
        due = self.due_entry.get().strip() or None
        desc = self.desc_text.get("1.0", tk.END).strip()

        data = {
            "title": title,
            "category_id": cat_id,
            "critical_level": critical,
            "pace_level": pace,
            "due_date": due,
            "description": desc,
        }
        if self.on_save:
            self.on_save(data)
        self.destroy()


class DashboardPanel(tk.Toplevel):
    """3-Column desktop workspace window for PLUS-ULTRA."""

    def __init__(
        self,
        parent: tk.Tk,
        task_service: TaskService,
        category_service: CategoryService,
        notification_queue: CapsuleNotificationQueue,
        code_service: CodeService | None = None,
        course_service: CourseService | None = None,
        idea_doubt_service: IdeaDoubtService | None = None,
        opportunity_service: OpportunityService | None = None,
        quick_link_service: QuickLinkService | None = None,
        on_notifications_cleared: Callable[[], None] | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        super().__init__(parent)
        self.task_service = task_service
        self.category_service = category_service
        self.notification_queue = notification_queue
        self.code_service = code_service
        self.course_service = course_service
        self.idea_doubt_service = idea_doubt_service
        self.opportunity_service = opportunity_service
        self.quick_link_service = quick_link_service
        self.on_notifications_cleared = on_notifications_cleared
        self.theme = theme

        self.title("PLUS-ULTRA Workspace")
        self.geometry("1180x700")
        self.minsize(1020, 600)
        self.configure(bg="#11141c")

        self.active_tab: str = "Tasks"
        self.status_filter: str = "All"
        self.prio_filter: str = "All"
        self.category_filter_id: str | None = None

        self.code_filter: str = "All"
        self.course_filter: str = "All"
        self.idea_filter: str = "All"
        self.opp_filter: str = "All"
        self.link_filter: str = "All"

        self._setup_styles()
        self._build_layout()
        self._refresh_categories()
        self._refresh_tasks()
        self._refresh_notifications()

        # Intercept window manager close to hide rather than destroy
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self.withdraw()

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Custom.Treeview",
            background="#1e2433",
            foreground="#f8fafc",
            fieldbackground="#1e2433",
            rowheight=32,
            borderwidth=0,
            font=(self.theme.font_family, 9),
        )
        style.configure(
            "Custom.Treeview.Heading",
            background="#151922",
            foreground="#00e5ff",
            font=(self.theme.font_family, 9, "bold"),
            borderwidth=0,
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", "#0284c7")],
            foreground=[("selected", "#ffffff")],
        )

    def _build_layout(self) -> None:
        # 1. Left Navigation Sidebar
        self.sidebar_col = tk.Frame(self, bg="#12151c", width=230)
        self.sidebar_col.pack(side="left", fill="y")
        self.sidebar_col.pack_propagate(False)
        self._build_sidebar()

        # 2. Right Notification Sidebar
        self.notif_col = tk.Frame(self, bg="#12151c", width=240)
        self.notif_col.pack(side="right", fill="y")
        self.notif_col.pack_propagate(False)
        self._build_notification_panel()

        # 3. Main Center Workspace Panel
        self.center_col = tk.Frame(self, bg="#161922")
        self.center_col.pack(side="left", fill="both", expand=True)

        # Tab containers
        self.tab_containers: dict[str, tk.Frame] = {}
        self._build_all_tab_containers()

        # Backwards-compat alias for testing
        self.placeholder_container = self.tab_containers["Code"]

    def _build_sidebar(self) -> None:
        header = tk.Label(
            self.sidebar_col,
            text="⚡ PLUS-ULTRA",
            bg="#12151c",
            fg="#00e5ff",
            font=(self.theme.font_family, 12, "bold"),
            pady=18,
            anchor="w",
            padx=16,
        )
        header.pack(fill="x")

        self.tab_buttons: dict[str, tk.Button] = {}
        for tab_name, icon in WORKSPACE_TABS:
            btn = tk.Button(
                self.sidebar_col,
                text=f"  {icon}  {tab_name}",
                anchor="w",
                bg="#12151c",
                fg="#94a3b8",
                activebackground="#1e2433",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                highlightthickness=0,
                padx=16,
                pady=10,
                font=(self.theme.font_family, 10),
                cursor="hand2",
                command=lambda name=tab_name: self._switch_tab(name),
            )
            btn.pack(fill="x", padx=6, pady=2)
            self.tab_buttons[tab_name] = btn

        self._highlight_active_tab()

        settings_frame = tk.Frame(self.sidebar_col, bg="#12151c")
        settings_frame.pack(side="bottom", fill="x", pady=12, padx=6)
        settings_btn = tk.Button(
            settings_frame,
            text="  ⚙️  Settings & Info",
            anchor="w",
            bg="#12151c",
            fg="#64748b",
            activebackground="#1e2433",
            activeforeground="#f8fafc",
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=16,
            pady=8,
            font=(self.theme.font_family, 9),
            cursor="hand2",
            command=lambda: self._switch_tab("Settings"),
        )
        settings_btn.pack(fill="x")
        self.settings_btn = settings_btn

    def _switch_tab(self, tab_name: str) -> None:
        self.active_tab = tab_name
        self._highlight_active_tab()

        for name, container in self.tab_containers.items():
            if name == tab_name:
                container.pack(fill="both", expand=True)
            else:
                container.pack_forget()

        if tab_name == "Tasks":
            self._refresh_tasks()
        elif tab_name == "Code":
            self._refresh_code()
        elif tab_name == "Courses":
            self._refresh_courses()
        elif tab_name == "Ideas-Doubt":
            self._refresh_ideas()
        elif tab_name == "Opportunities":
            self._refresh_opportunities()
        elif tab_name == "Quick Links":
            self._refresh_quick_links()
        elif tab_name == "Settings":
            self._refresh_settings()

    def _highlight_active_tab(self) -> None:
        for name, btn in self.tab_buttons.items():
            if name == self.active_tab:
                btn.configure(
                    bg="#1e2433",
                    fg="#00e5ff",
                    font=(self.theme.font_family, 10, "bold"),
                )
            else:
                btn.configure(
                    bg="#12151c",
                    fg="#94a3b8",
                    font=(self.theme.font_family, 10),
                )
        if hasattr(self, "settings_btn"):
            if self.active_tab == "Settings":
                self.settings_btn.configure(
                    bg="#1e2433",
                    fg="#00e5ff",
                    font=(self.theme.font_family, 9, "bold"),
                )
            else:
                self.settings_btn.configure(
                    bg="#12151c",
                    fg="#64748b",
                    font=(self.theme.font_family, 9),
                )

    def _build_all_tab_containers(self) -> None:
        # 1. Tasks
        self.tasks_container = tk.Frame(self.center_col, bg="#161922")
        self._build_tasks_view()
        self.tab_containers["Tasks"] = self.tasks_container

        # 2. Code
        self.code_container = tk.Frame(self.center_col, bg="#161922")
        self._build_code_view()
        self.tab_containers["Code"] = self.code_container

        # 3. Courses
        self.courses_container = tk.Frame(self.center_col, bg="#161922")
        self._build_courses_view()
        self.tab_containers["Courses"] = self.courses_container

        # 4. Ideas-Doubt
        self.ideas_container = tk.Frame(self.center_col, bg="#161922")
        self._build_ideas_view()
        self.tab_containers["Ideas-Doubt"] = self.ideas_container

        # 5. Opportunities
        self.opps_container = tk.Frame(self.center_col, bg="#161922")
        self._build_opportunities_view()
        self.tab_containers["Opportunities"] = self.opps_container

        # 6. Quick Links
        self.links_container = tk.Frame(self.center_col, bg="#161922")
        self._build_quick_links_view()
        self.tab_containers["Quick Links"] = self.links_container

        # 7. Settings
        self.settings_container = tk.Frame(self.center_col, bg="#161922")
        self._build_settings_view()
        self.tab_containers["Settings"] = self.settings_container

        # Initial view
        self.tasks_container.pack(fill="both", expand=True)

    # ==========================================
    # 1. TASKS TAB VIEW
    # ==========================================

    def _build_tasks_view(self) -> None:
        head_bar = tk.Frame(
            self.tasks_container, bg="#161922", padx=20, pady=16
        )
        head_bar.pack(fill="x")

        self.tasks_title_label = tk.Label(
            head_bar,
            text="Tasks & Deadlines",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 13, "bold"),
        )
        self.tasks_title_label.pack(side="left")

        new_task_btn = tk.Button(
            head_bar,
            text="+ New Task",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9, "bold"),
            command=self._open_create_task,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        new_task_btn.pack(side="right", padx=(8, 0))

        new_cat_btn = tk.Button(
            head_bar,
            text="+ Category",
            bg="#2b3448",
            fg="#f8fafc",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9),
            command=self._open_create_category,
            cursor="hand2",
            padx=10,
            pady=4,
        )
        new_cat_btn.pack(side="right")

        filter_bar = tk.Frame(self.tasks_container, bg="#161922", padx=20)
        filter_bar.pack(fill="x", pady=(0, 10))

        search_box = tk.Frame(filter_bar, bg="#161922")
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(search_box, text="🔍", bg="#161922", fg="#64748b").pack(
            side="left", padx=(0, 4)
        )
        self.search_entry = tk.Entry(
            search_box,
            bg="#12151c",
            fg="#f8fafc",
            relief="flat",
            insertbackground="#00e5ff",
            font=(self.theme.font_family, 9),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.search_entry.bind("<KeyRelease>", lambda _e: self._refresh_tasks())

        status_box = tk.Frame(filter_bar, bg="#161922")
        status_box.pack(side="right")
        for st in ["All", "Pending", "Completed"]:
            btn = tk.Button(
                status_box,
                text=st,
                bg="#1e2433",
                fg="#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda s=st: self._set_status_filter(s),
            )
            btn.pack(side="left", padx=2)

        self.prio_filter_combo = ttk.Combobox(
            status_box,
            values=["All Priority", "High", "Medium", "Low"],
            width=12,
            state="readonly",
        )
        self.prio_filter_combo.set("All Priority")
        self.prio_filter_combo.pack(side="left", padx=(6, 0))
        self.prio_filter_combo.bind(
            "<<ComboboxSelected>>", lambda _e: self._on_prio_filter_change()
        )

        table_frame = tk.Frame(self.tasks_container, bg="#161922", padx=20)
        table_frame.pack(fill="both", expand=True, pady=(0, 16))

        cols = ("status", "title", "category", "priority", "pace", "due_date")
        self.tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            selectmode="browse",
            style="Custom.Treeview",
        )
        self.tree.heading("status", text="Status")
        self.tree.heading("title", text="Title")
        self.tree.heading("category", text="Category")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("pace", text="Pace")
        self.tree.heading("due_date", text="Due Date")

        self.tree.column("status", width=90, anchor="center")
        self.tree.column("title", width=260, anchor="w")
        self.tree.column("category", width=120, anchor="w")
        self.tree.column("priority", width=90, anchor="center")
        self.tree.column("pace", width=90, anchor="center")
        self.tree.column("due_date", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Button-3>", self._on_tree_right_click)

    # ==========================================
    # 2. CODE TAB VIEW
    # ==========================================

    def _build_code_view(self) -> None:
        head_bar = tk.Frame(self.code_container, bg="#161922", padx=20, pady=16)
        head_bar.pack(fill="x")

        self.code_title_label = tk.Label(
            head_bar,
            text="💻 Code Snippets & DSA Tracker",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 13, "bold"),
        )
        self.code_title_label.pack(side="left")

        new_code_btn = tk.Button(
            head_bar,
            text="+ Add Code Item",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9, "bold"),
            command=self._open_create_code,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        new_code_btn.pack(side="right")

        filter_bar = tk.Frame(self.code_container, bg="#161922", padx=20)
        filter_bar.pack(fill="x", pady=(0, 10))

        search_box = tk.Frame(filter_bar, bg="#161922")
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(search_box, text="🔍", bg="#161922", fg="#64748b").pack(
            side="left", padx=(0, 4)
        )
        self.code_search_entry = tk.Entry(
            search_box,
            bg="#12151c",
            fg="#f8fafc",
            relief="flat",
            insertbackground="#00e5ff",
            font=(self.theme.font_family, 9),
        )
        self.code_search_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.code_search_entry.bind(
            "<KeyRelease>", lambda _e: self._refresh_code()
        )

        pills_box = tk.Frame(filter_bar, bg="#161922")
        pills_box.pack(side="right")
        cats = [
            "All",
            "Snippets",
            "CLI Commands",
            "Syntax Reference",
            "DSA Problem Tracker",
        ]
        self.code_filter_btns: dict[str, tk.Button] = {}
        for c in cats:
            btn = tk.Button(
                pills_box,
                text=c,
                bg="#1e2433",
                fg="#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda cat=c: self._set_code_filter(cat),
            )
            btn.pack(side="left", padx=2)
            self.code_filter_btns[c] = btn

        self.code_scroll = ScrollableFrame(self.code_container, bg="#161922")
        self.code_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _set_code_filter(self, cat: str) -> None:
        self.code_filter = cat
        for c, btn in self.code_filter_btns.items():
            if c == cat:
                btn.configure(bg="#0284c7", fg="#ffffff")
            else:
                btn.configure(bg="#1e2433", fg="#94a3b8")
        self._refresh_code()

    def _refresh_code(self) -> None:
        if not self.code_service:
            return

        for child in self.code_scroll.interior.winfo_children():
            child.destroy()

        query = self.code_search_entry.get().strip() or None
        items = self.code_service.list_items(
            category=None if self.code_filter == "All" else self.code_filter,
            search_query=query,
        )
        self.code_title_label.config(
            text=f"💻 Code Snippets & DSA Tracker ({len(items)})"
        )

        if not items:
            tk.Label(
                self.code_scroll.interior,
                text="No code items found matching current filters.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 10),
                pady=30,
            ).pack()
            return

        for item in items:
            card = tk.Frame(
                self.code_scroll.interior, bg="#1c212c", padx=14, pady=12
            )
            card.pack(fill="x", pady=6)

            # Header row
            top_row = tk.Frame(card, bg="#1c212c")
            top_row.pack(fill="x", pady=(0, 6))

            tk.Label(
                top_row,
                text=item.title,
                bg="#1c212c",
                fg="#f8fafc",
                font=(self.theme.font_family, 10, "bold"),
            ).pack(side="left")

            cat_pill = tk.Label(
                top_row,
                text=f" {item.category} ",
                bg="#2b3448",
                fg="#00e5ff",
                font=(self.theme.font_family, 8),
            )
            cat_pill.pack(side="left", padx=8)

            if item.category == "DSA Problem Tracker":
                diff_colors = {
                    "Easy": "#10b981",
                    "Medium": "#f59e0b",
                    "Hard": "#ef4444",
                }
                color = diff_colors.get(item.difficulty, "#94a3b8")
                tk.Label(
                    top_row,
                    text=f" {item.difficulty} ",
                    bg="#242b3b",
                    fg=color,
                    font=(self.theme.font_family, 8, "bold"),
                ).pack(side="left")

            # Actions row (Copy or DSA status)
            actions = tk.Frame(top_row, bg="#1c212c")
            actions.pack(side="right")

            if item.category == "DSA Problem Tracker":
                status_text = "✓ Solved" if item.is_done else "○ Todo"
                status_color = "#10b981" if item.is_done else "#94a3b8"
                toggle_btn = tk.Button(
                    actions,
                    text=status_text,
                    bg="#242b3b",
                    fg=status_color,
                    relief="flat",
                    bd=0,
                    highlightthickness=0,
                    font=(self.theme.font_family, 8, "bold"),
                    cursor="hand2",
                    padx=8,
                    pady=2,
                    command=lambda i=item.id: self._toggle_dsa_done(i),
                )
                toggle_btn.pack(side="left", padx=4)

                if item.url:
                    open_btn = tk.Button(
                        actions,
                        text="🔗 Open Problem",
                        bg="#0284c7",
                        fg="#ffffff",
                        relief="flat",
                        bd=0,
                        highlightthickness=0,
                        font=(self.theme.font_family, 8),
                        cursor="hand2",
                        padx=8,
                        pady=2,
                        command=lambda u=item.url: webbrowser.open(u),
                    )
                    open_btn.pack(side="left", padx=4)
            else:
                copy_btn = tk.Button(
                    actions,
                    text="📋 Copy",
                    bg="#1e2433",
                    fg="#00e5ff",
                    activebackground="#00e5ff",
                    activeforeground="#0a0e17",
                    relief="flat",
                    bd=0,
                    highlightthickness=0,
                    font=(self.theme.font_family, 8, "bold"),
                    cursor="hand2",
                    padx=10,
                    pady=2,
                )
                copy_btn.pack(side="left", padx=4)
                copy_btn.configure(
                    command=self._make_copy_callback(item.content, copy_btn)
                )

            del_btn = tk.Button(
                actions,
                text="🗑",
                bg="#1c212c",
                fg="#64748b",
                activeforeground="#ef4444",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                command=lambda i=item.id: self._delete_code_item(i),
            )
            del_btn.pack(side="left", padx=2)

            # Code / Content box
            if item.content:
                code_box = tk.Label(
                    card,
                    text=item.content,
                    bg="#0f131a",
                    fg="#cbd5e1",
                    font=("courier", 9),
                    anchor="w",
                    justify="left",
                    padx=10,
                    pady=8,
                )
                code_box.pack(fill="x", pady=4)

            if item.notes:
                tk.Label(
                    card,
                    text=f"Note: {item.notes}",
                    bg="#1c212c",
                    fg="#64748b",
                    font=(self.theme.font_family, 8),
                    anchor="w",
                ).pack(fill="x")

    def _make_copy_callback(
        self, text: str, btn: tk.Button
    ) -> Callable[[], None]:
        return lambda: self._copy_to_clipboard(text, btn)

    def _copy_to_clipboard(self, text: str, btn: tk.Button) -> None:

        self.clipboard_clear()
        self.clipboard_append(text)
        btn.config(text="✓ Copied!", fg="#10b981")
        self.after(1500, lambda: btn.config(text="📋 Copy", fg="#00e5ff"))

    def _toggle_dsa_done(self, item_id: str) -> None:
        if self.code_service:
            self.code_service.toggle_done(item_id)
            self._refresh_code()

    def _delete_code_item(self, item_id: str) -> None:
        if (
            messagebox.askyesno(
                "Delete Item", "Delete this code item?", parent=self
            )
            and self.code_service
        ):
            self.code_service.soft_delete_item(item_id)
            self._refresh_code()

    def _open_create_code(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add Code Item")
        dialog.geometry("480x420")
        dialog.configure(bg="#151922")
        dialog.transient(self)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg="#151922", padx=20, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Category:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        cat_combo = ttk.Combobox(
            frame,
            values=[
                "Snippets",
                "CLI Commands",
                "Syntax Reference",
                "DSA Problem Tracker",
            ],
            state="readonly",
        )
        cat_combo.set("Snippets")
        cat_combo.pack(fill="x", pady=(2, 8))

        tk.Label(
            frame,
            text="Title *:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        title_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 10),
        )
        title_entry.pack(fill="x", pady=(2, 8), ipady=3)

        tk.Label(
            frame,
            text="Code Content / Syntax:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        content_text = tk.Text(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            height=5,
            font=("courier", 9),
        )
        content_text.pack(fill="x", pady=(2, 8))

        tk.Label(
            frame,
            text="URL / Problem Link (optional):",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        url_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 9),
        )
        url_entry.pack(fill="x", pady=(2, 12), ipady=2)

        def _save() -> None:
            t = title_entry.get().strip()
            if not t:
                messagebox.showerror(
                    "Error", "Title cannot be empty.", parent=dialog
                )
                return
            if self.code_service:
                self.code_service.create_item(
                    category=cat_combo.get(),
                    title=t,
                    content=content_text.get("1.0", tk.END).strip(),
                    url=url_entry.get().strip(),
                )
                self._refresh_code()
                dialog.destroy()

        tk.Button(
            frame,
            text="Save Item",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=_save,
            padx=12,
            pady=4,
            cursor="hand2",
        ).pack(side="right")

    # ==========================================
    # 3. COURSES TAB VIEW
    # ==========================================

    def _build_courses_view(self) -> None:
        head_bar = tk.Frame(
            self.courses_container, bg="#161922", padx=20, pady=16
        )
        head_bar.pack(fill="x")

        self.course_title_label = tk.Label(
            head_bar,
            text="🎓 Course & Learning Tracker",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 13, "bold"),
        )
        self.course_title_label.pack(side="left")

        new_course_btn = tk.Button(
            head_bar,
            text="+ Add Course",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9, "bold"),
            command=self._open_create_course,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        new_course_btn.pack(side="right")

        filter_bar = tk.Frame(self.courses_container, bg="#161922", padx=20)
        filter_bar.pack(fill="x", pady=(0, 10))

        search_box = tk.Frame(filter_bar, bg="#161922")
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(search_box, text="🔍", bg="#161922", fg="#64748b").pack(
            side="left", padx=(0, 4)
        )
        self.course_search_entry = tk.Entry(
            search_box,
            bg="#12151c",
            fg="#f8fafc",
            relief="flat",
            insertbackground="#00e5ff",
            font=(self.theme.font_family, 9),
        )
        self.course_search_entry.pack(
            side="left", fill="x", expand=True, ipady=3
        )
        self.course_search_entry.bind(
            "<KeyRelease>", lambda _e: self._refresh_courses()
        )

        pills_box = tk.Frame(filter_bar, bg="#161922")
        pills_box.pack(side="right")
        self.course_filter_btns: dict[str, tk.Button] = {}
        for p in ["All", "Coursera", "NPTEL", "University", "Self-Paced"]:
            btn = tk.Button(
                pills_box,
                text=p,
                bg="#1e2433",
                fg="#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda plat=p: self._set_course_filter(plat),
            )
            btn.pack(side="left", padx=2)
            self.course_filter_btns[p] = btn

        self.courses_scroll = ScrollableFrame(
            self.courses_container, bg="#161922"
        )
        self.courses_scroll.pack(
            fill="both", expand=True, padx=20, pady=(0, 16)
        )

    def _set_course_filter(self, platform: str) -> None:
        self.course_filter = platform
        for p, btn in self.course_filter_btns.items():
            if p == platform:
                btn.configure(bg="#0284c7", fg="#ffffff")
            else:
                btn.configure(bg="#1e2433", fg="#94a3b8")
        self._refresh_courses()

    def _refresh_courses(self) -> None:
        if not self.course_service:
            return

        for child in self.courses_scroll.interior.winfo_children():
            child.destroy()

        query = self.course_search_entry.get().strip() or None
        courses = self.course_service.list_courses(
            platform=(
                None if self.course_filter == "All" else self.course_filter
            ),
            search_query=query,
        )
        self.course_title_label.config(
            text=f"🎓 Course & Learning Tracker ({len(courses)})"
        )

        if not courses:
            tk.Label(
                self.courses_scroll.interior,
                text="No courses found.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 10),
                pady=30,
            ).pack()
            return

        for c in courses:
            card = tk.Frame(
                self.courses_scroll.interior, bg="#1c212c", padx=16, pady=12
            )
            card.pack(fill="x", pady=6)

            top = tk.Frame(card, bg="#1c212c")
            top.pack(fill="x")

            tk.Label(
                top,
                text=c.title,
                bg="#1c212c",
                fg="#f8fafc",
                font=(self.theme.font_family, 10, "bold"),
            ).pack(side="left")

            tk.Label(
                top,
                text=f" {c.platform} ",
                bg="#2b3448",
                fg="#00e5ff",
                font=(self.theme.font_family, 8),
            ).pack(side="left", padx=8)

            actions = tk.Frame(top, bg="#1c212c")
            actions.pack(side="right")

            if c.completed_modules < c.total_modules:
                inc_btn = tk.Button(
                    actions,
                    text="+1 Module",
                    bg="#0284c7",
                    fg="#ffffff",
                    relief="flat",
                    bd=0,
                    highlightthickness=0,
                    font=(self.theme.font_family, 8, "bold"),
                    cursor="hand2",
                    padx=8,
                    pady=2,
                    command=lambda cid=c.id: self._inc_course(cid),
                )
                inc_btn.pack(side="left", padx=4)
            else:
                tk.Label(
                    actions,
                    text="✓ Completed",
                    bg="#1c212c",
                    fg="#10b981",
                    font=(self.theme.font_family, 8, "bold"),
                ).pack(side="left", padx=4)

            if c.url:
                tk.Button(
                    actions,
                    text="🔗 Open",
                    bg="#1e2433",
                    fg="#94a3b8",
                    relief="flat",
                    bd=0,
                    highlightthickness=0,
                    font=(self.theme.font_family, 8),
                    cursor="hand2",
                    command=lambda u=c.url: webbrowser.open(u),
                ).pack(side="left", padx=4)

            tk.Button(
                actions,
                text="🗑",
                bg="#1c212c",
                fg="#64748b",
                activeforeground="#ef4444",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                command=lambda cid=c.id: self._delete_course(cid),
            ).pack(side="left", padx=2)

            # Progress Bar
            pct = int((c.completed_modules / max(1, c.total_modules)) * 100)
            bar_text = (
                f"Progress: {c.completed_modules}/{c.total_modules} "
                f"modules ({pct}%)"
            )
            tk.Label(
                card,
                text=bar_text,
                bg="#1c212c",
                fg="#94a3b8",
                font=(self.theme.font_family, 8),
                anchor="w",
            ).pack(fill="x", pady=(6, 2))

            prog_bg = tk.Frame(card, bg="#12151c", height=6)
            prog_bg.pack(fill="x", pady=(2, 6))
            fill_frame = tk.Frame(prog_bg, bg="#00e5ff", height=6)
            fill_frame.place(relx=0, rely=0, relwidth=min(1.0, pct / 100))

            if c.instructor or c.notes:
                meta = f"Instructor: {c.instructor}" if c.instructor else ""
                if c.notes:
                    meta += f" • Note: {c.notes}"
                tk.Label(
                    card,
                    text=meta,
                    bg="#1c212c",
                    fg="#64748b",
                    font=(self.theme.font_family, 8),
                    anchor="w",
                ).pack(fill="x")

    def _inc_course(self, course_id: str) -> None:
        if self.course_service:
            self.course_service.increment_module(course_id)
            self._refresh_courses()

    def _delete_course(self, course_id: str) -> None:
        if (
            messagebox.askyesno("Delete", "Delete this course?", parent=self)
            and self.course_service
        ):
            self.course_service.soft_delete_course(course_id)
            self._refresh_courses()

    def _open_create_course(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add Course")
        dialog.geometry("420x360")
        dialog.configure(bg="#151922")
        dialog.transient(self)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg="#151922", padx=20, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Course Title *:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        t_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 10),
        )
        t_entry.pack(fill="x", pady=(2, 8), ipady=3)

        tk.Label(
            frame,
            text="Platform:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        p_combo = ttk.Combobox(
            frame,
            values=["Coursera", "NPTEL", "University", "YouTube", "Self-Paced"],
            state="readonly",
        )
        p_combo.set("Coursera")
        p_combo.pack(fill="x", pady=(2, 8))

        tk.Label(
            frame,
            text="Total Modules:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        m_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 10),
        )
        m_entry.insert(0, "10")
        m_entry.pack(fill="x", pady=(2, 8), ipady=2)

        tk.Label(
            frame,
            text="Course URL (optional):",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        u_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 9),
        )
        u_entry.pack(fill="x", pady=(2, 12), ipady=2)

        def _save() -> None:
            title = t_entry.get().strip()
            if not title:
                return
            try:
                tot = int(m_entry.get().strip() or "10")
            except ValueError:
                tot = 10
            if self.course_service:
                self.course_service.create_course(
                    title=title,
                    platform=p_combo.get(),
                    total_modules=tot,
                    url=u_entry.get().strip(),
                )
                self._refresh_courses()
                dialog.destroy()

        tk.Button(
            frame,
            text="Save Course",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=_save,
            padx=12,
            pady=4,
        ).pack(side="right")

    # ==========================================
    # 4. IDEAS & DOUBTS TAB VIEW
    # ==========================================

    def _build_ideas_view(self) -> None:
        head_bar = tk.Frame(
            self.ideas_container, bg="#161922", padx=20, pady=16
        )
        head_bar.pack(fill="x")

        self.idea_title_label = tk.Label(
            head_bar,
            text="💡 Project Ideas & Concept Doubts",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 13, "bold"),
        )
        self.idea_title_label.pack(side="left")

        new_btn = tk.Button(
            head_bar,
            text="+ Add Idea / Doubt",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9, "bold"),
            command=self._open_create_idea,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        new_btn.pack(side="right")

        filter_bar = tk.Frame(self.ideas_container, bg="#161922", padx=20)
        filter_bar.pack(fill="x", pady=(0, 10))

        search_box = tk.Frame(filter_bar, bg="#161922")
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(search_box, text="🔍", bg="#161922", fg="#64748b").pack(
            side="left", padx=(0, 4)
        )
        self.idea_search_entry = tk.Entry(
            search_box,
            bg="#12151c",
            fg="#f8fafc",
            relief="flat",
            insertbackground="#00e5ff",
            font=(self.theme.font_family, 9),
        )
        self.idea_search_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.idea_search_entry.bind(
            "<KeyRelease>", lambda _e: self._refresh_ideas()
        )

        pills_box = tk.Frame(filter_bar, bg="#161922")
        pills_box.pack(side="right")
        self.idea_filter_btns: dict[str, tk.Button] = {}
        pill_labels = {"All": "All", "Idea": "💡 Ideas", "Doubt": "❓ Doubts"}
        for k in ["All", "Idea", "Doubt"]:
            btn = tk.Button(
                pills_box,
                text=pill_labels.get(k, k),
                bg="#1e2433",
                fg="#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda kind=k: self._set_idea_filter(kind),
            )
            btn.pack(side="left", padx=2)
            self.idea_filter_btns[k] = btn

        self.ideas_scroll = ScrollableFrame(self.ideas_container, bg="#161922")
        self.ideas_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _set_idea_filter(self, kind: str) -> None:
        self.idea_filter = kind
        for k, btn in self.idea_filter_btns.items():
            if k == kind:
                btn.configure(bg="#0284c7", fg="#ffffff")
            else:
                btn.configure(bg="#1e2433", fg="#94a3b8")
        self._refresh_ideas()

    def _refresh_ideas(self) -> None:
        if not self.idea_doubt_service:
            return

        for child in self.ideas_scroll.interior.winfo_children():
            child.destroy()

        query = self.idea_search_entry.get().strip() or None
        items = self.idea_doubt_service.list_items(
            kind=None if self.idea_filter == "All" else self.idea_filter,
            search_query=query,
        )
        self.idea_title_label.config(
            text=f"💡 Project Ideas & Concept Doubts ({len(items)})"
        )

        if not items:
            tk.Label(
                self.ideas_scroll.interior,
                text="No ideas or doubts recorded.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 10),
                pady=30,
            ).pack()
            return

        for item in items:
            card = tk.Frame(
                self.ideas_scroll.interior, bg="#1c212c", padx=16, pady=12
            )
            card.pack(fill="x", pady=6)

            top = tk.Frame(card, bg="#1c212c")
            top.pack(fill="x")

            badge_text = "💡 Idea" if item.kind == "Idea" else "❓ Doubt"
            badge_bg = "#3b2d18" if item.kind == "Idea" else "#1e293b"
            badge_fg = "#f59e0b" if item.kind == "Idea" else "#38bdf8"
            tk.Label(
                top,
                text=f" {badge_text} ",
                bg=badge_bg,
                fg=badge_fg,
                font=(self.theme.font_family, 8, "bold"),
            ).pack(side="left")

            tk.Label(
                top,
                text=item.title,
                bg="#1c212c",
                fg="#f8fafc",
                font=(self.theme.font_family, 10, "bold"),
            ).pack(side="left", padx=8)

            actions = tk.Frame(top, bg="#1c212c")
            actions.pack(side="right")

            status_color = (
                "#10b981"
                if item.status in ("Resolved", "Completed")
                else "#00e5ff"
            )
            status_btn = tk.Button(
                actions,
                text=f"[{item.status}]",
                bg="#242b3b",
                fg=status_color,
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8, "bold"),
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda i=item.id: self._advance_idea(i),
            )
            status_btn.pack(side="left", padx=4)

            tk.Button(
                actions,
                text="🗑",
                bg="#1c212c",
                fg="#64748b",
                activeforeground="#ef4444",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                command=lambda i=item.id: self._delete_idea(i),
            ).pack(side="left", padx=2)

            if item.tech_stack_or_ref:
                label_prefix = (
                    "Tech Stack: " if item.kind == "Idea" else "Reference: "
                )
                tk.Label(
                    card,
                    text=f"{label_prefix}{item.tech_stack_or_ref}",
                    bg="#1c212c",
                    fg="#00e5ff",
                    font=(self.theme.font_family, 8),
                    anchor="w",
                ).pack(fill="x", pady=(4, 2))

            if item.description:
                tk.Label(
                    card,
                    text=item.description,
                    bg="#1c212c",
                    fg="#94a3b8",
                    font=(self.theme.font_family, 9),
                    anchor="w",
                    justify="left",
                ).pack(fill="x", pady=(2, 0))

    def _advance_idea(self, item_id: str) -> None:
        if self.idea_doubt_service:
            self.idea_doubt_service.advance_status(item_id)
            self._refresh_ideas()

    def _delete_idea(self, item_id: str) -> None:
        if (
            messagebox.askyesno("Delete", "Delete this item?", parent=self)
            and self.idea_doubt_service
        ):
            self.idea_doubt_service.soft_delete_item(item_id)
            self._refresh_ideas()

    def _open_create_idea(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add Idea or Doubt")
        dialog.geometry("440x360")
        dialog.configure(bg="#151922")
        dialog.transient(self)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg="#151922", padx=20, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Entry Type:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        k_combo = ttk.Combobox(
            frame, values=["Idea", "Doubt"], state="readonly"
        )
        k_combo.set("Idea")
        k_combo.pack(fill="x", pady=(2, 8))

        tk.Label(
            frame,
            text="Title / Question *:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        t_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 10),
        )
        t_entry.pack(fill="x", pady=(2, 8), ipady=3)

        tk.Label(
            frame,
            text="Tech Stack / Subject Reference:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        ref_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 9),
        )
        ref_entry.pack(fill="x", pady=(2, 8), ipady=2)

        tk.Label(
            frame,
            text="Description / Details:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        d_text = tk.Text(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            height=3,
            font=(self.theme.font_family, 9),
        )
        d_text.pack(fill="x", pady=(2, 12))

        def _save() -> None:
            t = t_entry.get().strip()
            if not t:
                return
            kind = k_combo.get()
            init_status = "Idea" if kind == "Idea" else "Open"
            if self.idea_doubt_service:
                self.idea_doubt_service.create_item(
                    kind=kind,
                    title=t,
                    tech_stack_or_ref=ref_entry.get().strip(),
                    description=d_text.get("1.0", tk.END).strip(),
                    status=init_status,
                )
                self._refresh_ideas()
                dialog.destroy()

        tk.Button(
            frame,
            text="Save Entry",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=_save,
            padx=12,
            pady=4,
        ).pack(side="right")

    # ==========================================
    # 5. OPPORTUNITIES TAB VIEW
    # ==========================================

    def _build_opportunities_view(self) -> None:
        head_bar = tk.Frame(self.opps_container, bg="#161922", padx=20, pady=16)
        head_bar.pack(fill="x")

        self.opp_title_label = tk.Label(
            head_bar,
            text="🚀 Opportunities & Career Tracker",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 13, "bold"),
        )
        self.opp_title_label.pack(side="left")

        new_btn = tk.Button(
            head_bar,
            text="+ Add Opportunity",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9, "bold"),
            command=self._open_create_opportunity,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        new_btn.pack(side="right")

        filter_bar = tk.Frame(self.opps_container, bg="#161922", padx=20)
        filter_bar.pack(fill="x", pady=(0, 10))

        search_box = tk.Frame(filter_bar, bg="#161922")
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(search_box, text="🔍", bg="#161922", fg="#64748b").pack(
            side="left", padx=(0, 4)
        )
        self.opp_search_entry = tk.Entry(
            search_box,
            bg="#12151c",
            fg="#f8fafc",
            relief="flat",
            insertbackground="#00e5ff",
            font=(self.theme.font_family, 9),
        )
        self.opp_search_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.opp_search_entry.bind(
            "<KeyRelease>", lambda _e: self._refresh_opportunities()
        )

        pills_box = tk.Frame(filter_bar, bg="#161922")
        pills_box.pack(side="right")
        self.opp_filter_btns: dict[str, tk.Button] = {}
        for k in ["All", "Internship", "Job", "Hackathon", "Scholarship"]:
            btn = tk.Button(
                pills_box,
                text=k,
                bg="#1e2433",
                fg="#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda kind=k: self._set_opp_filter(kind),
            )
            btn.pack(side="left", padx=2)
            self.opp_filter_btns[k] = btn

        self.opps_scroll = ScrollableFrame(self.opps_container, bg="#161922")
        self.opps_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _set_opp_filter(self, kind: str) -> None:
        self.opp_filter = kind
        for k, btn in self.opp_filter_btns.items():
            if k == kind:
                btn.configure(bg="#0284c7", fg="#ffffff")
            else:
                btn.configure(bg="#1e2433", fg="#94a3b8")
        self._refresh_opportunities()

    def _refresh_opportunities(self) -> None:
        if not self.opportunity_service:
            return

        for child in self.opps_scroll.interior.winfo_children():
            child.destroy()

        query = self.opp_search_entry.get().strip() or None
        items = self.opportunity_service.list_opportunities(
            kind=None if self.opp_filter == "All" else self.opp_filter,
            search_query=query,
        )
        self.opp_title_label.config(
            text=f"🚀 Opportunities & Career Tracker ({len(items)})"
        )

        if not items:
            tk.Label(
                self.opps_scroll.interior,
                text="No opportunities saved.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 10),
                pady=30,
            ).pack()
            return

        for opp in items:
            card = tk.Frame(
                self.opps_scroll.interior, bg="#1c212c", padx=16, pady=12
            )
            card.pack(fill="x", pady=6)

            top = tk.Frame(card, bg="#1c212c")
            top.pack(fill="x")

            tk.Label(
                top,
                text=opp.title,
                bg="#1c212c",
                fg="#f8fafc",
                font=(self.theme.font_family, 10, "bold"),
            ).pack(side="left")

            tk.Label(
                top,
                text=f" {opp.kind} ",
                bg="#2b3448",
                fg="#00e5ff",
                font=(self.theme.font_family, 8),
            ).pack(side="left", padx=8)

            actions = tk.Frame(top, bg="#1c212c")
            actions.pack(side="right")

            st_btn = tk.Button(
                actions,
                text=f"[{opp.status}]",
                bg="#242b3b",
                fg="#00e5ff",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8, "bold"),
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda oid=opp.id: self._advance_opp(oid),
            )
            st_btn.pack(side="left", padx=4)

            if opp.url:
                tk.Button(
                    actions,
                    text="🔗 Apply",
                    bg="#0284c7",
                    fg="#ffffff",
                    relief="flat",
                    bd=0,
                    highlightthickness=0,
                    font=(self.theme.font_family, 8),
                    cursor="hand2",
                    padx=8,
                    pady=2,
                    command=lambda u=opp.url: webbrowser.open(u),
                ).pack(side="left", padx=4)

            tk.Button(
                actions,
                text="🗑",
                bg="#1c212c",
                fg="#64748b",
                activeforeground="#ef4444",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                command=lambda oid=opp.id: self._delete_opp(oid),
            ).pack(side="left", padx=2)

            sub = f"Organization: {opp.organization}"
            if opp.deadline:
                sub += f" • Deadline: {opp.deadline}"
            tk.Label(
                card,
                text=sub,
                bg="#1c212c",
                fg="#94a3b8",
                font=(self.theme.font_family, 8),
                anchor="w",
            ).pack(fill="x", pady=(4, 2))

            if opp.notes:
                tk.Label(
                    card,
                    text=opp.notes,
                    bg="#1c212c",
                    fg="#64748b",
                    font=(self.theme.font_family, 8),
                    anchor="w",
                ).pack(fill="x")

    def _advance_opp(self, opp_id: str) -> None:
        if self.opportunity_service:
            self.opportunity_service.advance_status(opp_id)
            self._refresh_opportunities()

    def _delete_opp(self, opp_id: str) -> None:
        if (
            messagebox.askyesno("Delete", "Delete opportunity?", parent=self)
            and self.opportunity_service
        ):
            self.opportunity_service.soft_delete_opportunity(opp_id)
            self._refresh_opportunities()

    def _open_create_opportunity(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add Opportunity")
        dialog.geometry("440x360")
        dialog.configure(bg="#151922")
        dialog.transient(self)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg="#151922", padx=20, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Role / Event Title *:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        t_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 10),
        )
        t_entry.pack(fill="x", pady=(2, 8), ipady=3)

        tk.Label(
            frame,
            text="Company / Organization *:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        o_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 9),
        )
        o_entry.pack(fill="x", pady=(2, 8), ipady=2)

        tk.Label(
            frame,
            text="Type:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        k_combo = ttk.Combobox(
            frame,
            values=["Internship", "Job", "Hackathon", "Scholarship"],
            state="readonly",
        )
        k_combo.set("Internship")
        k_combo.pack(fill="x", pady=(2, 8))

        tk.Label(
            frame,
            text="Application URL (optional):",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        u_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 9),
        )
        u_entry.pack(fill="x", pady=(2, 12), ipady=2)

        def _save() -> None:
            t = t_entry.get().strip()
            org = o_entry.get().strip()
            if not t or not org:
                return
            if self.opportunity_service:
                self.opportunity_service.create_opportunity(
                    title=t,
                    organization=org,
                    kind=k_combo.get(),
                    url=u_entry.get().strip(),
                )
                self._refresh_opportunities()
                dialog.destroy()

        tk.Button(
            frame,
            text="Save Opportunity",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=_save,
            padx=12,
            pady=4,
        ).pack(side="right")

    # ==========================================
    # 6. QUICK LINKS TAB VIEW
    # ==========================================

    def _build_quick_links_view(self) -> None:
        head_bar = tk.Frame(
            self.links_container, bg="#161922", padx=20, pady=16
        )
        head_bar.pack(fill="x")

        self.link_title_label = tk.Label(
            head_bar,
            text="⚡ Quick Links & Workspace Shortcuts",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 13, "bold"),
        )
        self.link_title_label.pack(side="left")

        new_btn = tk.Button(
            head_bar,
            text="+ Add Quick Link",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9, "bold"),
            command=self._open_create_link,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        new_btn.pack(side="right")

        filter_bar = tk.Frame(self.links_container, bg="#161922", padx=20)
        filter_bar.pack(fill="x", pady=(0, 10))

        search_box = tk.Frame(filter_bar, bg="#161922")
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(search_box, text="🔍", bg="#161922", fg="#64748b").pack(
            side="left", padx=(0, 4)
        )
        self.link_search_entry = tk.Entry(
            search_box,
            bg="#12151c",
            fg="#f8fafc",
            relief="flat",
            insertbackground="#00e5ff",
            font=(self.theme.font_family, 9),
        )
        self.link_search_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.link_search_entry.bind(
            "<KeyRelease>", lambda _e: self._refresh_quick_links()
        )

        pills_box = tk.Frame(filter_bar, bg="#161922")
        pills_box.pack(side="right")
        self.link_filter_btns: dict[str, tk.Button] = {}
        for cat in ["All", "Web", "Local Folder", "Local File", "Tool"]:
            btn = tk.Button(
                pills_box,
                text=cat,
                bg="#1e2433",
                fg="#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda c=cat: self._set_link_filter(c),
            )
            btn.pack(side="left", padx=2)
            self.link_filter_btns[cat] = btn

        self.links_scroll = ScrollableFrame(self.links_container, bg="#161922")
        self.links_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _set_link_filter(self, category: str) -> None:
        self.link_filter = category
        for c, btn in self.link_filter_btns.items():
            if c == category:
                btn.configure(bg="#0284c7", fg="#ffffff")
            else:
                btn.configure(bg="#1e2433", fg="#94a3b8")
        self._refresh_quick_links()

    def _refresh_quick_links(self) -> None:
        if not self.quick_link_service:
            return

        for child in self.links_scroll.interior.winfo_children():
            child.destroy()

        query = self.link_search_entry.get().strip() or None
        links = self.quick_link_service.list_links(
            category=None if self.link_filter == "All" else self.link_filter,
            search_query=query,
        )
        self.link_title_label.config(
            text=f"⚡ Quick Links & Shortcuts ({len(links)})"
        )

        if not links:
            tk.Label(
                self.links_scroll.interior,
                text="No shortcuts configured.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 10),
                pady=30,
            ).pack()
            return

        for link in links:
            card = tk.Frame(
                self.links_scroll.interior, bg="#1c212c", padx=16, pady=12
            )
            card.pack(fill="x", pady=6)

            top = tk.Frame(card, bg="#1c212c")
            top.pack(fill="x")

            tk.Label(
                top,
                text=link.name,
                bg="#1c212c",
                fg="#f8fafc",
                font=(self.theme.font_family, 10, "bold"),
            ).pack(side="left")

            tk.Label(
                top,
                text=f" {link.category} ",
                bg="#2b3448",
                fg="#00e5ff",
                font=(self.theme.font_family, 8),
            ).pack(side="left", padx=8)

            tk.Label(
                top,
                text=f"🔥 {link.click_count} clicks",
                bg="#1c212c",
                fg="#f59e0b",
                font=(self.theme.font_family, 8),
            ).pack(side="left")

            actions = tk.Frame(top, bg="#1c212c")
            actions.pack(side="right")

            open_btn = tk.Button(
                actions,
                text="🚀 Open",
                bg="#00e5ff",
                fg="#0a0e17",
                activebackground="#00b4d8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8, "bold"),
                cursor="hand2",
                padx=10,
                pady=2,
                command=lambda lnk=link: self._launch_quick_link(lnk),
            )
            open_btn.pack(side="left", padx=4)

            tk.Button(
                actions,
                text="🗑",
                bg="#1c212c",
                fg="#64748b",
                activeforeground="#ef4444",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                command=lambda lid=link.id: self._delete_link(lid),
            ).pack(side="left", padx=2)

            tk.Label(
                card,
                text=link.target_uri,
                bg="#1c212c",
                fg="#64748b",
                font=("courier", 8),
                anchor="w",
            ).pack(fill="x", pady=(4, 0))

    def _launch_quick_link(self, link: QuickLink) -> None:
        uri = link.target_uri
        if uri.startswith(("http://", "https://")):
            webbrowser.open(uri)
        else:
            expanded = os.path.expanduser(uri)
            subprocess.Popen(["xdg-open", expanded])

        if self.quick_link_service:
            self.quick_link_service.record_click(link.id)
            self._refresh_quick_links()

    def _delete_link(self, link_id: str) -> None:
        if (
            messagebox.askyesno("Delete", "Delete quick link?", parent=self)
            and self.quick_link_service
        ):
            self.quick_link_service.soft_delete_link(link_id)
            self._refresh_quick_links()

    def _open_create_link(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add Quick Link")
        dialog.geometry("440x280")
        dialog.configure(bg="#151922")
        dialog.transient(self)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg="#151922", padx=20, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Display Name *:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        n_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 10),
        )
        n_entry.pack(fill="x", pady=(2, 8), ipady=3)

        tk.Label(
            frame,
            text="Target URI (Web URL or Local Path) *:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        u_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 9),
        )
        u_entry.pack(fill="x", pady=(2, 8), ipady=2)

        tk.Label(
            frame,
            text="Category:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        c_combo = ttk.Combobox(
            frame,
            values=["Web", "Local Folder", "Local File", "Tool"],
            state="readonly",
        )
        c_combo.set("Web")
        c_combo.pack(fill="x", pady=(2, 12))

        def _save() -> None:
            name = n_entry.get().strip()
            uri = u_entry.get().strip()
            if not name or not uri:
                return
            if self.quick_link_service:
                self.quick_link_service.create_link(
                    name=name,
                    target_uri=uri,
                    category=c_combo.get(),
                )
                self._refresh_quick_links()
                dialog.destroy()

        tk.Button(
            frame,
            text="Save Shortcut",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=_save,
            padx=12,
            pady=4,
        ).pack(side="right")

    # ==========================================
    # 7. SETTINGS & INFO TAB VIEW
    # ==========================================

    def _build_settings_view(self) -> None:
        head_bar = tk.Frame(
            self.settings_container, bg="#161922", padx=20, pady=16
        )
        head_bar.pack(fill="x")

        tk.Label(
            head_bar,
            text="⚙️ Preferences & Diagnostics",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 13, "bold"),
        ).pack(side="left")

        content = tk.Frame(self.settings_container, bg="#161922", padx=20)
        content.pack(fill="both", expand=True)

        # Widget Controls
        card1 = tk.Frame(content, bg="#1c212c", padx=16, pady=14)
        card1.pack(fill="x", pady=6)

        tk.Label(
            card1,
            text="Widget Behavior",
            bg="#1c212c",
            fg="#00e5ff",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        self.topmost_var = tk.BooleanVar(value=True)
        topmost_chk = tk.Checkbutton(
            card1,
            text="Keep floating capsule always-on-top",
            variable=self.topmost_var,
            bg="#1c212c",
            fg="#f8fafc",
            selectcolor="#12151c",
            activebackground="#1c212c",
            activeforeground="#00e5ff",
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=self._toggle_topmost,
        )
        topmost_chk.pack(anchor="w", pady=2)

        # Storage & System
        card2 = tk.Frame(content, bg="#1c212c", padx=16, pady=14)
        card2.pack(fill="x", pady=6)

        tk.Label(
            card2,
            text="Local Database Status",
            bg="#1c212c",
            fg="#00e5ff",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        db_path = str(config.get_db_path())
        tk.Label(
            card2,
            text=f"SQLite Store: {db_path}",
            bg="#1c212c",
            fg="#94a3b8",
            font=("courier", 8),
            anchor="w",
        ).pack(fill="x", pady=2)

        tk.Label(
            card2,
            text="Engine: SQLite 3.12+ WAL Mode (Advisory single-instance)",
            bg="#1c212c",
            fg="#64748b",
            font=(self.theme.font_family, 8),
            anchor="w",
        ).pack(fill="x", pady=2)

        # Actions card
        card3 = tk.Frame(content, bg="#1c212c", padx=16, pady=14)
        card3.pack(fill="x", pady=6)

        tk.Label(
            card3,
            text="Diagnostics & Testing Actions",
            bg="#1c212c",
            fg="#00e5ff",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        btn_row = tk.Frame(card3, bg="#1c212c")
        btn_row.pack(fill="x")

        tk.Button(
            btn_row,
            text="🔔 Send Test Notification",
            bg="#0284c7",
            fg="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9),
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._send_test_notification,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_row,
            text="🔄 Reseed Demo Data",
            bg="#2b3448",
            fg="#f8fafc",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 9),
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._reseed_data,
        ).pack(side="left")

    def _toggle_topmost(self) -> None:
        try:
            self.master.wm_attributes("-topmost", self.topmost_var.get())
        except Exception as exc:
            logger.warning("Could not set topmost: %s", exc)

    def _send_test_notification(self) -> None:
        self.notification_queue.push(
            title="System Alert",
            message="Test notification from PLUS-ULTRA workspace panel.",
            icon="🔔",
        )
        self._refresh_notifications()
        send_desktop_notification(
            title="PLUS-ULTRA Alert",
            message="Test notification pipeline verified.",
            urgency="normal",
        )

    def _reseed_data(self) -> None:
        from plus_ultra.db import get_connection, seed_demo_workspace_data

        conn = get_connection()
        try:
            seed_demo_workspace_data(conn)
        finally:
            conn.close()
        self._refresh_tasks()
        self._refresh_code()
        self._refresh_courses()
        self._refresh_ideas()
        self._refresh_opportunities()
        self._refresh_quick_links()
        messagebox.showinfo(
            "Reseed Complete",
            "Demo sample data populated for all tabs.",
            parent=self,
        )

    def _refresh_settings(self) -> None:
        pass

    # ==========================================
    # NOTIFICATION PANEL & SHARED CONTROLS
    # ==========================================

    def _build_notification_panel(self) -> None:
        head = tk.Frame(self.notif_col, bg="#12151c", padx=14, pady=18)
        head.pack(fill="x")

        tk.Label(
            head,
            text="🔔 Notifications",
            bg="#12151c",
            fg="#f8fafc",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(side="left")

        actions_frame = tk.Frame(self.notif_col, bg="#12151c", padx=14, pady=4)
        actions_frame.pack(fill="x")

        mark_all_btn = tk.Button(
            actions_frame,
            text="Mark All Read",
            bg="#1e2433",
            fg="#00e5ff",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 8),
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._mark_all_notifications_read,
        )
        mark_all_btn.pack(side="left")

        clear_btn = tk.Button(
            actions_frame,
            text="Clear",
            bg="#1e2433",
            fg="#94a3b8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 8),
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._clear_all_notifications,
        )
        clear_btn.pack(side="right")

        self.notif_listbox = tk.Listbox(
            self.notif_col,
            bg="#12151c",
            fg="#e2e8f0",
            selectbackground="#1e2433",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 8),
        )
        self.notif_listbox.pack(fill="both", expand=True, padx=14, pady=8)

    def _refresh_categories(self) -> None:
        self.active_categories = self.category_service.list_active()

    def _refresh_tasks(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        status_param = (
            None if self.status_filter == "All" else self.status_filter
        )
        prio_param = None if self.prio_filter == "All" else self.prio_filter
        search_query = self.search_entry.get().strip()

        tasks = self.task_service.list_tasks(
            category_id=self.category_filter_id,
            status=status_param,
            critical_level=prio_param,
            search_query=search_query or None,
        )

        cat_lookup = {c.id: c.name for c in self.active_categories}
        for task in tasks:
            status_symbol = (
                "✓ Completed"
                if task.status == "Completed"
                else "○ " + task.status
            )
            cat_name = cat_lookup.get(task.category_id or "", "—")
            due_display = task.due_date if task.due_date else "—"

            self.tree.insert(
                "",
                "end",
                iid=task.id,
                values=(
                    status_symbol,
                    task.title,
                    cat_name,
                    task.critical_level,
                    task.pace_level,
                    due_display,
                ),
            )

        self.tasks_title_label.config(text=f"Tasks & Deadlines ({len(tasks)})")

    def _refresh_notifications(self) -> None:
        self.notif_listbox.delete(0, tk.END)
        all_notifs = self.notification_queue.list_all()
        if not all_notifs:
            self.notif_listbox.insert(tk.END, "No recent alerts.")
        else:
            for item in all_notifs:
                unread_marker = "• " if not item.is_read else "  "
                display = f"{unread_marker}{item.icon} {item.title}"
                self.notif_listbox.insert(tk.END, display)

    def _set_status_filter(self, status: str) -> None:
        self.status_filter = status
        self._refresh_tasks()

    def _on_prio_filter_change(self) -> None:
        val = self.prio_filter_combo.get()
        self.prio_filter = "All" if val == "All Priority" else val
        self._refresh_tasks()

    def _on_tree_double_click(self, _event: tk.Event[Any]) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        task_id = selected[0]
        task = self.task_service.get_task(task_id)
        if task:
            self._open_edit_task(task)

    def _on_tree_right_click(self, event: tk.Event[Any]) -> None:
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)

        menu = tk.Menu(self, tearoff=0, bg="#1e2433", fg="#f8fafc")
        menu.add_command(
            label="Toggle Status (Pending / Completed)",
            command=lambda: self._toggle_selected_status(item),
        )
        menu.add_command(
            label="Edit Task...", command=lambda: self._edit_selected(item)
        )
        menu.add_separator()
        menu.add_command(
            label="Delete Task", command=lambda: self._delete_selected(item)
        )
        menu.tk_popup(event.x_root, event.y_root)

    def _toggle_selected_status(self, task_id: str) -> None:
        self.task_service.toggle_status(task_id)
        self._refresh_tasks()

    def _edit_selected(self, task_id: str) -> None:
        task = self.task_service.get_task(task_id)
        if task:
            self._open_edit_task(task)

    def _delete_selected(self, task_id: str) -> None:
        if messagebox.askyesno(
            "Confirm Delete", "Soft delete this task?", parent=self
        ):
            self.task_service.soft_delete_task(task_id)
            self._refresh_tasks()

    def _open_create_task(self) -> None:
        TaskDialog(
            parent=self,
            categories=self.active_categories,
            on_save=self._save_new_task,
        )

    def _save_new_task(self, data: dict[str, Any]) -> None:
        self.task_service.create_task(
            title=data["title"],
            category_id=data["category_id"],
            critical_level=data["critical_level"],
            pace_level=data["pace_level"],
            due_date=data["due_date"],
            description=data["description"],
        )
        self._refresh_tasks()

    def _open_edit_task(self, task: Task) -> None:
        TaskDialog(
            parent=self,
            categories=self.active_categories,
            task=task,
            on_save=lambda data: self._save_edited_task(task.id, data),
        )

    def _save_edited_task(self, task_id: str, data: dict[str, Any]) -> None:
        self.task_service.update_task(
            task_id=task_id,
            title=data["title"],
            category_id=data["category_id"],
            critical_level=data["critical_level"],
            pace_level=data["pace_level"],
            due_date=data["due_date"],
            description=data["description"],
        )
        self._refresh_tasks()

    def _open_create_category(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add Category")
        dialog.geometry("320x160")
        dialog.configure(bg="#151922")
        dialog.transient(self)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg="#151922", padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Category Name:",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")

        name_entry = tk.Entry(
            frame,
            bg="#1e2433",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 10),
        )
        name_entry.pack(fill="x", pady=(4, 14), ipady=3)

        def _save() -> None:
            val = name_entry.get().strip()
            if not val:
                return
            try:
                self.category_service.create_category(val)
                self._refresh_categories()
                self._refresh_tasks()
                dialog.destroy()
            except Exception as err:
                messagebox.showerror("Error", str(err), parent=dialog)

        tk.Button(
            frame,
            text="Create",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=_save,
        ).pack(side="right")

    def _mark_all_notifications_read(self) -> None:
        self.notification_queue.mark_all_read()
        self._refresh_notifications()
        if self.on_notifications_cleared:
            self.on_notifications_cleared()

    def _clear_all_notifications(self) -> None:
        self.notification_queue.clear()
        self._refresh_notifications()
        if self.on_notifications_cleared:
            self.on_notifications_cleared()

    def show(self) -> None:
        self._refresh_categories()
        self._refresh_tasks()
        self._refresh_code()
        self._refresh_courses()
        self._refresh_ideas()
        self._refresh_opportunities()
        self._refresh_quick_links()
        self._refresh_notifications()
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide(self) -> None:
        self.withdraw()

    def toggle(self) -> None:
        if self.state() == "normal":
            self.hide()
        else:
            self.show()
