"""Abstract repository contract for AppState local machine runtime state."""

from __future__ import annotations

from typing import Protocol


class AppStateRepositoryContract(Protocol):
    """Abstract contract for runtime machine-state repository operations."""

    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve machine-state value by key."""
        ...

    def set(self, key: str, value: str) -> None:
        """Store or update machine-state value."""
        ...

    def get_widget_position(self) -> tuple[int, int] | None:
        """Retrieve floating widget screen position (x, y)."""
        ...

    def set_widget_position(self, x: int, y: int) -> None:
        """Save floating widget screen position."""
        ...

