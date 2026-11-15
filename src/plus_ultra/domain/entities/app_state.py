"""AppState domain entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppState:
    """Key-value pair for machine-written local runtime state."""

    key: str
    value: str

