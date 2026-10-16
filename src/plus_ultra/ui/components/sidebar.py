"""Sidebar navigation component for PLUS-ULTRA workspace panel."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from plus_ultra.ui.theme import THEME, CapsuleTheme


class Sidebar:
    """Left navigation sidebar coordinating workspace tabs and brand."""

    def __init__(
        self,
        container: tk.Widget,
        theme: CapsuleTheme = THEME,
        on_switch_tab: Callable[[str], None] | None = None,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        self.container = container
        self.theme = theme
        self.on_switch_tab = on_switch_tab
        self.on_close = on_close
        self.tab_buttons: dict[str, tk.Button] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        # App brand header
        brand_frame = tk.Frame(self.container, bg="#12151c", padx=20, pady=24)
        brand_frame.pack(fill="x")

        tk.Label(
            brand_frame,
            text="⚡ PLUS-ULTRA",
            bg="#12151c",
            fg="#00e5ff",
            font=(self.theme.font_family, 14, "bold"),
        ).pack(anchor="w")

        tk.Label(
            brand_frame,
            text="B.Tech Computer Science Workspace",
            bg="#12151c",
            fg="#64748b",
            font=(self.theme.font_family, 8),
        ).pack(anchor="w", pady=(2, 0))

        # Nav items
        nav_items = [
            ("Tasks", "📌 Tasks & Deadlines"),
            ("Code", "💻 Code & DSA Tracker"),
            ("Courses", "🎓 Courses & NPTEL"),
            ("Ideas-Doubt", "💡 Ideas & Doubts"),
            ("Opportunities", "🚀 Career & Internships"),
            ("Quick Links", "⚡ Quick Launchers"),
        ]

        nav_frame = tk.Frame(self.container, bg="#12151c", padx=12, pady=10)
        nav_frame.pack(fill="both", expand=True)

        for tab_id, tab_label in nav_items:
            btn = tk.Button(
                nav_frame,
                text=tab_label,
                anchor="w",
                bg="#12151c",
                fg="#94a3b8",
                activebackground="#1e2433",
                activeforeground="#00e5ff",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(self.theme.font_family, 10),
                cursor="hand2",
                padx=16,
                pady=10,
                command=lambda tid=tab_id: self._on_tab_click(tid),
            )
            btn.pack(fill="x", pady=2)
            self.tab_buttons[tab_id] = btn

        # Bottom section: Settings and Close
        bottom_frame = tk.Frame(self.container, bg="#12151c", padx=12, pady=16)
        bottom_frame.pack(side="bottom", fill="x")

        self.settings_btn = tk.Button(
            bottom_frame,
            text="⚙️ Preferences & Info",
            anchor="w",
            bg="#12151c",
            fg="#94a3b8",
            activebackground="#1e2433",
            activeforeground="#00e5ff",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 10),
            cursor="hand2",
            padx=16,
            pady=8,
            command=lambda: self._on_tab_click("Settings"),
        )
        self.settings_btn.pack(fill="x", pady=(0, 4))

        tk.Button(
            bottom_frame,
            text="✕ Close Panel",
            anchor="w",
            bg="#12151c",
            fg="#ef4444",
            activebackground="#2b3448",
            activeforeground="#ff4d4d",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 10, "bold"),
            cursor="hand2",
            padx=16,
            pady=8,
            command=self._on_close_click,
        ).pack(fill="x")

    def _on_tab_click(self, tab_id: str) -> None:
        if self.on_switch_tab:
            self.on_switch_tab(tab_id)

    def _on_close_click(self) -> None:
        if self.on_close:
            self.on_close()

    def highlight_tab(self, active_tab: str) -> None:
        """Update active button styling across navigation items."""
        for name, btn in self.tab_buttons.items():
            if name == active_tab:
                btn.configure(
                    bg="#1e2433",
                    fg="#00e5ff",
                    font=(self.theme.font_family, 10, "bold"),
                )
            else:
                btn.configure(
                    bg="#12151c",
                    fg="#94a3b8",
                    font=(self.theme.font_family, 10),
                )
        if hasattr(self, "settings_btn"):
            if active_tab == "Settings":
                self.settings_btn.configure(
                    bg="#1e2433",
                    fg="#00e5ff",
                    font=(self.theme.font_family, 10, "bold"),
                )
            else:
                self.settings_btn.configure(
                    bg="#12151c",
                    fg="#94a3b8",
                    font=(self.theme.font_family, 10),
                )
