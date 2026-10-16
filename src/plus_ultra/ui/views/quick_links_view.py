"""Quick Links and Launcher Shortcuts workspace view component."""

from __future__ import annotations

import os
import subprocess
import tkinter as tk
import webbrowser
from tkinter import messagebox
from typing import Any

from plus_ultra.models import QuickLink
from plus_ultra.services import QuickLinkService
from plus_ultra.ui.components.scrollable import ScrollableFrame
from plus_ultra.ui.dialogs import QuickLinkDialog
from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import THEME, CapsuleTheme


class QuickLinksView:
    """Card-based launcher shortcuts workspace view with click tracking."""

    def __init__(
        self,
        container: tk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        quick_link_service: QuickLinkService | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        self.container = container
        self.parent_window = parent_window
        self.quick_link_service = quick_link_service
        self.theme = theme

        self.active_link_filter: str = "All"
        self.link_filter_btns: dict[str, tk.Button] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        head_bar = tk.Frame(self.container, bg="#161922", padx=28, pady=24)
        head_bar.pack(fill="x")

        icon = get_icon("fallback", 24)
        title_lbl = tk.Label(
            head_bar,
            text=" Quick Links & Shortcuts",
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
            text="+ Add Quick Link",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11, "bold"),
            command=self.open_create_link,
            cursor="hand2",
            padx=18,
            pady=8,
        ).pack(side="right")

        filter_bar = tk.Frame(self.container, bg="#161922", padx=28)
        filter_bar.pack(fill="x", pady=(0, 16))

        for cat in ["All", "Web", "Local Folder", "Local File", "Tool"]:
            btn = tk.Button(
                filter_bar,
                text=cat,
                bg="#1e2433" if cat == "All" else "#12151c",
                fg="#00e5ff" if cat == "All" else "#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 10, "bold"),
                cursor="hand2",
                padx=14,
                pady=6,
                command=lambda c=cat: self.set_link_filter(c),
            )
            btn.pack(side="left", padx=3)
            self.link_filter_btns[cat] = btn

        self.links_scroll = ScrollableFrame(self.container, bg="#161922")
        self.links_scroll.pack(fill="both", expand=True, padx=28, pady=(0, 20))

    def set_link_filter(self, category: str) -> None:
        """Update active shortcut category filter and reload cards."""
        self.active_link_filter = category
        for c, btn in self.link_filter_btns.items():
            if c == category:
                btn.configure(bg="#1e2433", fg="#00e5ff")
            else:
                btn.configure(bg="#12151c", fg="#94a3b8")
        self.refresh()

    def refresh(self) -> None:
        """Query quick links matching category and render interactive cards."""
        parent = self.links_scroll.interior
        for child in parent.winfo_children():
            child.destroy()

        if not self.quick_link_service:
            return

        cat = (
            None
            if self.active_link_filter == "All"
            else self.active_link_filter
        )
        links = self.quick_link_service.list_links(category=cat)

        if not links:
            empty_frame = tk.Frame(parent, bg="#161922", pady=48)
            empty_frame.pack(fill="x")
            tk.Label(
                empty_frame,
                text="No quick links found in this category.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 12),
            ).pack()
            return

        for link in links:
            self._render_card(parent, link)

    def _render_card(self, parent: tk.Widget, link: QuickLink) -> None:
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

        tk.Label(
            top,
            text=f"[{link.category}]",
            bg="#083344",
            fg="#22d3ee",
            font=(self.theme.font_family, 10, "bold"),
            padx=8,
            pady=3,
        ).pack(side="left", padx=(0, 10))

        tk.Label(
            top,
            text=link.name,
            bg="#1c212c",
            fg="#f8fafc",
            font=(self.theme.font_family, 14, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        acts = tk.Frame(top, bg="#1c212c")
        acts.pack(side="right")

        tk.Label(
            acts,
            text=f"Clicks: {link.click_count}",
            bg="#1c212c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
        ).pack(side="left", padx=10)

        tk.Button(
            acts,
            text="Open",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10, "bold"),
            cursor="hand2",
            padx=14,
            pady=5,
            command=lambda lnk=link: self.launch_quick_link(lnk),
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
            command=lambda lnk=link: self.open_edit_link(lnk),
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
            command=lambda lid=link.id: self.delete_link(lid),
        ).pack(side="left", padx=4)

        tk.Label(
            card,
            text=link.target_uri,
            bg="#1c212c",
            fg="#94a3b8",
            font=("courier", 10),
            anchor="w",
        ).pack(fill="x", pady=(8, 0))

    def launch_quick_link(self, link: QuickLink) -> None:
        """Launch web link or open local file/folder via xdg-open."""
        uri = link.target_uri
        if uri.startswith(("http://", "https://")):
            webbrowser.open(uri)
        else:
            expanded = os.path.expanduser(uri)
            subprocess.Popen(["xdg-open", expanded])

        if self.quick_link_service:
            self.quick_link_service.record_click(link.id)
            self.refresh()

    def delete_link(self, link_id: str) -> None:
        """Prompt confirmation and soft-delete quick link."""
        if (
            messagebox.askyesno(
                "Delete", "Delete quick link?", parent=self.parent_window
            )
            and self.quick_link_service
        ):
            self.quick_link_service.soft_delete_link(link_id)
            self.refresh()

    def open_create_link(self) -> None:
        """Open QuickLinkDialog to add a new link."""

        def _on_save(data: dict[str, Any]) -> None:
            if self.quick_link_service:
                self.quick_link_service.create_link(
                    name=data["name"],
                    target_uri=data["target_uri"],
                    category=data["category"],
                )
                self.refresh()

        QuickLinkDialog(self.parent_window, on_save=_on_save)

    def open_edit_link(self, link: QuickLink) -> None:
        """Open QuickLinkDialog to edit an existing link."""

        def _on_save(data: dict[str, Any]) -> None:
            if self.quick_link_service:
                self.quick_link_service.update_quick_link(
                    link_id=link.id,
                    name=data["name"],
                    target_uri=data["target_uri"],
                    category=data["category"],
                )
                self.refresh()

        QuickLinkDialog(self.parent_window, link=link, on_save=_on_save)
