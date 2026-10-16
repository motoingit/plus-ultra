"""Base helpers and utilities for modal dialogs."""

from __future__ import annotations

import tkinter as tk


def center_modal(dialog: tk.Toplevel, parent: tk.Widget) -> None:
    """Center modal dialog over parent window."""
    dialog.update_idletasks()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    px = parent.winfo_x()
    py = parent.winfo_y()
    w = dialog.winfo_width()
    h = dialog.winfo_height()
    x = max(20, px + (pw - w) // 2)
    y = max(20, py + (ph - h) // 2)
    dialog.geometry(f"+{x}+{y}")
