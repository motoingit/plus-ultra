"""Modal dialog for creating or editing academic/skill courses."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra.models import Course
from plus_ultra.ui.dialogs.base import center_modal
from plus_ultra.ui.theme import THEME, CapsuleTheme


class CourseDialog(tk.Toplevel):
    """Modal dialog for creating or editing academic/skill courses."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        course: Course | None = None,
        on_save: Callable[[dict[str, Any]], None] | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        super().__init__(parent)
        self.course = course
        self.on_save = on_save
        self.theme = theme

        self.title("Edit Course" if course else "Add Course")
        self.geometry("640x580")
        self.minsize(560, 520)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_modal(self, parent)

    def _build_ui(self) -> None:
        self.configure(bg="#12151c")

        footer = tk.Frame(self, bg="#0d1117", padx=28, pady=18)
        footer.pack(side="bottom", fill="x")

        save_label = "Update Course" if self.course else "Create Course"
        tk.Button(
            footer,
            text=save_label,
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 11, "bold"),
            command=self._handle_save,
            cursor="hand2",
            padx=20,
            pady=10,
        ).pack(side="right", padx=(10, 0))

        tk.Button(
            footer,
            text="Cancel",
            bg="#2b3448",
            fg="#e2e8f0",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 11),
            command=self.destroy,
            cursor="hand2",
            padx=16,
            pady=10,
        ).pack(side="right")

        body = tk.Frame(self, bg="#12151c", padx=28, pady=24)
        body.pack(side="top", fill="both", expand=True)

        tk.Label(
            body,
            text="Course Title *",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(anchor="w")
        self.title_entry = tk.Entry(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.title_entry.pack(fill="x", pady=(4, 12), ipady=5)
        if self.course:
            self.title_entry.insert(0, self.course.title)

        r1 = tk.Frame(body, bg="#12151c")
        r1.pack(fill="x", pady=(0, 12))

        plat_box = tk.Frame(r1, bg="#12151c")
        plat_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            plat_box,
            text="Platform",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.plat_combo = ttk.Combobox(
            plat_box,
            values=["University", "YouTube", "Other"],
            state="readonly",
        )
        self.plat_combo.set(
            self.course.platform if self.course else "University"
        )
        self.plat_combo.pack(fill="x", pady=(4, 0))

        inst_box = tk.Frame(r1, bg="#12151c")
        inst_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            inst_box,
            text="Instructor / Source",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.inst_entry = tk.Entry(
            inst_box,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        if self.course and self.course.instructor:
            self.inst_entry.insert(0, self.course.instructor)
        self.inst_entry.pack(fill="x", pady=(4, 0), ipady=4)

        r2 = tk.Frame(body, bg="#12151c")
        r2.pack(fill="x", pady=(0, 12))

        tot_box = tk.Frame(r2, bg="#12151c")
        tot_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            tot_box,
            text="Total Modules",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.tot_entry = tk.Entry(
            tot_box,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.tot_entry.insert(
            0, str(self.course.total_modules if self.course else 10)
        )
        self.tot_entry.pack(fill="x", pady=(4, 0), ipady=4)

        done_box = tk.Frame(r2, bg="#12151c")
        done_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            done_box,
            text="Completed Modules",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.done_entry = tk.Entry(
            done_box,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.done_entry.insert(
            0, str(self.course.completed_modules if self.course else 0)
        )
        self.done_entry.pack(fill="x", pady=(4, 0), ipady=4)

        tk.Label(
            body,
            text="Course / Lecture URL (optional)",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.url_entry = tk.Entry(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        if self.course and self.course.url:
            self.url_entry.insert(0, self.course.url)
        self.url_entry.pack(fill="x", pady=(4, 12), ipady=4)

        tk.Label(
            body,
            text="Notes / Topics",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.notes_entry = tk.Entry(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        if self.course and self.course.notes:
            self.notes_entry.insert(0, self.course.notes)
        self.notes_entry.pack(fill="x", pady=(4, 0), ipady=4)

    def _handle_save(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror(
                "Validation Error", "Course title cannot be empty.", parent=self
            )
            return

        try:
            tot = max(1, int(self.tot_entry.get().strip() or "10"))
        except ValueError:
            tot = 10

        try:
            done = max(0, min(tot, int(self.done_entry.get().strip() or "0")))
        except ValueError:
            done = 0

        payload = {
            "title": title,
            "platform": self.plat_combo.get(),
            "instructor": self.inst_entry.get().strip(),
            "total_modules": tot,
            "completed_modules": done,
            "url": self.url_entry.get().strip(),
            "notes": self.notes_entry.get().strip(),
        }
        if self.on_save:
            self.on_save(payload)
        self.destroy()
