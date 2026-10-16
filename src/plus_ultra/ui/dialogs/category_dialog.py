"""Modal dialog for creating a new Category."""

from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Callable

from plus_ultra.services import CategoryService
from plus_ultra.ui.dialogs.base import center_modal
from plus_ultra.ui.theme import THEME, CapsuleTheme


class CategoryDialog(tk.Toplevel):
    """Modal dialog for creating new task categories."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        category_service: CategoryService,
        on_success: Callable[[], None] | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        super().__init__(parent)
        self.category_service = category_service
        self.on_success = on_success
        self.theme = theme

        self.title("Add Category")
        self.geometry("520x280")
        self.minsize(440, 240)
        self.configure(bg="#12151c")
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_modal(self, parent)

    def _build_ui(self) -> None:
        footer = tk.Frame(self, bg="#0d1117", padx=24, pady=16)
        footer.pack(side="bottom", fill="x")

        body = tk.Frame(self, bg="#12151c", padx=24, pady=20)
        body.pack(side="top", fill="both", expand=True)

        tk.Label(
            body,
            text="Category Name *",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 11, "bold"),
        ).pack(anchor="w")
        self.entry = tk.Entry(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 12),
        )
        self.entry.pack(fill="x", pady=(6, 0), ipady=6)

        tk.Button(
            footer,
            text="Save Category",
            bg="#00e5ff",
            fg="#0a0e17",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 11, "bold"),
            command=self._save,
            cursor="hand2",
            padx=18,
            pady=8,
        ).pack(side="right", padx=(8, 0))

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
            padx=14,
            pady=8,
        ).pack(side="right")

    def _save(self) -> None:
        name = self.entry.get().strip()
        if not name:
            return
        with contextlib.suppress(Exception):
            self.category_service.create_category(name)
        if self.on_success:
            self.on_success()
        self.destroy()
