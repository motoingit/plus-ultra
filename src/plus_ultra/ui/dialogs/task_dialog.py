"""Modal dialog for creating or editing tasks with interactive Date & Time."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra.models import Category, Task
from plus_ultra.services import CategoryService
from plus_ultra.ui.components.datetime_picker import DateTimePicker
from plus_ultra.ui.dialogs.base import center_modal
from plus_ultra.ui.dialogs.category_dialog import CategoryDialog
from plus_ultra.ui.theme import THEME, CapsuleTheme


class TaskDialog(tk.Toplevel):
    """Modal dialog for creating or editing tasks with interactive Date/Time."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        categories: list[Category],
        task: Task | None = None,
        on_save: Callable[[dict[str, Any]], None] | None = None,
        theme: CapsuleTheme = THEME,
        category_service: CategoryService | None = None,
    ) -> None:
        super().__init__(parent)
        self.task = task
        self.categories = list(categories)
        self.on_save = on_save
        self.theme = theme
        self.category_service = category_service

        self.title("Edit Task" if task else "Create New Task")
        self.geometry("680x720")
        self.minsize(600, 640)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_modal(self, parent)

    @property
    def due_entry(self) -> tk.Entry:
        """Compatibility property for test assertions."""
        return self.datetime_picker.entry

    @property
    def time_entry(self) -> tk.Entry:
        """Compatibility property for test assertions."""
        return self.datetime_picker.entry

    def _build_ui(self) -> None:
        self.configure(bg="#12151c")

        # 1. FIXED BOTTOM ACTION BAR
        footer = tk.Frame(self, bg="#0d1117", padx=28, pady=18)
        footer.pack(side="bottom", fill="x")

        save_label = "Update Task" if self.task else "Create Task"
        save_btn = tk.Button(
            footer,
            text=save_label,
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11, "bold"),
            command=self._handle_save,
            cursor="hand2",
            padx=20,
            pady=10,
        )
        save_btn.pack(side="right", padx=(10, 0))

        cancel_btn = tk.Button(
            footer,
            text="Cancel",
            bg="#2b3448",
            fg="#e2e8f0",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11),
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

        cat_input_row = tk.Frame(cat_box, bg="#12151c")
        cat_input_row.pack(fill="x", pady=(4, 0))

        self.cat_combo = ttk.Combobox(
            cat_input_row,
            values=self._get_cat_values(),
            state="readonly",
        )
        cur_cat = "General"
        if self.task and self.task.category_id:
            for c in self.categories:
                if c.id == self.task.category_id:
                    cur_cat = c.name
                    break
        self.cat_combo.set(cur_cat)
        self.cat_combo.pack(side="left", fill="x", expand=True)
        self.cat_combo.bind("<<ComboboxSelected>>", self._on_cat_selected)

        # Quick inline add category button
        add_cat_btn = tk.Button(
            cat_input_row,
            text="+",
            bg="#1e2433",
            fg="#00e5ff",
            activebackground="#2b3448",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10, "bold"),
            cursor="hand2",
            padx=8,
            pady=2,
            command=self._prompt_new_category,
        )
        add_cat_btn.pack(side="left", padx=(6, 0))

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

        # Row 2: Pace
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

        # Row 3: Interactive Date & Time Picker
        due_section = tk.Frame(body, bg="#12151c")
        due_section.pack(fill="x", pady=(0, 12))

        tk.Label(
            due_section,
            text="Due Date & Time (Interactive Presets & 'Now')",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")

        init_due = ""
        if self.task and self.task.due_date:
            init_due = self.task.due_date
        self.datetime_picker = DateTimePicker(
            due_section,
            initial_value=init_due,
            include_time=True,
            theme=self.theme,
        )
        self.datetime_picker.pack(fill="x", pady=(4, 0))

        # Row 4: Reminder Checkbox
        self.remind_var = tk.BooleanVar(value=True)
        rem_chk = tk.Checkbutton(
            body,
            text="Schedule desktop notification at Due Date/Time",
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

    def _get_cat_values(self) -> list[str]:
        names = [c.name for c in self.categories] or ["General"]
        return names + ["+ Add New Category..."]

    def _on_cat_selected(self, _event: tk.Event) -> None:
        if self.cat_combo.get() == "+ Add New Category...":
            self._prompt_new_category()

    def _prompt_new_category(self) -> None:
        if self.category_service:
            CategoryDialog(
                self,
                category_service=self.category_service,
                on_success=self._on_category_created,
                theme=self.theme,
            )
        else:
            messagebox.showinfo(
                "Category Service",
                "Category service unavailable.",
                parent=self,
            )

    def _on_category_created(self) -> None:
        if self.category_service:
            self.categories = self.category_service.list_categories()
            new_vals = self._get_cat_values()
            self.cat_combo.configure(values=new_vals)
            if self.categories:
                self.cat_combo.set(self.categories[-1].name)

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

        full_due_str = self.datetime_picker.get_value()

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
