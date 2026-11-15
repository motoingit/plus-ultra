"""Category domain entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Category:
    """Category classification entity for organizing tasks and resources."""

    id: str
    name: str
    color: str = "#4a5568"
    created_at: str = ""
    updated_at: str = ""
    synced_at: str | None = None
    is_deleted: int = 0

