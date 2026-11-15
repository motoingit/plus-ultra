"""SQLAlchemy implementation of AppStateRepositoryContract."""

from __future__ import annotations

from sqlalchemy.orm import Session

from plus_ultra.domain.repositories.app_state_repository import (
    AppStateRepositoryContract,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    AppStateModel,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories.base import (
    SqlAlchemyRepositoryBase,
)


class SqlAlchemyAppStateRepository(
    SqlAlchemyRepositoryBase, AppStateRepositoryContract
):
    """SQLAlchemy repository for app_state machine runtime state."""

    def __init__(self, session: Session, autocommit: bool = True) -> None:
        super().__init__(session=session, autocommit=autocommit)

    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve machine-written state value."""
        model = self.session.get(AppStateModel, key)
        return str(model.value) if model else default

    def set(self, key: str, value: str) -> None:
        """Set or update machine-written state value atomically."""
        model = self.session.get(AppStateModel, key)
        if model is not None:
            model.value = str(value)
        else:
            model = AppStateModel(key=key, value=str(value))
            self.session.add(model)
        self._commit_or_flush()

    def get_widget_position(self) -> tuple[int, int] | None:
        """Retrieve saved widget screen coordinates (widget_x, widget_y)."""
        x_str = self.get("widget_x")
        y_str = self.get("widget_y")
        if x_str is not None and y_str is not None:
            try:
                return int(x_str), int(y_str)
            except ValueError:
                return None
        return None

    def set_widget_position(self, x: int, y: int) -> None:
        """Save widget screen coordinates to machine state."""
        self.set("widget_x", str(x))
        self.set("widget_y", str(y))

