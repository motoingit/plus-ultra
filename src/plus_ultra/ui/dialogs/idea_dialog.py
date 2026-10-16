"""Modal dialog for creating or editing ideas and concept doubts."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra.models import IdeaDoubt
from plus_ultra.ui.dialogs.base import center_modal
from plus_ultra.ui.theme import THEME, CapsuleTheme


class IdeaDialog(tk.Toplevel):
    """Modal dialog for creating or editing ideas and concept doubts."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        item: IdeaDoubt | None = None,
        on_save: Callable[[dict[str, Any]], None] | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        super().__init__(parent)
        self.item = item
        self.on_save = on_save
        self.theme = theme

        self.title("Edit Entry" if item else "Add Idea / Doubt")
        self.geometry("540x520")
        self.minsize(480, 480)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_modal(self, parent)

    def _build_ui(self) -> None:
        self.configure(bg="#12151c")

        footer = tk.Frame(self, bg="#0d1117", padx=24, pady=16)
        footer.pack(side="bottom", fill="x")

        save_label = "✓ Update Entry" if self.item else "✓ Create Entry"
        tk.Button(
            footer,
            text=save_label,
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10, "bold"),
            command=self._handle_save,
            cursor="hand2",
            padx=18,
            pady=8,
        ).pack(side="right", padx=(10, 0))

        tk.Button(
            footer,
            text="✕ Cancel",
            bg="#2b3448",
            fg="#e2e8f0",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10),
            command=self.destroy,
            cursor="hand2",
            padx=14,
            pady=8,
        ).pack(side="right")

        body = tk.Frame(self, bg="#12151c", padx=24, pady=20)
        body.pack(side="top", fill="both", expand=True)

        tk.Label(
            body,
            text="Title / Question *",
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

        r1 = tk.Frame(body, bg="#12151c")
        r1.pack(fill="x", pady=(0, 12))

        kind_box = tk.Frame(r1, bg="#12151c")
        kind_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            kind_box,
            text="Entry Kind",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.kind_combo = ttk.Combobox(
            kind_box, values=["Idea", "Doubt"], state="readonly"
        )
        self.kind_combo.set(self.item.kind if self.item else "Idea")
        self.kind_combo.pack(fill="x", pady=(4, 0))
        self.kind_combo.bind("<<ComboboxSelected>>", self._on_kind_change)

        status_box = tk.Frame(r1, bg="#12151c")
        status_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            status_box,
            text="Initial Status",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.status_combo = ttk.Combobox(status_box, state="readonly")
        self._update_status_options(self.kind_combo.get())
        if self.item:
            self.status_combo.set(self.item.status)
        self.status_combo.pack(fill="x", pady=(4, 0))

        tk.Label(
            body,
            text="Tech Stack / Topic Reference",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.tech_entry = tk.Entry(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        if self.item and self.item.tech_stack_or_ref:
            self.tech_entry.insert(0, self.item.tech_stack_or_ref)
        self.tech_entry.pack(fill="x", pady=(4, 12), ipady=4)

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
            height=5,
            font=(self.theme.font_family, 10),
        )
        if self.item and self.item.description:
            self.desc_text.insert("1.0", self.item.description)
        self.desc_text.pack(fill="both", expand=True, pady=(4, 0))

    def _on_kind_change(self, _event: tk.Event[Any]) -> None:
        self._update_status_options(self.kind_combo.get())

    def _update_status_options(self, kind: str) -> None:
        if kind == "Doubt":
            self.status_combo["values"] = ["Open", "Resolved"]
            self.status_combo.set("Open")
        else:
            self.status_combo["values"] = [
                "Idea",
                "Planned",
                "In Progress",
                "Completed",
            ]
            self.status_combo.set("Idea")

    def _handle_save(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror(
                "Validation Error", "Title cannot be empty.", parent=self
            )
            return

        payload = {
            "title": title,
            "kind": self.kind_combo.get(),
            "status": self.status_combo.get(),
            "tech_stack_or_ref": self.tech_entry.get().strip(),
            "description": self.desc_text.get("1.0", "end-1c").strip(),
        }
        if self.on_save:
            self.on_save(payload)
        self.destroy()
