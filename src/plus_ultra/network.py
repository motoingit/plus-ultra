"""Network status detection and connectivity utility for PLUS-ULTRA (Facade).

Re-exports NetworkStatusMonitor and is_network_online from
plus_ultra.diagnostics.network for backward compatibility.
"""

from __future__ import annotations

from plus_ultra.diagnostics.network import (
    NetworkStatusMonitor,
    is_network_online,
)

__all__ = [
    "NetworkStatusMonitor",
    "is_network_online",
]
