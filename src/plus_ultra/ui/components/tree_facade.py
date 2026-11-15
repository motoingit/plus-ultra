"""Facade for backward compatibility with tests expecting panel.tree."""

from __future__ import annotations

from typing import Any


class TreeCompatibilityFacade:
    """Facade for backward compatibility with tests expecting panel.tree."""

    def __init__(self, panel: Any) -> None:
        self.panel = panel

    def get_children(self) -> list[str]:
        """Return task IDs of currently filtered and rendered tasks."""
        return [t.id for t in self.panel._filtered_tasks]
