"""Main dashboard workspace window for PLUS-ULTRA.

Applies architectural separation:
- MVC Architecture: UI layer interacts exclusively with services and models.
- Zero SQL/SQLite imports: all data operations go through TaskService
  and CategoryService.
- 3-Column Layout: Left Navigation Sidebar, Main Workspace Panel with
  Option A styled Treeview, and Right Notification Panel.
- Live two-way synchronization with floating capsule unread bell indicator.
"""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra.models import Category, Task
from plus_ultra.notifications import CapsuleNotificationQueue
from plus_ultra.services import CategoryService, TaskService
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
        """Center dialog relative to the parent dashboard window."""
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
        """Construct form fields with modern dark palette."""
        self.configure(bg="#151922")
        frame = tk.Frame(self, bg="#151922", padx=20, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        # Title
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

        # Category and Priority row
        row_frame = tk.Frame(frame, bg="#151922")
        row_frame.pack(fill="x", pady=(0, 10))

        # Category combobox
        cat_box = tk.Frame(row_frame, bg="#151922")
        cat_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            cat_box,
            text="Category",
            bg="#151922",
            fg="#94a3b8",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        self.cat_map: dict[str, str | None] = {"(None)": None}
        for c in self.categories:
            self.cat_map[c.name] = c.id
        cat_names = list(self.cat_map.keys())

        self.cat_combo = ttk.Combobox(
            cat_box, values=cat_names, state="readonly"
        )
        current_cat_name = "(None)"
        if self.task and self.task.category_id:
            for c in self.categories:
                if c.id == self.task.category_id:
                    current_cat_name = c.name
                    break
        self.cat_combo.set(current_cat_name)
        self.cat_combo.pack(fill="x", pady=(4, 0))

        # Priority combobox
        prio_box = tk.Frame(row_frame, bg="#151922")
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

        # Pace and Due date row
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

        # Description / Notes
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

        # Action Buttons
        btn_frame = tk.Frame(frame, bg="#151922")
        btn_frame.pack(fill="x")

        save_btn = tk.Button(
            btn_frame,
            text="Save Task",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
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
            font=(self.theme.font_family, 9),
            command=self.destroy,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        cancel_btn.pack(side="right")

    def _handle_save(self) -> None:
        """Validate input and fire save callback."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror(
                "Validation Error", "Task title cannot be empty.", parent=self
            )
            return

        cat_name = self.cat_combo.get()
        cat_id = self.cat_map.get(cat_name)
        critical = self.prio_combo.get()
        pace = self.pace_combo.get()
        due = self.due_entry.get().strip() or None
        desc = self.desc_text.get("1.0", "end-1c").strip()

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
        on_notifications_cleared: Callable[[], None] | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        super().__init__(parent)
        self.task_service = task_service
        self.category_service = category_service
        self.notification_queue = notification_queue
        self.on_notifications_cleared = on_notifications_cleared
        self.theme = theme

        self.title("PLUS-ULTRA Workspace")
        self.geometry("1020x640")
        self.minsize(860, 520)
        self.configure(bg="#11141c")

        self.active_tab: str = "Tasks"
        self.status_filter: str = "All"
        self.prio_filter: str = "All"
        self.category_filter_id: str | None = None

        self._setup_styles()
        self._build_layout()
        self._refresh_categories()
        self._refresh_tasks()
        self._refresh_notifications()

        # Intercept window manager close to hide rather than destroy
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self.withdraw()  # Start hidden until capsule click

    def _setup_styles(self) -> None:
        """Configure ttk dark styles for the Treeview and widgets."""
        style = ttk.Style(self)
        style.theme_use("clam")

        # Treeview styling
        style.configure(
            "Custom.Treeview",
            background="#1e2433",
            foreground="#f8fafc",
            fieldbackground="#1e2433",
            rowheight=30,
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
        """Construct the 3-column layout."""
        # 1. Column 1: Left Navigation Sidebar
        self.sidebar_col = tk.Frame(self, bg="#131720", width=180)
        self.sidebar_col.pack(side="left", fill="y")
        self.sidebar_col.pack_propagate(False)
        self._build_sidebar()

        # 2. Column 3: Right Notification Sidebar
        self.notif_col = tk.Frame(self, bg="#131720", width=220)
        self.notif_col.pack(side="right", fill="y")
        self.notif_col.pack_propagate(False)
        self._build_notification_panel()

        # 3. Column 2: Main Center Workspace Panel
        self.center_col = tk.Frame(self, bg="#181d28")
        self.center_col.pack(side="left", fill="both", expand=True)
        self._build_center_panel()

    def _build_sidebar(self) -> None:
        """Construct left workspace navigation sidebar."""
        # App brand header
        header = tk.Label(
            self.sidebar_col,
            text="⚡ PLUS-ULTRA",
            bg="#131720",
            fg="#00e5ff",
            font=(self.theme.font_family, 11, "bold"),
            pady=16,
        )
        header.pack(fill="x")

        # 6 Workspace Tabs
        self.tab_buttons: dict[str, tk.Button] = {}
        for tab_name, icon in WORKSPACE_TABS:
            btn = tk.Button(
                self.sidebar_col,
                text=f"  {icon}  {tab_name}",
                anchor="w",
                bg="#131720",
                fg="#94a3b8",
                activebackground="#1e2433",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=12,
                pady=8,
                font=(self.theme.font_family, 9),
                cursor="hand2",
                command=lambda name=tab_name: self._switch_tab(name),
            )
            btn.pack(fill="x", padx=6, pady=2)
            self.tab_buttons[tab_name] = btn

        self._highlight_active_tab()

        # Bottom-pinned Settings button
        settings_frame = tk.Frame(self.sidebar_col, bg="#131720")
        settings_frame.pack(side="bottom", fill="x", pady=12, padx=6)
        settings_btn = tk.Button(
            settings_frame,
            text="  ⚙️  Settings",
            anchor="w",
            bg="#131720",
            fg="#64748b",
            activebackground="#1e2433",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            font=(self.theme.font_family, 9),
            cursor="hand2",
            command=self._open_settings_info,
        )
        settings_btn.pack(fill="x")

    def _switch_tab(self, tab_name: str) -> None:
        """Switch active workspace tab."""
        self.active_tab = tab_name
        self._highlight_active_tab()
        if tab_name == "Tasks":
            self.tasks_container.pack(fill="both", expand=True)
            self.placeholder_container.pack_forget()
            self._refresh_tasks()
        else:
            self.tasks_container.pack_forget()
            self.placeholder_container.pack(fill="both", expand=True)
            self._render_placeholder_tab(tab_name)

    def _highlight_active_tab(self) -> None:
        """Update sidebar tab styling for active selection."""
        for name, btn in self.tab_buttons.items():
            if name == self.active_tab:
                btn.configure(
                    bg="#1e2433",
                    fg="#00e5ff",
                    font=(self.theme.font_family, 9, "bold"),
                )
            else:
                btn.configure(
                    bg="#131720", fg="#94a3b8", font=(self.theme.font_family, 9)
                )

    def _build_center_panel(self) -> None:
        """Construct the main workspace area (Tasks & Placeholders)."""
        # 1. Tasks Container
        self.tasks_container = tk.Frame(self.center_col, bg="#181d28")
        self.tasks_container.pack(fill="both", expand=True)

        # Header Bar
        head_bar = tk.Frame(
            self.tasks_container, bg="#181d28", padx=20, pady=16
        )
        head_bar.pack(fill="x")

        self.tasks_title_label = tk.Label(
            head_bar,
            text="Tasks & Deadlines",
            bg="#181d28",
            fg="#f8fafc",
            font=(self.theme.font_family, 13, "bold"),
        )
        self.tasks_title_label.pack(side="left")

        # Action Buttons
        new_task_btn = tk.Button(
            head_bar,
            text="+ New Task",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            font=(self.theme.font_family, 9, "bold"),
            command=self._open_create_task,
            cursor="hand2",
            padx=10,
            pady=4,
        )
        new_task_btn.pack(side="right", padx=(8, 0))

        new_cat_btn = tk.Button(
            head_bar,
            text="+ Category",
            bg="#2b3448",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 9),
            command=self._open_create_category,
            cursor="hand2",
            padx=8,
            pady=4,
        )
        new_cat_btn.pack(side="right")

        # Filter & Search Bar
        filter_bar = tk.Frame(self.tasks_container, bg="#181d28", padx=20)
        filter_bar.pack(fill="x", pady=(0, 10))

        # Search Entry
        search_box = tk.Frame(filter_bar, bg="#181d28")
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(search_box, text="🔍", bg="#181d28", fg="#64748b").pack(
            side="left", padx=(0, 4)
        )
        self.search_entry = tk.Entry(
            search_box,
            bg="#131720",
            fg="#f8fafc",
            relief="flat",
            insertbackground="#00e5ff",
            font=(self.theme.font_family, 9),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.search_entry.bind("<KeyRelease>", lambda _e: self._refresh_tasks())

        # Status filter buttons
        status_box = tk.Frame(filter_bar, bg="#181d28")
        status_box.pack(side="right")
        for st in ["All", "Pending", "Completed"]:
            btn = tk.Button(
                status_box,
                text=st,
                bg="#131720",
                fg="#94a3b8",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda s=st: self._set_status_filter(s),
            )
            btn.pack(side="left", padx=2)

        # Priority filter combobox
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

        # Option A: Styled Treeview Table
        table_frame = tk.Frame(self.tasks_container, bg="#181d28", padx=20)
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

        # Scrollbar for Treeview
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # Bindings: Double-click to edit, Right-click context menu
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Button-3>", self._on_tree_right_click)

        # 2. Placeholder Container for non-task tabs
        self.placeholder_container = tk.Frame(self.center_col, bg="#181d28")

    def _build_notification_panel(self) -> None:
        """Construct right sidebar Notification stream."""
        head = tk.Frame(self.notif_col, bg="#131720", padx=12, pady=16)
        head.pack(fill="x")

        tk.Label(
            head,
            text="🔔 Notifications",
            bg="#131720",
            fg="#f8fafc",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(side="left")

        actions_frame = tk.Frame(self.notif_col, bg="#131720", padx=12, pady=4)
        actions_frame.pack(fill="x")

        mark_all_btn = tk.Button(
            actions_frame,
            text="Mark All Read",
            bg="#1e2433",
            fg="#00e5ff",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 8),
            cursor="hand2",
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
            font=(self.theme.font_family, 8),
            cursor="hand2",
            command=self._clear_all_notifications,
        )
        clear_btn.pack(side="right")

        # Notification listbox / scroll area
        self.notif_listbox = tk.Listbox(
            self.notif_col,
            bg="#131720",
            fg="#e2e8f0",
            selectbackground="#1e2433",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 8),
        )
        self.notif_listbox.pack(fill="both", expand=True, padx=12, pady=8)

    # --- Task and Category Refresh Operations ---

    def _refresh_categories(self) -> None:
        """Reload active categories from CategoryService."""
        self.active_categories = self.category_service.list_active()

    def _refresh_tasks(self) -> None:
        """Query and populate the Treeview table based on current filters."""
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
        """Update right sidebar notification list."""
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
        """Update active status filter."""
        self.status_filter = status
        self._refresh_tasks()

    def _on_prio_filter_change(self) -> None:
        """Update priority filter."""
        val = self.prio_filter_combo.get()
        self.prio_filter = "All" if val == "All Priority" else val
        self._refresh_tasks()

    # --- Treeview Events & Context Menus ---

    def _on_tree_double_click(self, _event: tk.Event[Any]) -> None:
        """Open edit dialog for selected task on double click."""
        selected = self.tree.selection()
        if not selected:
            return
        task_id = selected[0]
        task = self.task_service.get_task(task_id)
        if task:
            self._open_edit_task(task)

    def _on_tree_right_click(self, event: tk.Event[Any]) -> None:
        """Display context menu on right click over a task row."""
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
        """Toggle task status."""
        self.task_service.toggle_status(task_id)
        self._refresh_tasks()

    def _edit_selected(self, task_id: str) -> None:
        """Open edit dialog for selected task."""
        task = self.task_service.get_task(task_id)
        if task:
            self._open_edit_task(task)

    def _delete_selected(self, task_id: str) -> None:
        """Soft delete selected task."""
        if messagebox.askyesno(
            "Confirm Delete", "Soft delete this task?", parent=self
        ):
            self.task_service.soft_delete_task(task_id)
            self._refresh_tasks()

    # --- Dialog Openers ---

    def _open_create_task(self) -> None:
        """Open dialog to create a new task."""
        TaskDialog(
            parent=self,
            categories=self.active_categories,
            on_save=self._save_new_task,
        )

    def _save_new_task(self, data: dict[str, Any]) -> None:
        """Save newly created task through TaskService."""
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
        """Open dialog to edit an existing task."""
        TaskDialog(
            parent=self,
            categories=self.active_categories,
            task=task,
            on_save=lambda data: self._save_edited_task(task.id, data),
        )

    def _save_edited_task(self, task_id: str, data: dict[str, Any]) -> None:
        """Persist updated task fields through TaskService."""
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
        """Simple dialog to add a new category."""
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
            command=_save,
        ).pack(side="right")

    # --- Notification Actions ---

    def _mark_all_notifications_read(self) -> None:
        """Mark all notifications as read and notify floating capsule."""
        self.notification_queue.mark_all_read()
        self._refresh_notifications()
        if self.on_notifications_cleared:
            self.on_notifications_cleared()

    def _clear_all_notifications(self) -> None:
        """Clear all notifications and notify floating capsule."""
        self.notification_queue.clear()
        self._refresh_notifications()
        if self.on_notifications_cleared:
            self.on_notifications_cleared()

    # --- Non-Task Placeholder Views ---

    def _render_placeholder_tab(self, tab_name: str) -> None:
        """Render planned sub-sections view for non-task tabs."""
        for child in self.placeholder_container.winfo_children():
            child.destroy()

        header = tk.Label(
            self.placeholder_container,
            text=f"{tab_name} Workspace",
            bg="#181d28",
            fg="#f8fafc",
            font=(self.theme.font_family, 14, "bold"),
            pady=24,
        )
        header.pack(fill="x")

        info_text = (
            f"The '{tab_name}' feature module is mapped in features.md.\n"
            "Full sub-section views and interactive management are active in "
            "the upcoming phase."
        )
        tk.Label(
            self.placeholder_container,
            text=info_text,
            bg="#181d28",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
            justify="center",
            pady=16,
        ).pack()

    def _open_settings_info(self) -> None:
        """Display settings summary dialog."""
        messagebox.showinfo(
            "Settings & Profile",
            "Preferences are managed atomically via user-settings.json.\n"
            "Machine state is tracked in SQLite app_state.",
            parent=self,
        )

    # --- Visibility Controls ---

    def show(self) -> None:
        """Display the dashboard window and refresh its content."""
        self._refresh_categories()
        self._refresh_tasks()
        self._refresh_notifications()
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide(self) -> None:
        """Hide window without destruction."""
        self.withdraw()

    def toggle(self) -> None:
        """Toggle dashboard visibility."""
        if self.state() == "normal":
            self.hide()
        else:
            self.show()
