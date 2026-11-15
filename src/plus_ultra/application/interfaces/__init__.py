"""Application interfaces package."""

from __future__ import annotations

from plus_ultra.application.interfaces.unit_of_work import (
    UnitOfWork,
    UnitOfWorkFactory,
)

__all__ = ["UnitOfWork", "UnitOfWorkFactory"]

