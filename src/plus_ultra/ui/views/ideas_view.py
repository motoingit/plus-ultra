"""Project Ideas and Concept Doubts workspace view component."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Any

from plus_ultra.models import IdeaDoubt
from plus_ultra.services import IdeaDoubtService
from plus_ultra.ui.components.scrollable import ScrollableFrame
from plus_ultra.ui.dialogs import IdeaDialog
from plus_ultra.ui.theme import THEME, CapsuleTheme


class IdeasView:
    """Card-based ideas and doubts workspace view with status lifecycles."""

    def __init__(
        self,
        container: tk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        idea_doubt_service: IdeaDoubtService | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        self.container = container
        self.parent_window = parent_window
        self.idea_doubt_service = idea_doubt_service
        self.theme = theme

        self.active_idea_filter: str = "All"
        self.idea_filter_btns: dict[str, tk.Button] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        head_bar = tk.Frame(self.container, bg="#161922", padx=24, pady=20)
        head_bar.pack(fill="x")

        tk.Label(
            head_bar,
            text="💡 Project Ideas & Concept Doubts",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 15, "bold"),
        ).pack(side="left")

        tk.Button(
            head_bar,
            text="+ Add Entry",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 10, "bold"),
            command=self.open_create_idea,
            cursor="hand2",
            padx=16,
            pady=6,
        ).pack(side="right")

        # Filters: All, Ideas, Doubts
        filter_bar = tk.Frame(self.container, bg="#161922", padx=24)
        filter_bar.pack(fill="x", pady=(0, 12))

        for kind in ["All", "Idea", "Doubt"]:
            label = (
                "All Entries"
                if kind == "All"
                else ("💡 Ideas" if kind == "Idea" else "❓ Doubts")
            )
            btn = tk.Button(
                filter_bar,
                text=label,
                bg="#1e2433" if kind == "All" else "#12151c",
                fg="#00e5ff" if kind == "All" else "#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 9, "bold"),
                cursor="hand2",
                padx=12,
                pady=5,
                command=lambda k=kind: self.set_idea_filter(k),
            )
            btn.pack(side="left", padx=2)
            self.idea_filter_btns[kind] = btn

        self.ideas_scroll = ScrollableFrame(self.container, bg="#161922")
        self.ideas_scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def set_idea_filter(self, kind: str) -> None:
        """Update active entry kind filter and reload cards."""
        self.active_idea_filter = kind
        for k, btn in self.idea_filter_btns.items():
            if k == kind:
                btn.configure(bg="#1e2433", fg="#00e5ff")
            else:
                btn.configure(bg="#12151c", fg="#94a3b8")
        self.refresh()

    def refresh(self) -> None:
        """Query ideas and doubts matching filter and render cards."""
        parent = self.ideas_scroll.interior
        for child in parent.winfo_children():
            child.destroy()

        if not self.idea_doubt_service:
            return

        kind = (
            None
            if self.active_idea_filter == "All"
            else self.active_idea_filter
        )
        items = self.idea_doubt_service.list_items(kind=kind)

        if not items:
            tk.Label(
                parent,
                text="No ideas or doubts recorded yet.",
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

            is_doubt = item.kind == "Doubt"
            icon = "❓" if is_doubt else "💡"
            tk.Label(
                top,
                text=f"{icon} {item.title}",
                bg="#1c212c",
                fg="#f8fafc",
                font=(self.theme.font_family, 12, "bold"),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            acts = tk.Frame(top, bg="#1c212c")
            acts.pack(side="right")

            # Status Cycle / Toggle Button
            status_bg = (
                "#064e3b"
                if item.status in ("Resolved", "Completed")
                else "#1e2433"
            )
            status_fg = (
                "#34d399"
                if item.status in ("Resolved", "Completed")
                else "#00e5ff"
            )
            tk.Button(
                acts,
                text=f"[{item.status}]",
                bg=status_bg,
                fg=status_fg,
                activebackground="#2b3448",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 9, "bold"),
                cursor="hand2",
                padx=10,
                pady=3,
                command=lambda iid=item.id: self.advance_idea(iid),
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
                command=lambda it=item: self.open_edit_idea(it),
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
                command=lambda iid=item.id: self.delete_idea(iid),
            ).pack(side="left", padx=3)

            if item.tech_stack_or_ref:
                tk.Label(
                    card,
                    text=f"Tags: {item.tech_stack_or_ref}",
                    bg="#083344",
                    fg="#22d3ee",
                    font=(self.theme.font_family, 8, "bold"),
                    padx=6,
                    pady=1,
                    anchor="w",
                ).pack(anchor="w", pady=(6, 2))

            if item.description:
                tk.Label(
                    card,
                    text=item.description,
                    bg="#1c212c",
                    fg="#94a3b8",
                    font=(self.theme.font_family, 10),
                    anchor="w",
                    justify="left",
                ).pack(fill="x", pady=(4, 0))

    def advance_idea(self, item_id: str) -> None:
        """Cycle idea status or toggle doubt open/resolved."""
        if self.idea_doubt_service:
            self.idea_doubt_service.advance_status(item_id)
            self.refresh()

    def delete_idea(self, item_id: str) -> None:
        """Prompt confirmation and soft-delete idea or doubt."""
        if (
            messagebox.askyesno(
                "Delete", "Delete this entry?", parent=self.parent_window
            )
            and self.idea_doubt_service
        ):
            self.idea_doubt_service.soft_delete_item(item_id)
            self.refresh()

    def open_create_idea(self) -> None:
        """Open IdeaDialog to create a new idea or doubt."""

        def _on_save(data: dict[str, Any]) -> None:
            if self.idea_doubt_service:
                self.idea_doubt_service.create_item(
                    kind=data["kind"],
                    title=data["title"],
                    description=data["description"],
                    tech_stack_or_ref=data["tech_stack_or_ref"],
                    status=data["status"],
                )
                self.refresh()

        IdeaDialog(self.parent_window, on_save=_on_save)

    def open_edit_idea(self, item: IdeaDoubt) -> None:
        """Open IdeaDialog to edit an existing idea or doubt."""

        def _on_save(data: dict[str, Any]) -> None:
            if self.idea_doubt_service:
                self.idea_doubt_service.update_idea_doubt(
                    item_id=item.id,
                    title=data["title"],
                    kind=data["kind"],
                    description=data["description"],
                    tech_stack_or_ref=data["tech_stack_or_ref"],
                    status=data["status"],
                )
                self.refresh()

        IdeaDialog(self.parent_window, item=item, on_save=_on_save)
