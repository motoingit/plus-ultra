"""Network status detection and connectivity utility for PLUS-ULTRA."""

from __future__ import annotations

import queue
import socket
import threading


def is_network_online(
    host: str = "1.1.1.1", port: int = 53, timeout: float = 1.0
) -> bool:
    """Check network connectivity via a lightweight socket probe.

    Probes Cloudflare/Google public DNS on port 53 without dependencies.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, TimeoutError):
        if host != "8.8.8.8":
            try:
                with socket.create_connection(("8.8.8.8", 53), timeout=timeout):
                    return True
            except (OSError, TimeoutError):
                pass
        return False


class NetworkStatusMonitor:
    """Thread-safe network probe monitor using a pure Python queue."""

    def __init__(self) -> None:
        self.result_queue: queue.Queue[bool] = queue.Queue()
        self._probing: bool = False
        self.last_status: bool = True

    def probe_async(self) -> None:
        """Start background socket probe if not already running."""
        if self._probing:
            return
        self._probing = True

        def _worker() -> None:
            try:
                online = is_network_online()
                self.result_queue.put(online)
            finally:
                self._probing = False

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def get_result(self) -> bool | None:
        """Retrieve latest probe result without blocking, or None."""
        try:
            val = self.result_queue.get_nowait()
            self.last_status = val
            return val
        except queue.Empty:
            return None
