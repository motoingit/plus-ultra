"""Windows process management and introspection.

Applies OS concepts:
- Process querying and lifecycle via Windows API / os.kill probe.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class WindowsProcessManager:
    """Provides process introspection for Windows."""

    def get_current_pid(self) -> int:
        return os.getpid()

    def is_pid_running(self, pid: int) -> bool:
        """Check if process with PID exists."""
        if pid <= 0:
            return False
        try:
            # os.kill(pid, 0) performs OpenProcess without terminating
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Access denied means process exists under another privilege level
            return True
        except OSError:
            return False
