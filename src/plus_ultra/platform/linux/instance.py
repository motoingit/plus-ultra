"""Linux single-instance mutual exclusion lock using POSIX fcntl.flock.

Applies OS concepts:
- Advisory file locking (fcntl.flock) with LOCK_EX | LOCK_NB.
- Enforces private file permissions (mode 0o600: owner read/write only).
- Records process PID for diagnostic inspection.
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[assignment]

from plus_ultra.platform.interfaces.paths import PathProvider

logger = logging.getLogger(__name__)


class LinuxSingleInstanceLock:
    """Manages an exclusive POSIX advisory lock file on Linux."""

    def __init__(
        self,
        paths: PathProvider | None = None,
        lock_path: Path | None = None,
        lock_filename: str = "plus-ultra.lock",
    ) -> None:
        if lock_path is not None:
            self._lock_path = lock_path
        elif paths is not None:
            self._lock_path = paths.get_state_dir() / lock_filename
        else:
            self._lock_path = (
                Path.home() / ".local" / "state" / "plus-ultra" / lock_filename
            )

        self._fd: int | None = None
        self._is_acquired = False

    @property
    def lock_path(self) -> Path:
        return self._lock_path

    @property
    def is_acquired(self) -> bool:
        return self._is_acquired

    def acquire(self) -> bool:
        """Attempt to acquire exclusive advisory lock without blocking."""
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(
                self._lock_path,
                os.O_RDWR | os.O_CREAT,
                0o600,
            )
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, f"{os.getpid()}\n".encode())

            self._fd = fd
            self._is_acquired = True
            logger.info(
                "Acquired Linux single-instance lock on %s (pid: %d)",
                self._lock_path,
                os.getpid(),
            )
            return True
        except (BlockingIOError, OSError) as exc:
            logger.warning(
                "Linux single-instance lock contention on %s: %s",
                self._lock_path,
                exc,
            )
            with contextlib.suppress(OSError):
                if "fd" in locals():
                    os.close(fd)
            self._is_acquired = False
            return False

    def release(self) -> None:
        """Release the advisory lock and delete lock file."""
        if self._fd is not None:
            try:
                if fcntl is not None:
                    fcntl.flock(self._fd, fcntl.LOCK_UN)
                os.close(self._fd)
                logger.info(
                    "Released Linux single-instance lock on %s",
                    self._lock_path,
                )
            except OSError as err:
                logger.error("Error releasing Linux lock: %s", err)
            finally:
                self._fd = None
                self._is_acquired = False
                with contextlib.suppress(OSError):
                    self._lock_path.unlink()

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
        self.release()
