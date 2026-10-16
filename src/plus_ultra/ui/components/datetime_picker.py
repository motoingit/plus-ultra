"""Interactive reusable Date and Time picker component for PLUS-ULTRA."""

from __future__ import annotations

import contextlib
import datetime
import tkinter as tk
from collections.abc import Callable

from plus_ultra.ui.theme import THEME, CapsuleTheme


class DateTimePicker(tk.Frame):
    """Interactive date and time selector with presets and quick actions."""

    def __init__(
        self,
        parent: tk.Widget,
        initial_value: str = "",
        include_time: bool = True,
        theme: CapsuleTheme = THEME,
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent, bg="#12151c")
        self.include_time = include_time
        self.theme = theme
        self.on_change = on_change

        self._build_ui()
        if initial_value:
            self.set_value(initial_value)

    def _build_ui(self) -> None:
        # 1. Main Display / Entry field with "Now" button
        entry_row = tk.Frame(self, bg="#12151c")
        entry_row.pack(fill="x")

        self.entry = tk.Entry(
            entry_row,
            bg="#1c212c",
            fg="#f8fafc",
            insertbackground="#00e5ff",
            relief="flat",
            font=(self.theme.font_family, 11),
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)

        now_btn = tk.Button(
            entry_row,
            text="⚡ Now",
            bg="#00e5ff",
            fg="#0a0e17",
            activebackground="#00b4d8",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 9, "bold"),
            cursor="hand2",
            padx=8,
            pady=3,
            command=self.set_now,
        )
        now_btn.pack(side="left", padx=(6, 0))

        # 2. Date Quick Presets: [Today] [Tomorrow] [+3 Days] [+1 Wk]
        preset_row = tk.Frame(self, bg="#12151c")
        preset_row.pack(fill="x", pady=(6, 0))

        date_presets = [
            ("Today", 0),
            ("Tomorrow", 1),
            ("+3 Days", 3),
            ("+1 Wk", 7),
        ]
        for label, days_offset in date_presets:
            tk.Button(
                preset_row,
                text=label,
                bg="#1c212c",
                fg="#94a3b8",
                activebackground="#2b3448",
                activeforeground="#00e5ff",
                relief="flat",
                bd=0,
                font=(self.theme.font_family, 8),
                cursor="hand2",
                padx=6,
                pady=2,
                command=lambda d=days_offset: self.add_days_from_today(d),
            ).pack(side="left", padx=(0, 4))

        # Stepper buttons: [-1d] [+1d]
        tk.Button(
            preset_row,
            text="-1d",
            bg="#161922",
            fg="#64748b",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 8),
            cursor="hand2",
            padx=5,
            pady=2,
            command=lambda: self.step_days(-1),
        ).pack(side="left", padx=(4, 2))
        tk.Button(
            preset_row,
            text="+1d",
            bg="#161922",
            fg="#64748b",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 8),
            cursor="hand2",
            padx=5,
            pady=2,
            command=lambda: self.step_days(1),
        ).pack(side="left", padx=(0, 2))

        # 3. Time Quick Presets (if include_time is enabled)
        if self.include_time:
            time_row = tk.Frame(self, bg="#12151c")
            time_row.pack(fill="x", pady=(4, 0))

            time_presets = [
                "09:00",
                "12:00",
                "15:00",
                "18:00",
                "21:00",
                "23:59",
            ]
            for t_str in time_presets:
                tk.Button(
                    time_row,
                    text=t_str,
                    bg="#161922",
                    fg="#94a3b8",
                    activebackground="#2b3448",
                    activeforeground="#00e5ff",
                    relief="flat",
                    bd=0,
                    font=(self.theme.font_family, 8),
                    cursor="hand2",
                    padx=5,
                    pady=2,
                    command=lambda t=t_str: self.set_time(t),
                ).pack(side="left", padx=(0, 3))

    def get_value(self) -> str:
        """Return the current date/time string from the entry field."""
        return self.entry.get().strip()

    def set_value(self, val: str) -> None:
        """Set the text inside the entry field."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, val.strip())
        if self.on_change:
            self.on_change(val.strip())

    def insert(self, index: int | str, string: str) -> None:
        """Delegate insert to the internal entry widget."""
        self.entry.insert(index, string)

    def delete(self, first: int | str, last: int | str | None = None) -> None:
        """Delegate delete to the internal entry widget."""
        self.entry.delete(first, last)

    def set_now(self) -> None:
        """Insert the current date and time automatically."""
        now = datetime.datetime.now()
        fmt = "%Y-%m-%d %H:%M" if self.include_time else "%Y-%m-%d"
        self.set_value(now.strftime(fmt))

    def add_days_from_today(self, offset_days: int) -> None:
        """Set date relative to today, preserving time if present."""
        target_date = datetime.date.today() + datetime.timedelta(
            days=offset_days
        )
        date_str = target_date.strftime("%Y-%m-%d")

        current = self.get_value()
        time_part = "18:00"
        if " " in current:
            parts = current.split(maxsplit=1)
            time_part = parts[1]

        if self.include_time:
            self.set_value(f"{date_str} {time_part}")
        else:
            self.set_value(date_str)

    def set_time(self, time_str: str) -> None:
        """Update or append the time component to the existing date."""
        current = self.get_value()
        date_part = datetime.date.today().strftime("%Y-%m-%d")
        if current:
            parts = current.split(maxsplit=1)
            date_part = parts[0]

        self.set_value(f"{date_part} {time_str}")

    def step_days(self, delta_days: int) -> None:
        """Increment or decrement the current date value by delta_days."""
        current = self.get_value()
        base_date = datetime.date.today()
        time_part = "18:00"

        if current:
            parts = current.split(maxsplit=1)
            with contextlib.suppress(ValueError):
                base_date = datetime.date.fromisoformat(parts[0])
            if len(parts) > 1:
                time_part = parts[1]

        new_date = base_date + datetime.timedelta(days=delta_days)
        date_str = new_date.strftime("%Y-%m-%d")

        if self.include_time:
            self.set_value(f"{date_str} {time_part}")
        else:
            self.set_value(date_str)
