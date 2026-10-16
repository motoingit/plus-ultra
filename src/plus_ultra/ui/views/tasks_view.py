"""Tasks and Deadlines workspace view component."""

from __future__ import annotations

import datetime
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra.models import Task
from plus_ultra.services import CategoryService, ReminderService, TaskService
from plus_ultra.ui.components.scrollable import ScrollableFrame
from plus_ultra.ui.dialogs import CategoryDialog, TaskDialog
from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import THEME, CapsuleTheme

logger = logging.getLogger(__name__)


class TasksView:
    """Card-based tasks workspace view with filtering, searching, and CRUD."""

    def __init__(
        self,
        container: tk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        task_service: TaskService,
        category_service: CategoryService,
        reminder_service: ReminderService | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        self.container = container
        self.parent_window = parent_window
        self.task_service = task_service
        self.category_service = category_service
        self.reminder_service = reminder_service
        self.theme = theme

        self.current_status_filter: str = "All"
        self.current_priority_filter: str = "All Priority"
        self.filtered_tasks: list[Task] = []
        self.status_buttons: dict[str, tk.Button] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        head_bar = tk.Frame(self.container, bg="#161922", padx=28, pady=24)
        head_bar.pack(fill="x")

        icon = get_icon("fallback", 24)
        title_lbl = tk.Label(
            head_bar,
            text=" Tasks",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 16, "bold"),
            image=icon,
            compound="left",
        )
        title_lbl.image = icon  # type: ignore[attr-defined]
        title_lbl.pack(side="left")

        tk.Button(
            head_bar,
            text="+ New Task",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11, "bold"),
            command=self.open_create_task,
            cursor="hand2",
            padx=18,
            pady=8,
        ).pack(side="right")

        # Filters Bar
        filter_bar = tk.Frame(self.container, bg="#161922", padx=28)
        filter_bar.pack(fill="x", pady=(0, 16))

        search_box = tk.Frame(filter_bar, bg="#161922")
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 16))
        tk.Label(
            search_box,
            text="Search:",
            bg="#161922",
            fg="#94a3b8",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(side="left", padx=(0, 6))
        self.search_entry = tk.Entry(
            search_box,
            bg="#12151c",
            fg="#f8fafc",
            relief="flat",
            insertbackground="#00e5ff",
            font=(self.theme.font_family, 11),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=5)
        self.search_entry.bind("<KeyRelease>", lambda _e: self.refresh())

        status_box = tk.Frame(filter_bar, bg="#161922")
        status_box.pack(side="right")
        for st in ["All", "Pending", "Completed"]:
            btn = tk.Button(
                status_box,
                text=st,
                bg="#1e2433" if st == "All" else "#12151c",
                fg="#00e5ff" if st == "All" else "#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 10, "bold"),
                cursor="hand2",
                padx=12,
                pady=5,
                command=lambda s=st: self.set_status_filter(s),
            )
            btn.pack(side="left", padx=3)
            self.status_buttons[st] = btn

        self.prio_filter_combo = ttk.Combobox(
            status_box,
            values=["All Priority", "High", "Medium", "Low"],
            width=13,
            state="readonly",
            font=(self.theme.font_family, 10),
        )
        self.prio_filter_combo.set("All Priority")
        self.prio_filter_combo.pack(side="left", padx=(8, 0))
        self.prio_filter_combo.bind(
            "<<ComboboxSelected>>", lambda _e: self._on_prio_filter_change()
        )

        # Scrollable Task Cards Frame
        self.tasks_scroll = ScrollableFrame(self.container, bg="#161922")
        self.tasks_scroll.pack(fill="both", expand=True, padx=28, pady=(0, 20))

    def set_status_filter(self, status: str) -> None:
        """Update active status filter button and reload cards."""
        self.current_status_filter = status
        for st, btn in self.status_buttons.items():
            if st == status:
                btn.configure(bg="#1e2433", fg="#00e5ff")
            else:
                btn.configure(bg="#12151c", fg="#94a3b8")
        self.refresh()

    def _on_prio_filter_change(self) -> None:
        self.current_priority_filter = self.prio_filter_combo.get()
        self.refresh()

    def refresh(self) -> None:
        """Query tasks matching filters and render interactive 2x cards."""
        parent = self.tasks_scroll.interior
        for child in parent.winfo_children():
            child.destroy()

        query = self.search_entry.get().strip() or None
        stat = (
            None
            if self.current_status_filter == "All"
            else self.current_status_filter
        )
        prio = (
            None
            if self.current_priority_filter == "All Priority"
            else self.current_priority_filter
        )

        tasks = self.task_service.list_tasks(
            status=stat, critical_level=prio, search_query=query
        )
        self.filtered_tasks = tasks

        if not tasks:
            empty_frame = tk.Frame(parent, bg="#161922", pady=48)
            empty_frame.pack(fill="x")
            tk.Label(
                empty_frame,
                text="No tasks match your filters.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 12),
            ).pack()
            return

        cat_map = {
            c.id: c.name for c in self.category_service.list_categories()
        }

        for task in tasks:
            self._render_task_card(parent, task, cat_map)

    def _render_task_card(
        self, parent: tk.Widget, task: Task, cat_map: dict[str, str]
    ) -> None:
        card = tk.Frame(
            parent,
            bg="#1c212c",
            padx=24,
            pady=18,
            highlightbackground="#2b3448",
            highlightthickness=1,
        )
        card.pack(fill="x", pady=8)

        top_row = tk.Frame(card, bg="#1c212c")
        top_row.pack(fill="x")

        is_done = task.status == "Completed"
        status_label = "[Done]" if is_done else "[Pending]"
        status_fg = "#10b981" if is_done else "#00e5ff"
        status_bg = "#0f291e" if is_done else "#162032"

        status_btn = tk.Button(
            top_row,
            text=status_label,
            bg=status_bg,
            fg=status_fg,
            activebackground=status_bg,
            activeforeground=status_fg,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 10, "bold"),
            cursor="hand2",
            padx=10,
            pady=4,
            command=lambda tid=task.id: self.toggle_selected_status(tid),
        )
        status_btn.pack(side="left", padx=(0, 12))

        title_fg = "#64748b" if is_done else "#f8fafc"
        tk.Label(
            top_row,
            text=task.title,
            bg="#1c212c",
            fg=title_fg,
            font=(self.theme.font_family, 14, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        act_box = tk.Frame(top_row, bg="#1c212c")
        act_box.pack(side="right")

        tk.Button(
            act_box,
            text="Edit",
            bg="#2b3448",
            fg="#e2e8f0",
            activebackground="#3b475e",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 10),
            cursor="hand2",
            padx=12,
            pady=5,
            command=lambda t=task: self.open_edit_task(t),
        ).pack(side="left", padx=4)

        tk.Button(
            act_box,
            text="Delete",
            bg="#3f1d24",
            fg="#fca5a5",
            activebackground="#5c2630",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 10),
            cursor="hand2",
            padx=12,
            pady=5,
            command=lambda tid=task.id: self.delete_task(tid),
        ).pack(side="left", padx=4)

        meta_row = tk.Frame(card, bg="#1c212c")
        meta_row.pack(fill="x", pady=(10, 0))

        cat_name = cat_map.get(task.category_id or "", "General")
        tk.Label(
            meta_row,
            text=f"[{cat_name}]",
            bg="#083344",
            fg="#22d3ee",
            font=(self.theme.font_family, 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left", padx=(0, 6))

        p_colors = {
            "High": ("#451a1a", "#f87171"),
            "Medium": ("#452a10", "#fbbf24"),
            "Low": ("#1e293b", "#94a3b8"),
        }
        bg_c, fg_c = p_colors.get(task.critical_level, ("#1e293b", "#94a3b8"))
        tk.Label(
            meta_row,
            text=f"[{task.critical_level}]",
            bg=bg_c,
            fg=fg_c,
            font=(self.theme.font_family, 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left", padx=4)

        if task.pace_level:
            tk.Label(
                meta_row,
                text=f"Pace: {task.pace_level}",
                bg="#1e2433",
                fg="#cbd5e1",
                font=(self.theme.font_family, 9),
                padx=8,
                pady=2,
            ).pack(side="left", padx=4)

        if task.due_date:
            due_text = f"Due: {task.due_date}"
            due_bg = "#1e2433"
            due_fg = "#cbd5e1"
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            due_cutoff = now_str[: len(task.due_date)]
            if not is_done and task.due_date < due_cutoff:
                due_text = f"Overdue: {task.due_date}"
                due_bg = "#451a1a"
                due_fg = "#f87171"

            tk.Label(
                meta_row,
                text=due_text,
                bg=due_bg,
                fg=due_fg,
                font=(self.theme.font_family, 9, "bold"),
                padx=8,
                pady=2,
            ).pack(side="left", padx=4)

        if task.description:
            tk.Label(
                card,
                text=task.description,
                bg="#1c212c",
                fg="#94a3b8",
                font=(self.theme.font_family, 11),
                anchor="w",
                justify="left",
            ).pack(fill="x", pady=(8, 0))

    def toggle_selected_status(self, task_id: str) -> None:
        """Toggle task status between Pending and Completed."""
        self.task_service.toggle_status(task_id)
        self.refresh()

    def delete_task(self, task_id: str) -> None:
        """Prompt confirmation and soft-delete a task."""
        if messagebox.askyesno(
            "Delete Task", "Delete this task?", parent=self.parent_window
        ):
            self.task_service.soft_delete_task(task_id)
            self.refresh()

    def open_create_task(self) -> None:
        """Open TaskDialog to add a new task."""
        cats = self.category_service.list_categories()

        def _on_save(data: dict[str, Any]) -> None:
            logger.info(
                "TasksView: Creating task '%s' [due=%s, schedule_reminder=%s]",
                data.get("title"),
                data.get("due_date"),
                data.get("schedule_reminder"),
            )
            new_task = self.task_service.create_task(
                title=data["title"],
                category_id=data["category_id"],
                critical_level=data["critical_level"],
                pace_level=data["pace_level"],
                due_date=data["due_date"],
                description=data["description"],
            )
            if (
                data.get("schedule_reminder")
                and data["due_date"]
                and self.reminder_service
            ):
                try:
                    rem = self.reminder_service.create_reminder(
                        new_task.id, data["due_date"]
                    )
                    logger.info(
                        "TasksView: Scheduled reminder %s for task %s at %s",
                        rem.id,
                        new_task.id,
                        data["due_date"],
                    )
                except Exception as exc:
                    logger.warning(
                        "TasksView: Failed to schedule reminder for %s: %s",
                        new_task.id,
                        exc,
                    )
            self.refresh()

        TaskDialog(
            self.parent_window,
            categories=cats,
            on_save=_on_save,
            category_service=self.category_service,
        )

    def open_edit_task(self, task: Task) -> None:
        """Open TaskDialog to edit an existing task."""
        cats = self.category_service.list_categories()

        def _on_save(data: dict[str, Any]) -> None:
            logger.info(
                "TasksView: Updating task %s '%s' [due=%s]",
                task.id,
                data.get("title"),
                data.get("due_date"),
            )
            self.task_service.update_task(
                task_id=task.id,
                title=data["title"],
                category_id=data["category_id"],
                critical_level=data["critical_level"],
                pace_level=data["pace_level"],
                due_date=data["due_date"],
                description=data["description"],
            )
            if (
                data.get("schedule_reminder")
                and data["due_date"]
                and self.reminder_service
            ):
                try:
                    rem = self.reminder_service.create_reminder(
                        task.id, data["due_date"]
                    )
                    logger.info(
                        "TasksView: Scheduled reminder %s for task %s at %s",
                        rem.id,
                        task.id,
                        data["due_date"],
                    )
                except Exception as exc:
                    logger.warning(
                        "TasksView: Failed to schedule reminder for %s: %s",
                        task.id,
                        exc,
                    )
            self.refresh()

        TaskDialog(
            self.parent_window,
            categories=cats,
            task=task,
            on_save=_on_save,
            category_service=self.category_service,
        )

    def open_create_category(self) -> None:
        """Open CategoryDialog to create a new category."""
        CategoryDialog(
            self.parent_window,
            category_service=self.category_service,
            on_success=self.refresh,
        )
