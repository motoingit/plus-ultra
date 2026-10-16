"""Modal dialog for creating or editing quick links and shortcuts."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra.models import QuickLink
from plus_ultra.ui.dialogs.base import center_modal
from plus_ultra.ui.theme import THEME, CapsuleTheme


class QuickLinkDialog(tk.Toplevel):
    """Modal dialog for creating or editing quick links and shortcuts."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        link: QuickLink | None = None,
        on_save: Callable[[dict[str, Any]], None] | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        super().__init__(parent)
        self.link = link
        self.on_save = on_save
        self.theme = theme

        self.title("Edit Shortcut" if link else "Add Quick Link")
        self.geometry("520x420")
        self.minsize(460, 380)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_modal(self, parent)

    def _build_ui(self) -> None:
        self.configure(bg="#12151c")

        footer = tk.Frame(self, bg="#0d1117", padx=24, pady=16)
        footer.pack(side="bottom", fill="x")

        save_label = "✓ Update Shortcut" if self.link else "✓ Create Shortcut"
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
            text="Display Name *",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(anchor="w")
        self.name_entry = tk.Entry(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.name_entry.pack(fill="x", pady=(4, 12), ipady=5)
        if self.link:
            self.name_entry.insert(0, self.link.name)

        tk.Label(
            body,
            text="Target URI (Web URL or Local Path) *",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10, "bold"),
        ).pack(anchor="w")
        self.uri_entry = tk.Entry(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.uri_entry.pack(fill="x", pady=(4, 12), ipady=5)
        if self.link:
            self.uri_entry.insert(0, self.link.target_uri)

        tk.Label(
            body,
            text="Category",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.cat_combo = ttk.Combobox(
            body,
            values=["Web", "Local Folder", "Local File", "Tool"],
            state="readonly",
        )
        self.cat_combo.set(self.link.category if self.link else "Web")
        self.cat_combo.pack(fill="x", pady=(4, 0))

    def _handle_save(self) -> None:
        name = self.name_entry.get().strip()
        uri = self.uri_entry.get().strip()
        if not name or not uri:
            messagebox.showerror(
                "Validation Error",
                "Display Name and Target URI are required.",
                parent=self,
            )
            return

        payload = {
            "name": name,
            "target_uri": uri,
            "category": self.cat_combo.get(),
        }
        if self.on_save:
            self.on_save(payload)
        self.destroy()
