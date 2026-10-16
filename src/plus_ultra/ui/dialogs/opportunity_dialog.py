"""Modal dialog for creating or editing career opportunities."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra.models import Opportunity
from plus_ultra.ui.components.datetime_picker import DateTimePicker
from plus_ultra.ui.dialogs.base import center_modal
from plus_ultra.ui.theme import THEME, CapsuleTheme


class OpportunityDialog(tk.Toplevel):
    """Modal dialog for creating or editing career opportunities."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        item: Opportunity | None = None,
        on_save: Callable[[dict[str, Any]], None] | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        super().__init__(parent)
        self.item = item
        self.on_save = on_save
        self.theme = theme

        self.title("Edit Opportunity" if item else "Add Opportunity")
        self.geometry("640x640")
        self.minsize(560, 560)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_modal(self, parent)

    @property
    def dead_entry(self) -> tk.Entry:
        """Compatibility property for test assertions."""
        return self.datetime_picker.entry

    def _build_ui(self) -> None:
        self.configure(bg="#12151c")

        footer = tk.Frame(self, bg="#0d1117", padx=28, pady=18)
        footer.pack(side="bottom", fill="x")

        save_label = "Update Opportunity" if self.item else "Create Opportunity"
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

        body = tk.Frame(self, bg="#12151c", padx=24, pady=20)
        body.pack(side="top", fill="both", expand=True)

        tk.Label(
            body,
            text="Role / Program Title *",
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
        if self.item:
            self.title_entry.insert(0, self.item.title)

        tk.Label(
            body,
            text="Company / Organization *",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(anchor="w")
        self.org_entry = tk.Entry(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.org_entry.pack(fill="x", pady=(4, 12), ipady=5)
        if self.item:
            self.org_entry.insert(0, self.item.organization)

        r1 = tk.Frame(body, bg="#12151c")
        r1.pack(fill="x", pady=(0, 12))

        kind_box = tk.Frame(r1, bg="#12151c")
        kind_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            kind_box,
            text="Opportunity Type",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.kind_combo = ttk.Combobox(
            kind_box,
            values=[
                "Internship",
                "Full-time",
                "Hackathon",
                "Fellowship",
                "Research",
            ],
            state="readonly",
        )
        self.kind_combo.set(self.item.kind if self.item else "Internship")
        self.kind_combo.pack(fill="x", pady=(4, 0))

        status_box = tk.Frame(r1, bg="#12151c")
        status_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            status_box,
            text="Application Status",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.status_combo = ttk.Combobox(
            status_box,
            values=["Saved", "Applied", "In Progress", "Accepted", "Rejected"],
            state="readonly",
        )
        self.status_combo.set(self.item.status if self.item else "Saved")
        self.status_combo.pack(fill="x", pady=(4, 0))

        r2 = tk.Frame(body, bg="#12151c")
        r2.pack(fill="x", pady=(0, 12))

        dead_box = tk.Frame(r2, bg="#12151c")
        dead_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            dead_box,
            text="Deadline (Presets & 'Now')",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        init_dead = ""
        if self.item and self.item.deadline:
            init_dead = self.item.deadline
        self.datetime_picker = DateTimePicker(
            dead_box,
            initial_value=init_dead,
            include_time=False,
            theme=self.theme,
        )
        self.datetime_picker.pack(fill="x", pady=(4, 0))

        url_box = tk.Frame(r2, bg="#12151c")
        url_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            url_box,
            text="Application Link / Portal URL",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.url_entry = tk.Entry(
            url_box,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        if self.item and self.item.url:
            self.url_entry.insert(0, self.item.url)
        self.url_entry.pack(fill="x", pady=(4, 0), ipady=4)

        tk.Label(
            body,
            text="Notes / Requirements",
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
        if self.item and self.item.notes:
            self.notes_entry.insert(0, self.item.notes)
        self.notes_entry.pack(fill="x", pady=(4, 0), ipady=4)

    def _handle_save(self) -> None:
        title = self.title_entry.get().strip()
        org = self.org_entry.get().strip()
        if not title or not org:
            messagebox.showerror(
                "Validation Error",
                "Title and Organization are required.",
                parent=self,
            )
            return

        payload = {
            "title": title,
            "organization": org,
            "kind": self.kind_combo.get(),
            "status": self.status_combo.get(),
            "deadline": self.datetime_picker.get_value(),
            "url": self.url_entry.get().strip(),
            "notes": self.notes_entry.get().strip(),
        }
        if self.on_save:
            self.on_save(payload)
        self.destroy()
