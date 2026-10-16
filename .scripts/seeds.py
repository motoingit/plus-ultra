"""Initial demo dataset for workspace modules and tasks.

Legacy compatibility wrapper around .scripts/seed_data.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure 'src' and '.scripts' are in sys.path
_scripts_dir = Path(__file__).resolve().parent
_src_dir = _scripts_dir.parent / "src"
for p in (str(_scripts_dir), str(_src_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from seed_data import (  # noqa: E402
    main,
    seed_demo_workspace_data,
    unseed_demo_workspace_data,
)

__all__ = [
    "main",
    "seed_demo_workspace_data",
    "unseed_demo_workspace_data",
]

if __name__ == "__main__":
    sys.exit(main())
