"""PS/I (Problem Solving, Project Ideas & Concept Doubts) workspace view."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Any

from plus_ultra.models import IdeaDoubt
from plus_ultra.services import IdeaDoubtService
from plus_ultra.ui.components.scrollable import ScrollableFrame
from plus_ultra.ui.dialogs import IdeaDialog
from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import THEME, CapsuleTheme


class IdeasView:
    """Sub-tabbed PS/I workspace view with status lifecycles."""

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

        self.active_subtab: str = "Idea"
        self._build_ui()

    @property
    def active_idea_filter(self) -> str:
        """Compatibility property for existing callers and tests."""
        return self.active_subtab

    def _build_ui(self) -> None:
        head_bar = tk.Frame(self.container, bg="#161922", padx=28, pady=24)
        head_bar.pack(fill="x")

        icon = get_icon("fallback", 24)
        title_lbl = tk.Label(
            head_bar,
            text=" PS/I",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 16, "bold"),
            image=icon,
            compound="left",
        )
        title_lbl.image = icon  # type: ignore[attr-defined]
        title_lbl.pack(side="left")

        self.add_btn = tk.Button(
            head_bar,
            text="+ Add Idea",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11, "bold"),
            command=self.open_create_entry,
            cursor="hand2",
            padx=18,
            pady=8,
        )
        self.add_btn.pack(side="right")

        # Two dedicated sub-tabs: [ Project Ideas ] and [ Concept Doubts ]
        tab_bar = tk.Frame(self.container, bg="#161922", padx=28)
        tab_bar.pack(fill="x", pady=(0, 16))

        self.btn_ideas_tab = tk.Button(
            tab_bar,
            text="Project Ideas",
            bg="#1e2433",
            fg="#00e5ff",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11, "bold"),
            cursor="hand2",
            padx=18,
            pady=7,
            command=lambda: self.switch_subtab("Idea"),
        )
        self.btn_ideas_tab.pack(side="left", padx=(0, 8))

        self.btn_doubts_tab = tk.Button(
            tab_bar,
            text="Concept Doubts",
            bg="#12151c",
            fg="#94a3b8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11, "bold"),
            cursor="hand2",
            padx=18,
            pady=7,
            command=lambda: self.switch_subtab("Doubt"),
        )
        self.btn_doubts_tab.pack(side="left")

        self.ideas_scroll = ScrollableFrame(self.container, bg="#161922")
        self.ideas_scroll.pack(fill="both", expand=True, padx=28, pady=(0, 20))

    def switch_subtab(self, kind: str) -> None:
        """Switch between Ideas and Doubts sub-tabs."""
        self.active_subtab = kind
        if kind == "Idea":
            self.btn_ideas_tab.configure(bg="#1e2433", fg="#00e5ff")
            self.btn_doubts_tab.configure(bg="#12151c", fg="#94a3b8")
            self.add_btn.configure(text="+ Add Idea")
        else:
            self.btn_doubts_tab.configure(bg="#1e2433", fg="#00e5ff")
            self.btn_ideas_tab.configure(bg="#12151c", fg="#94a3b8")
            self.add_btn.configure(text="+ Add Doubt")
        self.refresh()

    def set_idea_filter(self, kind: str) -> None:
        """Compatibility filter method."""
        target = "Doubt" if kind == "Doubt" else "Idea"
        self.switch_subtab(target)

    def refresh(self) -> None:
        """Query entries for active subtab and render cards."""
        parent = self.ideas_scroll.interior
        for child in parent.winfo_children():
            child.destroy()

        if not self.idea_doubt_service:
            return

        items = self.idea_doubt_service.list_items(kind=self.active_subtab)

        if not items:
            empty_msg = (
                "No project ideas recorded yet."
                if self.active_subtab == "Idea"
                else "No concept doubts recorded yet."
            )
            empty_frame = tk.Frame(parent, bg="#161922", pady=48)
            empty_frame.pack(fill="x")
            tk.Label(
                empty_frame,
                text=empty_msg,
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 12),
            ).pack()
            return

        for item in items:
            self._render_card(parent, item)

    def _render_card(self, parent: tk.Widget, item: IdeaDoubt) -> None:
        card = tk.Frame(
            parent,
            bg="#1c212c",
            padx=24,
            pady=18,
            highlightbackground="#2b3448",
            highlightthickness=1,
        )
        card.pack(fill="x", pady=8)

        top = tk.Frame(card, bg="#1c212c")
        top.pack(fill="x")

        kind_text = f"[{item.kind}]"
        kind_bg = "#083344" if item.kind == "Idea" else "#312e81"
        kind_fg = "#22d3ee" if item.kind == "Idea" else "#a5b4fc"

        tk.Label(
            top,
            text=kind_text,
            bg=kind_bg,
            fg=kind_fg,
            font=(self.theme.font_family, 10, "bold"),
            padx=8,
            pady=3,
        ).pack(side="left", padx=(0, 10))

        tk.Label(
            top,
            text=item.title,
            bg="#1c212c",
            fg="#f8fafc",
            font=(self.theme.font_family, 14, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        acts = tk.Frame(top, bg="#1c212c")
        acts.pack(side="right")

        # Status Cycle / Toggle Button
        status_bg = (
            "#064e3b" if item.status in ("Resolved", "Completed") else "#1e2433"
        )
        status_fg = (
            "#34d399" if item.status in ("Resolved", "Completed") else "#00e5ff"
        )
        tk.Button(
            acts,
            text=f"[{item.status}]",
            bg=status_bg,
            fg=status_fg,
            activebackground="#2b3448",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10, "bold"),
            cursor="hand2",
            padx=12,
            pady=5,
            command=lambda iid=item.id: self.advance_idea(iid),
        ).pack(side="left", padx=4)

        tk.Button(
            acts,
            text="Edit",
            bg="#2b3448",
            fg="#e2e8f0",
            activebackground="#3b475e",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10),
            cursor="hand2",
            padx=12,
            pady=5,
            command=lambda it=item: self.open_edit_idea(it),
        ).pack(side="left", padx=4)

        tk.Button(
            acts,
            text="Delete",
            bg="#3f1d24",
            fg="#fca5a5",
            activebackground="#5c2630",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10),
            cursor="hand2",
            padx=12,
            pady=5,
            command=lambda iid=item.id: self.delete_idea(iid),
        ).pack(side="left", padx=4)

        if item.tech_stack_or_ref:
            tk.Label(
                card,
                text=f"Reference: {item.tech_stack_or_ref}",
                bg="#1e2433",
                fg="#94a3b8",
                font=(self.theme.font_family, 9),
                padx=8,
                pady=2,
                anchor="w",
            ).pack(anchor="w", pady=(8, 2))

        if item.description:
            tk.Label(
                card,
                text=item.description,
                bg="#1c212c",
                fg="#cbd5e1",
                font=(self.theme.font_family, 11),
                anchor="w",
                justify="left",
            ).pack(fill="x", pady=(6, 0))

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

    def open_create_entry(self) -> None:
        """Open IdeaDialog to create a new idea or doubt for active subtab."""

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

        IdeaDialog(
            self.parent_window,
            default_kind=self.active_subtab,
            on_save=_on_save,
        )

    def open_create_idea(self) -> None:
        """Compatibility method."""
        self.open_create_entry()

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
