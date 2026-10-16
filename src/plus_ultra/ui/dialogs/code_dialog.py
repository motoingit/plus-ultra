"""Modal dialog for creating or editing code snippets and DSA problems."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra.models import CodeItem
from plus_ultra.ui.dialogs.base import center_modal
from plus_ultra.ui.theme import THEME, CapsuleTheme


class CodeDialog(tk.Toplevel):
    """Modal dialog for creating or editing code snippets and DSA problems."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        item: CodeItem | None = None,
        on_save: Callable[[dict[str, Any]], None] | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        super().__init__(parent)
        self.item = item
        self.on_save = on_save
        self.theme = theme

        self.title("Edit Code Item" if item else "Add Code Item")
        self.geometry("580x580")
        self.minsize(500, 500)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_modal(self, parent)

    def _build_ui(self) -> None:
        self.configure(bg="#12151c")

        footer = tk.Frame(self, bg="#0d1117", padx=24, pady=16)
        footer.pack(side="bottom", fill="x")

        save_label = "✓ Update Item" if self.item else "✓ Create Item"
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
            text="Title / Problem Name *",
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

        cat_box = tk.Frame(r1, bg="#12151c")
        cat_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            cat_box,
            text="Category",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.cat_combo = ttk.Combobox(
            cat_box,
            values=[
                "Snippets",
                "CLI Commands",
                "Syntax Reference",
                "DSA Problem Tracker",
            ],
            state="readonly",
        )
        self.cat_combo.set(self.item.category if self.item else "Snippets")
        self.cat_combo.pack(fill="x", pady=(4, 0))

        lang_box = tk.Frame(r1, bg="#12151c")
        lang_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            lang_box,
            text="Language / Tool",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.lang_entry = tk.Entry(
            lang_box,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.lang_entry.insert(0, self.item.language if self.item else "python")
        self.lang_entry.pack(fill="x", pady=(4, 0), ipady=4)

        r2 = tk.Frame(body, bg="#12151c")
        r2.pack(fill="x", pady=(0, 12))

        diff_box = tk.Frame(r2, bg="#12151c")
        diff_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            diff_box,
            text="Difficulty (DSA)",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.diff_combo = ttk.Combobox(
            diff_box, values=["Easy", "Medium", "Hard"], state="readonly"
        )
        self.diff_combo.set(self.item.difficulty if self.item else "Easy")
        self.diff_combo.pack(fill="x", pady=(4, 0))

        url_box = tk.Frame(r2, bg="#12151c")
        url_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(
            url_box,
            text="Problem / Reference URL (optional)",
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
            text="Code Snippet / Command Content",
            bg="#12151c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w")
        self.code_text = tk.Text(
            body,
            bg="#1c212c",
            fg="#f8fafc",
            relief="flat",
            font=("courier", 10),
            height=6,
        )
        self.code_text.pack(fill="both", expand=True, pady=(4, 0))
        if self.item and self.item.content:
            self.code_text.insert("1.0", self.item.content)

    def _handle_save(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror(
                "Validation Error", "Title cannot be empty.", parent=self
            )
            return

        payload = {
            "title": title,
            "category": self.cat_combo.get(),
            "language": self.lang_entry.get().strip() or "python",
            "difficulty": self.diff_combo.get(),
            "url": self.url_entry.get().strip(),
            "content": self.code_text.get("1.0", "end-1c").strip(),
        }
        if self.on_save:
            self.on_save(payload)
        self.destroy()
