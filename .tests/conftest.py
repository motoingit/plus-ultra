"""Pytest configuration and test environment initialization for PLUS-ULTRA."""

from __future__ import annotations

import os
import pathlib
import sys

from plus_ultra.ui.icons import clear_icon_cache

# Ensure Tkinter can find Tcl/Tk libraries on Windows under uv-managed Python.
# Crucial: Use as_posix() because Tcl treats backslashes (\tcl) as escape characters!
if sys.platform == "win32":
    base_prefix = pathlib.Path(sys.base_prefix).resolve()
    tcl_dir = base_prefix / "tcl"
    if tcl_dir.is_dir():
        tcl_86 = (tcl_dir / "tcl8.6").as_posix()
        tk_86 = (tcl_dir / "tk8.6").as_posix()
        os.environ["TCL_LIBRARY"] = tcl_86
        os.environ["TK_LIBRARY"] = tk_86


import pytest


@pytest.fixture(autouse=True)
def _cleanup_tk_icon_cache() -> None:
    """Clear icon cache between tests so PhotoImages don't leak across roots."""
    clear_icon_cache()
