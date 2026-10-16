"""Icon loader and image manager for PLUS-ULTRA.

Loads icons from resources/icons/, resources/base/, resources/folders/,
and resources/tabs/, falling back to fallback.png. Uses pure Python
standard-library Tkinter PhotoImage scaling with zero external runtime
dependencies.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

# In-memory image cache keyed by (interpreter_id, icon_name, size)
_ICON_CACHE: dict[tuple[int, str, int], tk.PhotoImage] = {}


def _get_resource_dirs() -> list[Path]:
    """Return prioritized list of resource directories to search for icons."""
    base_pkg = Path(__file__).resolve().parents[1]
    res_dir = base_pkg / "resources"
    return [
        res_dir / "icons",
        res_dir / "base",
        res_dir / "folders",
        res_dir / "tabs",
    ]


def find_icon_path(icon_name: str) -> Path | None:
    """Resolve an icon file path by searching resource subdirectories."""
    dirs = _get_resource_dirs()
    candidates = [
        f"{icon_name}.png",
        f"{icon_name}.gif",
        f"{icon_name}.ppm",
        f"{icon_name}.svg",
    ]

    for d in dirs:
        if not d.exists():
            continue
        for candidate in candidates:
            cand_path = d / candidate
            if cand_path.is_file():
                return cand_path

    # Fallback path
    fallback = dirs[0] / "fallback.png"
    if fallback.is_file():
        return fallback

    return None


def get_icon(
    icon_name: str = "fallback",
    size: int = 24,
    master: tk.Misc | None = None,
) -> tk.PhotoImage | None:
    """Retrieve and scale a cached Tkinter PhotoImage for the specified icon.

    Args:
        icon_name: Name of the icon asset (without extension).
        size: Target pixel bounding box dimension.
        master: Optional Tk widget representing the active interpreter root.

    Returns:
        A cached PhotoImage scaled via subsample, or None if Tk is uninitialized
        or no image asset was found.
    """
    try:
        active_root = (
            master.winfo_toplevel() if master is not None else tk._default_root
        )
        if active_root is None or not active_root.winfo_exists():
            return None
    except Exception:
        return None

    root_id = id(active_root)
    cache_key = (root_id, icon_name, size)
    if cache_key in _ICON_CACHE:
        cached = _ICON_CACHE[cache_key]
        try:
            active_root.tk.call("image", "type", str(cached))
            return cached
        except Exception:
            _ICON_CACHE.pop(cache_key, None)

    path = find_icon_path(icon_name)
    if not path or path.suffix.lower() == ".svg":
        if path and path.suffix.lower() == ".svg":
            path = find_icon_path("fallback")
            if not path or path.suffix.lower() == ".svg":
                return None
        else:
            return None

    try:
        img = tk.PhotoImage(file=str(path), master=active_root)
        orig_w = img.width()
        orig_h = img.height()

        if orig_w > size and orig_h > size and size > 0:
            scale_x = max(1, orig_w // size)
            scale_y = max(1, orig_h // size)
            scaled = img.subsample(scale_x, scale_y)
            _ICON_CACHE[cache_key] = scaled
            return scaled

        _ICON_CACHE[cache_key] = img
        return img
    except Exception:
        return None


def clear_icon_cache() -> None:
    """Flush the in-memory icon cache."""
    _ICON_CACHE.clear()
