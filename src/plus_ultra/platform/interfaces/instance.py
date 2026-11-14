"""Single-instance mutual exclusion lock interface.

Applies OS concepts:
- Mutual Exclusion & Critical Sections: Ensures only one application process
  executes concurrently per user desktop session.
- Advisory vs mandatory file locking or OS named mutexes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class SingleInstanceLock(Protocol):
    """Protocol for single-instance concurrency control."""

    @property
    def lock_path(self) -> Path:
        """Filesystem path or identifier used for locking."""
        ...

    @property
    def is_acquired(self) -> bool:
        """Return True if this instance currently holds the lock."""
        ...

    def acquire(self) -> bool:
        """Attempt to acquire exclusive lock without blocking.

        Returns:
            True if lock was acquired, False if another instance holds it.
        """
        ...

    def release(self) -> None:
        """Release the exclusive lock and remove ephemeral lock file."""
        ...

    def __enter__(self) -> bool:
        """Context manager entry acquiring the lock."""
        ...

    def __exit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
        """Context manager exit releasing the lock."""
        ...
