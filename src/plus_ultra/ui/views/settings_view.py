"""Preferences and Diagnostics workspace view component."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox

from plus_ultra import config
from plus_ultra.database import get_connection, seed_demo_workspace_data
from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import THEME, CapsuleTheme


class SettingsView:
    """Preferences and Diagnostics view displaying status and maintenance."""

    def __init__(
        self,
        container: tk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        theme: CapsuleTheme = THEME,
        on_reseed: Callable[[], None] | None = None,
    ) -> None:
        self.container = container
        self.parent_window = parent_window
        self.theme = theme
        self.on_reseed = on_reseed

        self._build_ui()

    def _build_ui(self) -> None:
        head_bar = tk.Frame(self.container, bg="#161922", padx=28, pady=24)
        head_bar.pack(fill="x")

        icon = get_icon("fallback", 24)
        title_lbl = tk.Label(
            head_bar,
            text=" Preferences & Diagnostics",
            bg="#161922",
            fg="#f8fafc",
            font=(self.theme.font_family, 16, "bold"),
            image=icon,
            compound="left",
        )
        title_lbl.image = icon  # type: ignore[attr-defined]
        title_lbl.pack(side="left")

        content = tk.Frame(self.container, bg="#161922", padx=28)
        content.pack(fill="both", expand=True)

        card1 = tk.Frame(
            content,
            bg="#1c212c",
            padx=24,
            pady=20,
            highlightbackground="#2b3448",
            highlightthickness=1,
        )
        card1.pack(fill="x", pady=10)

        tk.Label(
            card1,
            text="Widget Behavior",
            bg="#1c212c",
            fg="#00e5ff",
            font=(self.theme.font_family, 13, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        self.topmost_var = tk.BooleanVar(value=True)
        topmost_chk = tk.Checkbutton(
            card1,
            text="Keep floating capsule always-on-top",
            variable=self.topmost_var,
            bg="#1c212c",
            fg="#f8fafc",
            selectcolor="#12151c",
            activebackground="#1c212c",
            activeforeground="#00e5ff",
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=self._toggle_topmost,
            font=(self.theme.font_family, 11),
        )
        topmost_chk.pack(anchor="w", pady=4)

        card2 = tk.Frame(
            content,
            bg="#1c212c",
            padx=24,
            pady=20,
            highlightbackground="#2b3448",
            highlightthickness=1,
        )
        card2.pack(fill="x", pady=10)

        tk.Label(
            card2,
            text="Local Database Status",
            bg="#1c212c",
            fg="#00e5ff",
            font=(self.theme.font_family, 13, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        db_path = str(config.get_db_path())
        tk.Label(
            card2,
            text=f"SQLite Store: {db_path}",
            bg="#1c212c",
            fg="#cbd5e1",
            font=("courier", 10),
            anchor="w",
        ).pack(fill="x", pady=3)

        tk.Label(
            card2,
            text="Engine: SQLite 3.12+ WAL Mode (Advisory single-instance)",
            bg="#1c212c",
            fg="#94a3b8",
            font=(self.theme.font_family, 10),
            anchor="w",
        ).pack(fill="x", pady=3)

        card3 = tk.Frame(
            content,
            bg="#1c212c",
            padx=24,
            pady=20,
            highlightbackground="#2b3448",
            highlightthickness=1,
        )
        card3.pack(fill="x", pady=10)

        tk.Label(
            card3,
            text="Developer / Maintenance Actions",
            bg="#1c212c",
            fg="#00e5ff",
            font=(self.theme.font_family, 13, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        tk.Button(
            card3,
            text="Reseed Demo Data",
            bg="#2b3448",
            fg="#f8fafc",
            activebackground="#3b475e",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11, "bold"),
            cursor="hand2",
            padx=18,
            pady=8,
            command=self.reseed_demo_data,
        ).pack(anchor="w")

    def _toggle_topmost(self) -> None:
        pass

    def refresh(self) -> None:
        """Refresh settings state."""
        pass

    def reseed_demo_data(self) -> None:
        """Trigger workspace demo data reseed and notify user."""
        conn = get_connection()
        try:
            seed_demo_workspace_data(conn)
            messagebox.showinfo(
                "Demo Data",
                "Successfully reseeded demo workspace data across all tabs!",
                parent=self.parent_window,
            )
            if self.on_reseed:
                self.on_reseed()
        except Exception as exc:
            messagebox.showerror(
                "Reseed Error",
                f"Failed to reseed workspace data: {exc}",
                parent=self.parent_window,
            )
