"""Reusable scrollable dark frame for card-based sub-views."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


class ScrollableFrame(tk.Frame):
    """Reusable scrollable dark frame for card-based sub-views."""

    def __init__(self, parent: tk.Widget, bg: str = "#161922") -> None:
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.interior = tk.Frame(self.canvas, bg=bg)

        self.canvas_win = self.canvas.create_window(
            (0, 0), window=self.interior, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.interior.bind("<Configure>", self._on_interior_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.bind_all("<Button-4>", self._on_mousewheel_up, add="+")
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_down, add="+")

    def _on_interior_configure(self, _event: tk.Event[Any]) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event[Any]) -> None:
        self.canvas.itemconfig(self.canvas_win, width=event.width)

    def _on_mousewheel_up(self, _event: tk.Event[Any]) -> None:
        if self.winfo_ismapped():
            self.canvas.yview_scroll(-1, "units")

    def _on_mousewheel_down(self, _event: tk.Event[Any]) -> None:
        if self.winfo_ismapped():
            self.canvas.yview_scroll(1, "units")
