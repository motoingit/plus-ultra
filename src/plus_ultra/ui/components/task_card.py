"""Task card item component for PLUS-ULTRA Tasks workspace view."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from plus_ultra.models import Task
from plus_ultra.ui.theme import THEME, CapsuleTheme


class TaskCard(tk.Frame):
    """Card widget rendering a single task with status toggle and actions."""

    def __init__(
        self,
        parent: tk.Widget,
        task: Task,
        category_name: str,
        theme: CapsuleTheme = THEME,
        on_toggle: Callable[[str], None] | None = None,
        on_edit: Callable[[Task], None] | None = None,
        on_delete: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(
            parent,
            bg="#1c212c",
            padx=24,
            pady=18,
            highlightbackground="#2b3448",
            highlightthickness=1,
        )
        self.task = task
        self.category_name = category_name
        self.theme = theme
        self.on_toggle = on_toggle
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.pack(fill="x", pady=8)
        self._build_card()

    def _build_card(self) -> None:
        """Render top row, meta row, and description."""
        top_row = tk.Frame(self, bg="#1c212c")
        top_row.pack(fill="x")

        is_done = self.task.status == "Completed"
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
            command=self._handle_toggle,
        )
        status_btn.pack(side="left", padx=(0, 12))

        title_fg = "#64748b" if is_done else "#f8fafc"
        tk.Label(
            top_row,
            text=self.task.title,
            bg="#1c212c",
            fg=title_fg,
            font=(self.theme.font_family, 14, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Action Buttons
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
            command=self._handle_edit,
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
            command=self._handle_delete,
        ).pack(side="left", padx=4)

        # Meta Row: Category, Priority, Pace, Due Date
        meta_row = tk.Frame(self, bg="#1c212c")
        meta_row.pack(fill="x", pady=(10, 0))

        tk.Label(
            meta_row,
            text=f"[{self.category_name}]",
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
        bg_c, fg_c = p_colors.get(
            self.task.critical_level, ("#1e293b", "#94a3b8")
        )
        tk.Label(
            meta_row,
            text=f"[{self.task.critical_level}]",
            bg=bg_c,
            fg=fg_c,
            font=(self.theme.font_family, 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left", padx=4)

        if self.task.pace_level:
            tk.Label(
                meta_row,
                text=f"Pace: {self.task.pace_level}",
                bg="#1e2433",
                fg="#cbd5e1",
                font=(self.theme.font_family, 9),
                padx=8,
                pady=2,
            ).pack(side="left", padx=4)

        if self.task.due_date:
            import datetime

            due_text = f"Due: {self.task.due_date}"
            due_bg = "#1e2433"
            due_fg = "#e0e7ff"
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            due_cutoff = now_str[: len(self.task.due_date)]
            if not is_done and self.task.due_date < due_cutoff:
                due_text = f"Overdue: {self.task.due_date}"
                due_bg = "#451a1a"
                due_fg = "#f87171"

            due_weight = "bold" if "Overdue" in due_text else "normal"
            tk.Label(
                meta_row,
                text=due_text,
                bg=due_bg,
                fg=due_fg,
                font=(self.theme.font_family, 9, due_weight),
                padx=8,
                pady=2,
            ).pack(side="left", padx=4)

        if self.task.is_google_task:
            tk.Label(
                meta_row,
                text="[Google Task]",
                bg="#172554",
                fg="#60a5fa",
                font=(self.theme.font_family, 9, "bold"),
                padx=8,
                pady=2,
            ).pack(side="left", padx=4)

        if self.task.description:
            tk.Label(
                self,
                text=self.task.description,
                bg="#1c212c",
                fg="#94a3b8",
                font=(self.theme.font_family, 10),
                anchor="w",
                justify="left",
                wraplength=700,
            ).pack(fill="x", pady=(10, 0))

    def _handle_toggle(self) -> None:
        if self.on_toggle:
            self.on_toggle(self.task.id)

    def _handle_edit(self) -> None:
        if self.on_edit:
            self.on_edit(self.task)

    def _handle_delete(self) -> None:
        if self.on_delete:
            self.on_delete(self.task.id)
