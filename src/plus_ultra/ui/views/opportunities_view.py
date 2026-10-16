"""Opportunities and Career pipeline workspace view component."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import messagebox
from typing import Any

from plus_ultra.models import Opportunity
from plus_ultra.services import OpportunityService
from plus_ultra.ui.components.scrollable import ScrollableFrame
from plus_ultra.ui.dialogs import OpportunityDialog
from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import THEME, CapsuleTheme


class OpportunitiesView:
    """Card-based opportunities workspace view with status lifecycles."""

    def __init__(
        self,
        container: tk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        opportunity_service: OpportunityService | None = None,
        theme: CapsuleTheme = THEME,
    ) -> None:
        self.container = container
        self.parent_window = parent_window
        self.opportunity_service = opportunity_service
        self.theme = theme

        self.active_opp_filter: str = "All"
        self.opp_filter_btns: dict[str, tk.Button] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        head_bar = tk.Frame(self.container, bg="#161922", padx=28, pady=24)
        head_bar.pack(fill="x")

        icon = get_icon("fallback", 24)
        title_lbl = tk.Label(
            head_bar,
            text=" Opportunities & Pipeline",
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
            text="+ Add Opportunity",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11, "bold"),
            command=self.open_create_opportunity,
            cursor="hand2",
            padx=18,
            pady=8,
        ).pack(side="right")

        filter_bar = tk.Frame(self.container, bg="#161922", padx=28)
        filter_bar.pack(fill="x", pady=(0, 16))

        for kind in [
            "All",
            "Internship",
            "Full-time",
            "Hackathon",
            "Fellowship",
        ]:
            btn = tk.Button(
                filter_bar,
                text=kind,
                bg="#1e2433" if kind == "All" else "#12151c",
                fg="#00e5ff" if kind == "All" else "#94a3b8",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 10, "bold"),
                cursor="hand2",
                padx=14,
                pady=6,
                command=lambda k=kind: self.set_opp_filter(k),
            )
            btn.pack(side="left", padx=3)
            self.opp_filter_btns[kind] = btn

        self.opps_scroll = ScrollableFrame(self.container, bg="#161922")
        self.opps_scroll.pack(fill="both", expand=True, padx=28, pady=(0, 20))

    def set_opp_filter(self, kind: str) -> None:
        """Update active opportunity type filter and reload cards."""
        self.active_opp_filter = kind
        for k, btn in self.opp_filter_btns.items():
            if k == kind:
                btn.configure(bg="#1e2433", fg="#00e5ff")
            else:
                btn.configure(bg="#12151c", fg="#94a3b8")
        self.refresh()

    def refresh(self) -> None:
        """Query opportunities matching filter and render interactive cards."""
        parent = self.opps_scroll.interior
        for child in parent.winfo_children():
            child.destroy()

        if not self.opportunity_service:
            return

        kind = (
            None if self.active_opp_filter == "All" else self.active_opp_filter
        )
        opps = self.opportunity_service.list_opportunities(kind=kind)

        if not opps:
            empty_frame = tk.Frame(parent, bg="#161922", pady=48)
            empty_frame.pack(fill="x")
            tk.Label(
                empty_frame,
                text="No opportunities saved in this filter.",
                bg="#161922",
                fg="#64748b",
                font=(self.theme.font_family, 12),
            ).pack()
            return

        for opp in opps:
            self._render_card(parent, opp)

    def _render_card(self, parent: tk.Widget, opp: Opportunity) -> None:
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
            text=f"{opp.title}  |  {opp.organization}",
            bg="#1c212c",
            fg="#f8fafc",
            font=(self.theme.font_family, 14, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        acts = tk.Frame(top, bg="#1c212c")
        acts.pack(side="right")

        st_colors = {
            "Saved": ("#1e2433", "#94a3b8"),
            "Applied": ("#1e2433", "#00e5ff"),
            "In Progress": ("#452a10", "#fbbf24"),
            "Accepted": ("#064e3b", "#34d399"),
            "Rejected": ("#451a1a", "#f87171"),
        }
        bg_s, fg_s = st_colors.get(opp.status, ("#1e2433", "#94a3b8"))
        tk.Button(
            acts,
            text=f"[{opp.status}]",
            bg=bg_s,
            fg=fg_s,
            activebackground="#2b3448",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 10, "bold"),
            cursor="hand2",
            padx=12,
            pady=5,
            command=lambda oid=opp.id: self.advance_opp(oid),
        ).pack(side="left", padx=4)

        if opp.url:
            tk.Button(
                acts,
                text="Apply Link",
                bg="#00e5ff",
                fg="#0a0e17",
                activebackground="#00b4d8",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 10, "bold"),
                cursor="hand2",
                padx=12,
                pady=5,
                command=lambda u=opp.url: webbrowser.open(u),
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
            command=lambda o=opp: self.open_edit_opportunity(o),
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
            command=lambda oid=opp.id: self.delete_opp(oid),
        ).pack(side="left", padx=4)

        meta_row = tk.Frame(card, bg="#1c212c")
        meta_row.pack(fill="x", pady=(10, 0))

        tk.Label(
            meta_row,
            text=f"[{opp.kind}]",
            bg="#083344",
            fg="#22d3ee",
            font=(self.theme.font_family, 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left", padx=(0, 6))

        if opp.deadline:
            tk.Label(
                meta_row,
                text=f"Deadline: {opp.deadline}",
                bg="#1e2433",
                fg="#fbbf24",
                font=(self.theme.font_family, 9, "bold"),
                padx=8,
                pady=2,
            ).pack(side="left", padx=4)

        if opp.notes:
            tk.Label(
                card,
                text=opp.notes,
                bg="#1c212c",
                fg="#cbd5e1",
                font=(self.theme.font_family, 11),
                anchor="w",
                justify="left",
            ).pack(fill="x", pady=(8, 0))

    def advance_opp(self, opp_id: str) -> None:
        """Advance opportunity status along its pipeline."""
        if self.opportunity_service:
            self.opportunity_service.advance_status(opp_id)
            self.refresh()

    def delete_opp(self, opp_id: str) -> None:
        """Prompt confirmation and soft-delete opportunity."""
        if (
            messagebox.askyesno(
                "Delete", "Delete this opportunity?", parent=self.parent_window
            )
            and self.opportunity_service
        ):
            self.opportunity_service.soft_delete_opportunity(opp_id)
            self.refresh()

    def open_create_opportunity(self) -> None:
        """Open OpportunityDialog to add a new opportunity."""

        def _on_save(data: dict[str, Any]) -> None:
            if self.opportunity_service:
                self.opportunity_service.create_opportunity(
                    title=data["title"],
                    organization=data["organization"],
                    kind=data["kind"],
                    status=data["status"],
                    deadline=data["deadline"],
                    url=data["url"],
                    notes=data["notes"],
                )
                self.refresh()

        OpportunityDialog(self.parent_window, on_save=_on_save)

    def open_edit_opportunity(self, opp: Opportunity) -> None:
        """Open OpportunityDialog to edit an existing opportunity."""

        def _on_save(data: dict[str, Any]) -> None:
            if self.opportunity_service:
                self.opportunity_service.update_opportunity(
                    opp_id=opp.id,
                    title=data["title"],
                    organization=data["organization"],
                    kind=data["kind"],
                    status=data["status"],
                    deadline=data["deadline"],
                    url=data["url"],
                    notes=data["notes"],
                )
                self.refresh()

        OpportunityDialog(self.parent_window, item=opp, on_save=_on_save)
