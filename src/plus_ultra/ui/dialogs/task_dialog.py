"""Modal dialog for creating or editing tasks with Date & Time options."""

from __future__ import annotations

import datetime
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra.models import Category, Task
from plus_ultra.ui.dialogs.base import center_modal
from plus_ultra.ui.theme import THEME, CapsuleTheme


class TaskDialog(tk.Toplevel):
    """Modal dialog for creating or editing tasks with Date & Time options."""

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
        self.geometry("560x580")
        self.minsize(500, 520)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_modal(self, parent)

    def _build_ui(self) -> None:
        self.configure(bg="#12151c")

        # 1. FIXED BOTTOM ACTION BAR (Guaranteed Visible)
        footer = tk.Frame(self, bg="#0d1117", padx=24, pady=16)
        footer.pack(side="bottom", fill="x")

        save_label = "✓ Update Task" if self.task else "✓ Create Task"
        save_btn = tk.Button(
            footer,
            text=save_label,
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 10, "bold"),
            command=self._handle_save,
            cursor="hand2",
            padx=18,
            pady=8,
        )
        save_btn.pack(side="right", padx=(10, 0))

        cancel_btn = tk.Button(
            footer,
            text="✕ Cancel",
            bg="#2b3448",
            fg="#e2e8f0",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 10),
            command=self.destroy,
            cursor="hand2",
            padx=14,
            pady=8,
        )
        cancel_btn.pack(side="right")

        # 2. MAIN FORM BODY
        body = tk.Frame(self, bg="#12151c", padx=24, pady=20)
        body.pack(side="top", fill="both", expand=True)

        tk.Label(
            body,
            text="Task Title *",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(anchor="w")

        self.title_entry = tk.Entry(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            insertbackground="#00e5ff",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.title_entry.pack(fill="x", pady=(4, 12), ipady=5)
        if self.task:
            self.title_entry.insert(0, self.task.title)

        # Row 1: Category & Priority
        r1 = tk.Frame(body, bg="#12151c")
        r1.pack(fill="x", pady=(0, 12))

        cat_box = tk.Frame(r1, bg="#12151c")
        cat_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            cat_box,
            text="Category",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        cat_names = [c.name for c in self.categories] or ["General"]
        self.cat_combo = ttk.Combobox(
            cat_box, values=cat_names, state="readonly"
        )
        cur_cat = "General"
        if self.task and self.task.category_id:
            for c in self.categories:
                if c.id == self.task.category_id:
                    cur_cat = c.name
                    break
        self.cat_combo.set(cur_cat)
        self.cat_combo.pack(fill="x", pady=(4, 0))

        prio_box = tk.Frame(r1, bg="#12151c")
        prio_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            prio_box,
            text="Priority",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.prio_combo = ttk.Combobox(
            prio_box, values=["High", "Medium", "Low"], state="readonly"
        )
        self.prio_combo.set(self.task.critical_level if self.task else "Medium")
        self.prio_combo.pack(fill="x", pady=(4, 0))

        # Row 2: Pace & Due Date
        r2 = tk.Frame(body, bg="#12151c")
        r2.pack(fill="x", pady=(0, 12))

        pace_box = tk.Frame(r2, bg="#12151c")
        pace_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            pace_box,
            text="Pace",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.pace_combo = ttk.Combobox(
            pace_box, values=["Short-term", "Long-term"], state="readonly"
        )
        self.pace_combo.set(self.task.pace_level if self.task else "Short-term")
        self.pace_combo.pack(fill="x", pady=(4, 0))

        due_box = tk.Frame(r2, bg="#12151c")
        due_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            due_box,
            text="Due Date (YYYY-MM-DD)",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.due_entry = tk.Entry(
            due_box,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.due_entry.pack(fill="x", pady=(4, 0), ipady=4)

        # Parse existing due date and time
        existing_date = ""
        existing_time = ""
        if self.task and self.task.due_date:
            parts = self.task.due_date.strip().split()
            existing_date = parts[0]
            if len(parts) > 1:
                existing_time = parts[1]
            self.due_entry.insert(0, existing_date)

        # Row 3: Due Time Option & Quick Presets
        r3 = tk.Frame(body, bg="#12151c")
        r3.pack(fill="x", pady=(0, 12))

        time_box = tk.Frame(r3, bg="#12151c")
        time_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            time_box,
            text="Due Time (HH:MM optional)",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.time_entry = tk.Entry(
            time_box,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.time_entry.pack(fill="x", pady=(4, 0), ipady=4)
        if existing_time:
            self.time_entry.insert(0, existing_time)

        quick_box = tk.Frame(r3, bg="#12151c")
        quick_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            quick_box,
            text="Quick Time Presets",
            bg="#12151c",
            fg="#64748b",
            font=(self.theme.font_family, 9),
        ).pack(anchor="w")
        preset_row = tk.Frame(quick_box, bg="#12151c")
        preset_row.pack(fill="x", pady=(4, 0))
        for p_label, p_time in [
            ("09:00", "09:00"),
            ("14:00", "14:00"),
            ("18:00", "18:00"),
            ("23:59", "23:59"),
        ]:
            tk.Button(
                preset_row,
                text=p_label,
                bg="#1c212c",
                fg="#94a3b8",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                padx=6,
                pady=2,
                command=lambda t=p_time: self._set_quick_time(t),
            ).pack(side="left", padx=2)

        # Row 4: Reminder Checkbox
        self.remind_var = tk.BooleanVar(value=True)
        rem_chk = tk.Checkbutton(
            body,
            text="⏰ Schedule desktop notification at Due Date/Time",
            variable=self.remind_var,
            bg="#12151c",
            fg="#f8fafc",
            selectcolor="#1c212c",
            activebackground="#12151c",
            activeforeground="#00e5ff",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 9),
        )
        rem_chk.pack(anchor="w", pady=(0, 10))

        # Row 5: Notes / Description
        tk.Label(
            body,
            text="Description / Notes",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.desc_text = tk.Text(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            height=4,
            font=(self.theme.font_family, 10),
        )
        self.desc_text.pack(fill="both", expand=True, pady=(4, 0))
        if self.task and self.task.description:
            self.desc_text.insert("1.0", self.task.description)

    def _set_quick_time(self, time_str: str) -> None:
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, time_str)
        # If date is empty, default to today
        if not self.due_entry.get().strip():
            today_str = datetime.date.today().isoformat()
            self.due_entry.insert(0, today_str)

    def _handle_save(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror(
                "Validation Error", "Task title cannot be empty.", parent=self
            )
            return

        cat_id = None
        chosen_cat = self.cat_combo.get()
        for c in self.categories:
            if c.name == chosen_cat:
                cat_id = c.id
                break

        due_date_val = self.due_entry.get().strip()
        due_time_val = self.time_entry.get().strip()
        full_due_str = due_date_val
        if due_date_val and due_time_val:
            full_due_str = f"{due_date_val} {due_time_val}"

        payload = {
            "title": title,
            "category_id": cat_id,
            "critical_level": self.prio_combo.get(),
            "pace_level": self.pace_combo.get(),
            "due_date": full_due_str,
            "schedule_reminder": self.remind_var.get(),
            "description": self.desc_text.get("1.0", "end-1c").strip(),
        }

        if self.on_save:
            self.on_save(payload)
        self.destroy()
