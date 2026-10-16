"""Dedicated DSA problem tracker workspace view component."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import messagebox
from typing import Any

from plus_ultra.models import CodeItem
from plus_ultra.services import CodeService
from plus_ultra.ui.components.scrollable import ScrollableFrame
from plus_ultra.ui.dialogs import CodeDialog
from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import THEME, CapsuleTheme


class DSAView:
    """Dedicated DSA problem tracker view with filters, metrics, and CRUD."""

    CATEGORY_NAME = "DSA Problem Tracker"

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

        self.active_filter: str = "All"
        self.filter_buttons: dict[str, tk.Button] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        head_bar = tk.Frame(self.container, bg="#161922", padx=28, pady=24)
        head_bar.pack(fill="x")

        icon = get_icon("fallback", 24)
        title_lbl = tk.Label(
            head_bar,
            text=" DSA Problem Tracker",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 16, "bold"),
            image=icon,
            compound="left",
        )
        title_lbl.image = icon  # type: ignore[attr-defined]
        title_lbl.pack(side="left")

        tk.Button(
            head_bar,
            text="+ Add Problem",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11, "bold"),
            command=self.open_create_problem,
            cursor="hand2",
            padx=18,
            pady=8,
        ).pack(side="right")

        # Filter Sub-Tabs: All, Easy, Medium, Hard, Solved, Todo
        filter_bar = tk.Frame(self.container, bg="#161922", padx=28)
        filter_bar.pack(fill="x", pady=(0, 16))

        for opt in ["All", "Easy", "Medium", "Hard", "Solved", "Todo"]:
            btn = tk.Button(
                filter_bar,
                text=opt,
                bg="#1e2433" if opt == "All" else "#12151c",
                fg="#00e5ff" if opt == "All" else "#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 10, "bold"),
                cursor="hand2",
                padx=14,
                pady=6,
                command=lambda o=opt: self.set_filter(o),
            )
            btn.pack(side="left", padx=3)
            self.filter_buttons[opt] = btn

        self.scroll_frame = ScrollableFrame(self.container, bg="#161922")
        self.scroll_frame.pack(fill="both", expand=True, padx=28, pady=(0, 20))

    def set_filter(self, opt: str) -> None:
        """Update active difficulty/status filter and reload cards."""
        self.active_filter = opt
        for name, btn in self.filter_buttons.items():
            if name == opt:
                btn.config(bg="#1e2433", fg="#00e5ff")
            else:
                btn.config(bg="#12151c", fg="#94a3b8")
        self.refresh()

    def _matches_filter(self, item: CodeItem) -> bool:
        diff = (item.difficulty or "").lower()
        f = self.active_filter
        if f == "All":
            return True
        if f in ("Easy", "Medium", "Hard"):
            return diff == f.lower()
        if f == "Solved":
            return bool(item.is_done)
        if f == "Todo":
            return not item.is_done
        return False

    def refresh(self) -> None:
        """Reload and render 2x DSA problem cards from code service."""
        for child in self.scroll_frame.interior.winfo_children():
            child.destroy()

        if not self.code_service:
            return

        all_items = self.code_service.list_items(category=self.CATEGORY_NAME)
        filtered = [it for it in all_items if self._matches_filter(it)]

        if not filtered:
            empty_box = tk.Frame(
                self.scroll_frame.interior, bg="#161922", pady=48
            )
            empty_box.pack(fill="both", expand=True)
            tk.Label(
                empty_box,
                text="No DSA problems found for the selected filter.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 12),
            ).pack()
            return

        for item in filtered:
            self._render_problem_card(item)

    def _render_problem_card(self, item: CodeItem) -> None:
        card = tk.Frame(
            self.scroll_frame.interior,
            bg="#1c212c",
            padx=24,
            pady=20,
            highlightbackground="#2b3448",
            highlightthickness=1,
        )
        card.pack(fill="x", pady=10)

        # Header row: Status badge + Title + Difficulty badge
        top_row = tk.Frame(card, bg="#1c212c")
        top_row.pack(fill="x", pady=(0, 10))

        status_text = "[Solved]" if item.is_done else "[Todo]"
        status_fg = "#10b981" if item.is_done else "#f59e0b"
        status_bg = "#0f291e" if item.is_done else "#2a2114"

        tk.Label(
            top_row,
            text=status_text,
            bg=status_bg,
            fg=status_fg,
            font=(self.theme.font_family, 10, "bold"),
            padx=8,
            pady=3,
        ).pack(side="left", padx=(0, 12))

        title_lbl = tk.Label(
            top_row,
            text=item.title,
            bg="#1c212c",
            fg="#f8fafc",
            font=(self.theme.font_family, 14, "bold"),
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        if item.difficulty:
            diff = item.difficulty.capitalize()
            diff_colors = {
                "Easy": ("#0f291e", "#10b981"),
                "Medium": ("#2a2114", "#f59e0b"),
                "Hard": ("#2a1215", "#ef4444"),
            }
            bg_col, fg_col = diff_colors.get(diff, ("#1e2433", "#00e5ff"))
            tk.Label(
                top_row,
                text=diff,
                bg=bg_col,
                fg=fg_col,
                font=(self.theme.font_family, 10, "bold"),
                padx=10,
                pady=3,
            ).pack(side="right")

        # Content / Notes
        if item.content:
            body = tk.Label(
                card,
                text=item.content,
                bg="#1c212c",
                fg="#cbd5e1",
                font=(self.theme.font_family, 11),
                wraplength=700,
                justify="left",
                anchor="w",
            )
            body.pack(fill="x", pady=(0, 10))

        # Action bar: Toggle Done, Open URL, Edit, Delete
        action_row = tk.Frame(card, bg="#1c212c")
        action_row.pack(fill="x", pady=(4, 0))

        done_btn_text = "Mark Todo" if item.is_done else "Mark Solved"
        done_btn_fg = "#94a3b8" if item.is_done else "#00e5ff"
        tk.Button(
            action_row,
            text=done_btn_text,
            bg="#242b3a",
            fg=done_btn_fg,
            activebackground="#2b3448",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10, "bold"),
            cursor="hand2",
            padx=14,
            pady=6,
            command=lambda i=item.id: self.toggle_dsa_done(i),
        ).pack(side="left", padx=(0, 10))

        if item.url:
            tk.Button(
                action_row,
                text="Open Problem Link",
                bg="#242b3a",
                fg="#38bdf8",
                activebackground="#2b3448",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 10),
                cursor="hand2",
                padx=12,
                pady=6,
                command=lambda u=item.url: webbrowser.open(u),
            ).pack(side="left", padx=(0, 10))

        tk.Button(
            action_row,
            text="Delete",
            bg="#242b3a",
            fg="#ef4444",
            activebackground="#3b1d24",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10),
            cursor="hand2",
            padx=12,
            pady=6,
            command=lambda i=item.id: self.delete_problem(i),
        ).pack(side="right")

        tk.Button(
            action_row,
            text="Edit",
            bg="#242b3a",
            fg="#cbd5e1",
            activebackground="#2b3448",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10),
            cursor="hand2",
            padx=12,
            pady=6,
            command=lambda it=item: self.open_edit_problem(it),
        ).pack(side="right", padx=(0, 8))

    def toggle_dsa_done(self, item_id: str) -> None:
        """Toggle problem solved state."""
        if not self.code_service:
            return
        self.code_service.toggle_done(item_id)
        self.refresh()

    def open_create_problem(self) -> None:
        """Launch modal dialog to register a new DSA problem."""
        if not self.code_service:
            return

        def _on_save(data: dict[str, Any]) -> None:
            self.code_service.create_item(
                category=self.CATEGORY_NAME,
                title=data["title"],
                content=data["content"],
                language=data["language"],
                difficulty=data["difficulty"],
                url=data["url"],
            )
            self.refresh()

        CodeDialog(
            self.parent_window,
            mode="create",
            on_save=_on_save,
            theme=self.theme,
        )

    def open_edit_problem(self, item: CodeItem) -> None:
        """Launch modal dialog to edit an existing DSA problem."""
        if not self.code_service:
            return

        def _on_save(data: dict[str, Any]) -> None:
            self.code_service.update_code_item(
                item_id=item.id,
                category=self.CATEGORY_NAME,
                title=data["title"],
                content=data["content"],
                language=data["language"],
                difficulty=data["difficulty"],
                url=data["url"],
            )
            self.refresh()

        CodeDialog(
            self.parent_window,
            item=item,
            mode="edit",
            on_save=_on_save,
            theme=self.theme,
        )

    def delete_problem(self, item_id: str) -> None:
        """Delete a DSA problem after confirmation."""
        if not self.code_service:
            return
        if messagebox.askyesno(
            "Confirm Delete",
            "Delete this DSA problem?",
            parent=self.parent_window,
        ):
            self.code_service.soft_delete_item(item_id)
            self.refresh()
