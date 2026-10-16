"""Code and DSA tracking workspace view component."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from collections.abc import Callable
from tkinter import messagebox
from typing import Any

from plus_ultra.models import CodeItem
from plus_ultra.services import CodeService
from plus_ultra.ui.components.scrollable import ScrollableFrame
from plus_ultra.ui.dialogs import CodeDialog
from plus_ultra.ui.theme import THEME, CapsuleTheme


class CodeView:
    """Card-based code snippet and DSA workspace view with full CRUD."""

    def __init__(
        self,
        container: tk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        code_service: CodeService | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        self.container = container
        self.parent_window = parent_window
        self.code_service = code_service
        self.theme = theme

        self.active_code_filter: str = "All"
        self.code_filter_btns: dict[str, tk.Button] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        head_bar = tk.Frame(self.container, bg="#161922", padx=24, pady=20)
        head_bar.pack(fill="x")

        tk.Label(
            head_bar,
            text="💻 Code & DSA Workspace",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 15, "bold"),
        ).pack(side="left")

        tk.Button(
            head_bar,
            text="+ Add Code Item",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 10, "bold"),
            command=self.open_create_code,
            cursor="hand2",
            padx=16,
            pady=6,
        ).pack(side="right")

        # Filter Sub-Tabs
        filter_bar = tk.Frame(self.container, bg="#161922", padx=24)
        filter_bar.pack(fill="x", pady=(0, 12))

        for cat in [
            "All",
            "Snippets",
            "CLI Commands",
            "Syntax Reference",
            "DSA Problem Tracker",
        ]:
            btn = tk.Button(
                filter_bar,
                text=cat,
                bg="#1e2433" if cat == "All" else "#12151c",
                fg="#00e5ff" if cat == "All" else "#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 9, "bold"),
                cursor="hand2",
                padx=12,
                pady=5,
                command=lambda c=cat: self.set_code_filter(c),
            )
            btn.pack(side="left", padx=2)
            self.code_filter_btns[cat] = btn

        self.code_scroll = ScrollableFrame(self.container, bg="#161922")
        self.code_scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def set_code_filter(self, cat: str) -> None:
        """Update active code category filter and reload cards."""
        self.active_code_filter = cat
        for c, btn in self.code_filter_btns.items():
            if c == cat:
                btn.configure(bg="#1e2433", fg="#00e5ff")
            else:
                btn.configure(bg="#12151c", fg="#94a3b8")
        self.refresh()

    def refresh(self) -> None:
        """Query code items matching category and render interactive cards."""
        parent = self.code_scroll.interior
        for child in parent.winfo_children():
            child.destroy()

        if not self.code_service:
            return

        cat = (
            None
            if self.active_code_filter == "All"
            else self.active_code_filter
        )
        items = self.code_service.list_items(category=cat)

        if not items:
            tk.Label(
                parent,
                text="No code items found in this category.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 11),
                pady=40,
            ).pack()
            return

        for item in items:
            card = tk.Frame(parent, bg="#1c212c", padx=16, pady=12)
            card.pack(fill="x", pady=6)

            top = tk.Frame(card, bg="#1c212c")
            top.pack(fill="x")

            is_dsa = item.category == "DSA Problem Tracker"

            if is_dsa:
                dsa_btn_text = "✓ Solved" if item.is_done else "○ Todo"
                dsa_fg = "#10b981" if item.is_done else "#fbbf24"
                tk.Button(
                    top,
                    text=dsa_btn_text,
                    bg="#12151c",
                    fg=dsa_fg,
                    relief="flat",
                    bd=0,
                    font=(self.theme.font_family, 9, "bold"),
                    cursor="hand2",
                    padx=8,
                    pady=2,
                    command=lambda iid=item.id: self.toggle_dsa_done(iid),
                ).pack(side="left", padx=(0, 8))

            tk.Label(
                top,
                text=item.title,
                bg="#1c212c",
                fg="#f8fafc",
                font=(self.theme.font_family, 12, "bold"),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            # Action Buttons: Copy, Edit, Delete
            acts = tk.Frame(top, bg="#1c212c")
            acts.pack(side="right")

            if item.content:
                copy_btn = tk.Button(
                    acts,
                    text="📋 Copy",
                    bg="#2b3448",
                    fg="#00e5ff",
                    activebackground="#3b475e",
                    relief="flat",
                    bd=0,
                    font=(self.theme.font_family, 9, "bold"),
                    cursor="hand2",
                    padx=10,
                    pady=3,
                )
                copy_btn.configure(
                    command=self._make_copy_callback(item.content, copy_btn)
                )
                copy_btn.pack(side="left", padx=3)

            if item.url:
                tk.Button(
                    acts,
                    text="🔗 Open",
                    bg="#1e2433",
                    fg="#cbd5e1",
                    relief="flat",
                    bd=0,
                    font=(self.theme.font_family, 9),
                    cursor="hand2",
                    padx=8,
                    pady=3,
                    command=lambda u=item.url: webbrowser.open(u),
                ).pack(side="left", padx=3)

            tk.Button(
                acts,
                text="✏️ Edit",
                bg="#2b3448",
                fg="#e2e8f0",
                activebackground="#3b475e",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 9),
                cursor="hand2",
                padx=10,
                pady=3,
                command=lambda i=item: self.open_edit_code(i),
            ).pack(side="left", padx=3)

            tk.Button(
                acts,
                text="🗑️ Delete",
                bg="#3f1d24",
                fg="#fca5a5",
                activebackground="#5c2630",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 9),
                cursor="hand2",
                padx=10,
                pady=3,
                command=lambda iid=item.id: self.delete_code_item(iid),
            ).pack(side="left", padx=3)

            # Metadata Chips
            meta_box = tk.Frame(card, bg="#1c212c")
            meta_box.pack(fill="x", pady=(6, 0))

            tk.Label(
                meta_box,
                text=f"📁 {item.category}",
                bg="#083344",
                fg="#22d3ee",
                font=(self.theme.font_family, 8, "bold"),
                padx=6,
                pady=1,
            ).pack(side="left", padx=(0, 4))

            if item.language:
                tk.Label(
                    meta_box,
                    text=f"🛠️ {item.language}",
                    bg="#1e2433",
                    fg="#94a3b8",
                    font=(self.theme.font_family, 8),
                    padx=6,
                    pady=1,
                ).pack(side="left", padx=4)

            if is_dsa and item.difficulty:
                d_colors = {
                    "Easy": ("#064e3b", "#34d399"),
                    "Medium": ("#452a10", "#fbbf24"),
                    "Hard": ("#451a1a", "#f87171"),
                }
                bg_d, fg_d = d_colors.get(
                    item.difficulty, ("#1e2433", "#94a3b8")
                )
                tk.Label(
                    meta_box,
                    text=f"⚡ {item.difficulty}",
                    bg=bg_d,
                    fg=fg_d,
                    font=(self.theme.font_family, 8, "bold"),
                    padx=6,
                    pady=1,
                ).pack(side="left", padx=4)

            # Code Preview Block
            if item.content:
                code_box = tk.Frame(card, bg="#12151c", padx=10, pady=8)
                code_box.pack(fill="x", pady=(6, 0))
                display_code = item.content
                if len(display_code.splitlines()) > 5:
                    lines = display_code.splitlines()[:5]
                    display_code = "\n".join(lines) + "\n... [truncated]"
                tk.Label(
                    code_box,
                    text=display_code,
                    bg="#12151c",
                    fg="#cbd5e1",
                    font=("courier", 9),
                    anchor="w",
                    justify="left",
                ).pack(fill="x")

    def _make_copy_callback(
        self, text: str, btn: tk.Button
    ) -> Callable[[], None]:
        return lambda: self.copy_to_clipboard(text, btn)

    def copy_to_clipboard(self, text: str, btn: tk.Button) -> None:
        """Copy snippet text to OS clipboard and display transient feedback."""
        self.parent_window.clipboard_clear()
        self.parent_window.clipboard_append(text)
        orig_text = btn.cget("text")
        btn.configure(text="✓ Copied!", fg="#10b981")
        self.parent_window.after(
            1500, lambda: btn.configure(text=orig_text, fg="#00e5ff")
        )

    def toggle_dsa_done(self, item_id: str) -> None:
        """Toggle DSA problem solved status."""
        if self.code_service:
            self.code_service.toggle_done(item_id)
            self.refresh()

    def delete_code_item(self, item_id: str) -> None:
        """Prompt confirmation and soft-delete code item."""
        if (
            messagebox.askyesno(
                "Delete", "Delete this code item?", parent=self.parent_window
            )
            and self.code_service
        ):
            self.code_service.soft_delete_item(item_id)
            self.refresh()

    def open_create_code(self) -> None:
        """Open CodeDialog to add a new code snippet or DSA item."""

        def _on_save(data: dict[str, Any]) -> None:
            if self.code_service:
                self.code_service.create_item(
                    category=data["category"],
                    title=data["title"],
                    content=data["content"],
                    language=data["language"],
                    difficulty=data["difficulty"],
                    url=data["url"],
                )
                self.refresh()

        CodeDialog(self.parent_window, on_save=_on_save)

    def open_edit_code(self, item: CodeItem) -> None:
        """Open CodeDialog to edit an existing code item."""

        def _on_save(data: dict[str, Any]) -> None:
            if self.code_service:
                self.code_service.update_code_item(
                    item_id=item.id,
                    category=data["category"],
                    title=data["title"],
                    content=data["content"],
                    language=data["language"],
                    difficulty=data["difficulty"],
                    url=data["url"],
                )
                self.refresh()

        CodeDialog(self.parent_window, item=item, on_save=_on_save)
