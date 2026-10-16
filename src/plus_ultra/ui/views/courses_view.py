"""Courses and Certifications workspace view component."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import messagebox
from typing import Any

from plus_ultra.models import Course
from plus_ultra.services import CourseService
from plus_ultra.ui.components.scrollable import ScrollableFrame
from plus_ultra.ui.dialogs import CourseDialog
from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import THEME, CapsuleTheme


class CoursesView:
    """Card-based courses workspace view with module progress tracking."""

    def __init__(
        self,
        container: tk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        course_service: CourseService | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        self.container = container
        self.parent_window = parent_window
        self.course_service = course_service
        self.theme = theme

        self.active_course_filter: str = "All"
        self.course_filter_btns: dict[str, tk.Button] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        head_bar = tk.Frame(self.container, bg="#161922", padx=28, pady=24)
        head_bar.pack(fill="x")

        icon = get_icon("fallback", 24)
        title_lbl = tk.Label(
            head_bar,
            text="Courses & Certifications",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 16, "bold"),
            image=icon,
            compound="left",
            padx=10,
        )
        title_lbl.image = icon  # type: ignore[attr-defined]
        title_lbl.pack(side="left")

        tk.Button(
            head_bar,
            text="+ Add Course",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11, "bold"),
            command=self.open_create_course,
            cursor="hand2",
            padx=20,
            pady=8,
        ).pack(side="right")

        # Platform Filter Pills
        filter_bar = tk.Frame(self.container, bg="#161922", padx=28)
        filter_bar.pack(fill="x", pady=(0, 16))

        for plat in [
            "All",
            "University",
            "YouTube",
            "Independent",
            "Book",
        ]:
            btn = tk.Button(
                filter_bar,
                text=plat,
                bg="#1e2433" if plat == "All" else "#12151c",
                fg="#00e5ff" if plat == "All" else "#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 11, "bold"),
                cursor="hand2",
                padx=16,
                pady=8,
                command=lambda p=plat: self.set_course_filter(p),
            )
            btn.pack(side="left", padx=4)
            self.course_filter_btns[plat] = btn

        self.courses_scroll = ScrollableFrame(self.container, bg="#161922")
        self.courses_scroll.pack(
            fill="both", expand=True, padx=28, pady=(0, 20)
        )

    def set_course_filter(self, platform: str) -> None:
        """Update active platform filter and reload cards."""
        self.active_course_filter = platform
        for p, btn in self.course_filter_btns.items():
            if p == platform:
                btn.configure(bg="#1e2433", fg="#00e5ff")
            else:
                btn.configure(bg="#12151c", fg="#94a3b8")
        self.refresh()

    def refresh(self) -> None:
        """Query courses matching platform and render interactive cards."""
        parent = self.courses_scroll.interior
        for child in parent.winfo_children():
            child.destroy()

        if not self.course_service:
            return

        plat = (
            None
            if self.active_course_filter == "All"
            else self.active_course_filter
        )
        courses = self.course_service.list_courses(platform=plat)

        if not courses:
            tk.Label(
                parent,
                text="No courses found in this category.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 11),
                pady=40,
            ).pack()
            return

        for c in courses:
            card = tk.Frame(parent, bg="#1c212c", padx=28, pady=20)
            card.pack(fill="x", pady=10)

            top = tk.Frame(card, bg="#1c212c")
            top.pack(fill="x")

            tk.Label(
                top,
                text=f"{c.title}",
                bg="#1c212c",
                fg="#f8fafc",
                font=(self.theme.font_family, 15, "bold"),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            acts = tk.Frame(top, bg="#1c212c")
            acts.pack(side="right")

            tk.Button(
                acts,
                text="+1 Module",
                bg="#00e5ff",
                fg="#0a0e17",
                activebackground="#00b4d8",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 11, "bold"),
                cursor="hand2",
                padx=12,
                pady=4,
                command=lambda cid=c.id: self.inc_course(cid),
            ).pack(side="left", padx=4)

            if c.url:
                tk.Button(
                    acts,
                    text="Open",
                    bg="#1e2433",
                    fg="#cbd5e1",
                    relief="flat",
                    bd=0,
                    font=(self.theme.font_family, 11),
                    cursor="hand2",
                    padx=12,
                    pady=4,
                    command=lambda u=c.url: webbrowser.open(u),
                ).pack(side="left", padx=4)

            tk.Button(
                acts,
                text="Edit",
                bg="#2b3448",
                fg="#e2e8f0",
                activebackground="#3b475e",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 11),
                cursor="hand2",
                padx=12,
                pady=4,
                command=lambda crs=c: self.open_edit_course(crs),
            ).pack(side="left", padx=4)

            tk.Button(
                acts,
                text="Delete",
                bg="#3f1d24",
                fg="#fca5a5",
                activebackground="#5c2630",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 11),
                cursor="hand2",
                padx=12,
                pady=4,
                command=lambda cid=c.id: self.delete_course(cid),
            ).pack(side="left", padx=4)

            # Platform Tag
            meta_box = tk.Frame(card, bg="#1c212c")
            meta_box.pack(fill="x", pady=(10, 0))

            tk.Label(
                meta_box,
                text=f"[{c.platform}]",
                bg="#083344",
                fg="#22d3ee",
                font=(self.theme.font_family, 11, "bold"),
                padx=10,
                pady=3,
            ).pack(side="left", padx=(0, 8))

            if c.instructor:
                tk.Label(
                    meta_box,
                    text=f"Instructor: {c.instructor}",
                    bg="#1c212c",
                    fg="#94a3b8",
                    font=(self.theme.font_family, 11),
                ).pack(side="left")

            # Progress Bar & Percentage
            pct = int((c.completed_modules / max(1, c.total_modules)) * 100)
            bar_text = (
                f"Modules: {c.completed_modules} / {c.total_modules} "
                f"({pct}% complete)"
            )
            tk.Label(
                card,
                text=bar_text,
                bg="#1c212c",
                fg="#94a3b8",
                font=(self.theme.font_family, 11),
                anchor="w",
            ).pack(fill="x", pady=(10, 4))

            prog_bg = tk.Frame(card, bg="#12151c", height=10)
            prog_bg.pack(fill="x", pady=(2, 8))
            fill_frame = tk.Frame(prog_bg, bg="#00e5ff", height=10)
            fill_frame.place(relx=0, rely=0, relwidth=min(1.0, pct / 100))

            if c.notes:
                tk.Label(
                    card,
                    text=f"Note: {c.notes}",
                    bg="#1c212c",
                    fg="#94a3b8",
                    font=(self.theme.font_family, 12),
                    anchor="w",
                ).pack(fill="x", pady=(4, 0))

    def inc_course(self, course_id: str) -> None:
        """Increment completed module count for course."""
        if self.course_service:
            self.course_service.increment_module(course_id)
            self.refresh()

    def delete_course(self, course_id: str) -> None:
        """Prompt confirmation and soft-delete course."""
        if (
            messagebox.askyesno(
                "Delete", "Delete this course?", parent=self.parent_window
            )
            and self.course_service
        ):
            self.course_service.soft_delete_course(course_id)
            self.refresh()

    def open_create_course(self) -> None:
        """Open CourseDialog to add a new course."""

        def _on_save(data: dict[str, Any]) -> None:
            if self.course_service:
                self.course_service.create_course(
                    title=data["title"],
                    platform=data["platform"],
                    instructor=data["instructor"],
                    total_modules=data["total_modules"],
                    completed_modules=data["completed_modules"],
                    url=data["url"],
                    notes=data["notes"],
                )
                self.refresh()

        CourseDialog(self.parent_window, on_save=_on_save)

    def open_edit_course(self, course: Course) -> None:
        """Open CourseDialog to edit an existing course."""

        def _on_save(data: dict[str, Any]) -> None:
            if self.course_service:
                self.course_service.update_course(
                    course_id=course.id,
                    title=data["title"],
                    platform=data["platform"],
                    instructor=data["instructor"],
                    total_modules=data["total_modules"],
                    completed_modules=data["completed_modules"],
                    url=data["url"],
                    notes=data["notes"],
                )
                self.refresh()

        CourseDialog(self.parent_window, course=course, on_save=_on_save)
