"""Platform-specific window effects and presentation interface.

Applies OS concepts:
- Window Manager and Compositor interactions: XWayland XShape clipping,
  Windows DWM attributes, rounded window bounds, always-on-top attributes.
"""

from __future__ import annotations

import tkinter as tk
from typing import Protocol, runtime_checkable


@runtime_checkable
class WindowEffects(Protocol):
    """Protocol for platform-specific window styling and masking."""

    def apply_capsule_shape(
        self, window: tk.Tk | tk.Toplevel, width: int, height: int, radius: int
    ) -> bool:
        """Apply non-rectangular pill/capsule clipping to window.

        Returns:
            True if shape mask was successfully applied, False on fallback.
        """
        ...

    def set_always_on_top(
        self, window: tk.Tk | tk.Toplevel, enabled: bool
    ) -> bool:
        """Configure window stacking to hover above all other windows."""
        ...
