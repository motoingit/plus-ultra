"""Desktop platform adapter and process management for PLUS-ULTRA.

Applies OS concepts:
- Mutual Exclusion & Single Instance: POSIX advisory file locking (fcntl.flock)
  ensures only one application process runs concurrently per user session.
- Process lifecycle: Clean lock acquisition, PID recording, and release on
  normal shutdown or signal termination.
"""

from __future__ import annotations

import contextlib
import fcntl
import logging
import os
from pathlib import Path

from plus_ultra import config

logger = logging.getLogger(__name__)

LOCK_FILENAME = "plus-ultra.lock"


class SingleInstanceLock:
    """Manages an exclusive advisory file lock for the application process."""

    def __init__(self, lock_path: Path | None = None) -> None:
        self.lock_path = lock_path or (config.get_state_dir() / LOCK_FILENAME)
        self._fd: int | None = None

    def acquire(self) -> bool:
        """Attempt to acquire exclusive advisory lock without blocking.

        Returns:
            True if lock was acquired, False if another instance holds it.
        """
        config.get_state_dir()  # Ensure state directory exists (0o700)
        try:
            fd = os.open(
                self.lock_path,
                os.O_RDWR | os.O_CREAT,
                0o600,
            )
            # Try exclusive non-blocking lock
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Record PID for diagnostic inspection
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, f"{os.getpid()}\n".encode())

            self._fd = fd
            logger.info(
                "Acquired single-instance lock on %s (pid: %d)",
                self.lock_path,
                os.getpid(),
            )
            return True
        except (BlockingIOError, OSError) as exc:
            logger.warning(
                "Single-instance lock contention on %s: %s",
                self.lock_path,
                exc,
            )
            with contextlib.suppress(OSError):
                if "fd" in locals():
                    os.close(fd)
            return False

    def release(self) -> None:
        """Release the advisory lock and close the file descriptor."""
        if self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                os.close(self._fd)
                logger.info(
                    "Released single-instance lock on %s", self.lock_path
                )
            except OSError as err:
                logger.error("Error releasing lock: %s", err)
            finally:
                self._fd = None
                with contextlib.suppress(OSError):
                    self.lock_path.unlink()

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
        self.release()
