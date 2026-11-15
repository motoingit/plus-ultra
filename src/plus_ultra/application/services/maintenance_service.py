"""Application service for database maintenance and demo data management."""

from __future__ import annotations

import logging
from typing import Any

from plus_ultra.infrastructure.persistence.database_factory import (
    DatabaseFactory,
)
from plus_ultra.infrastructure.persistence.database_initializer import (
    wipe_database,
)

logger = logging.getLogger(__name__)


class MaintenanceService:
    """Coordinates database maintenance, resets, and demo reseeding."""

    def __init__(self, factory: DatabaseFactory | None = None) -> None:
        self.factory = factory or DatabaseFactory()

    def wipe_all_data(self) -> None:
        """Clear all domain records while preserving schema and connections."""
        session = self.factory.create_session()
        try:
            wipe_database(session)
            logger.info("MaintenanceService: Database wiped successfully.")
        finally:
            session.close()

    def reseed_demo_workspace_data(self, force: bool = False) -> dict[str, Any]:
        """Reseed initial demo data across all domain categories."""
        from plus_ultra.database import seed_demo_workspace_data

        session = self.factory.create_session()
        try:
            res = seed_demo_workspace_data(session, force=force)
            logger.info("MaintenanceService: Demo data reseeded successfully.")
            return res if isinstance(res, dict) else {}
        finally:
            session.close()
