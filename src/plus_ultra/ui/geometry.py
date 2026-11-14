"""Capsule geometry and perimeter path calculation functions.

Applies mathematical modeling:
- Validates input dimensions to eliminate degenerate geometries.
- Generates 2D parametric polygons and perimeter trajectories for animations.
"""

from __future__ import annotations

import math


def generate_capsule_points(
    w: int, h: int, r: int, steps: int = 24
) -> list[float]:
    """Generate exact coordinates for a horizontal capsule polygon.

    Args:
        w: Width of capsule in pixels (must be > 0).
        h: Height of capsule in pixels (must be > 0).
        r: Corner radius in pixels (0 <= r <= min(w, h) / 2).
        steps: Number of radial interpolation steps along semicircle caps.

    Returns:
        List of alternating [x0, y0, x1, y1, ...] coordinate points for canvas.

    Raises:
        ValueError: If dimensions or radius are negative or invalid.
    """
    if w <= 0 or h <= 0:
        raise ValueError(f"Dimensions must be positive: width={w}, height={h}")
    max_radius = min(w, h) // 2
    if r < 0 or r > max_radius:
        raise ValueError(
            f"Radius must be between 0 and {max_radius}, got {r}"
        )
    if steps < 2:
        raise ValueError(f"Steps must be >= 2, got {steps}")

    points: list[float] = []

    # 1. Top straight edge: left to right
    points.extend([float(r), 1.0, float(w - r), 1.0])

    # 2. Right semicircle: -pi/2 to pi/2
    cx, cy = float(w - r), float(h) / 2.0
    for i in range(steps + 1):
        theta = -math.pi / 2.0 + (math.pi * i / steps)
        points.extend(
            [cx + (r - 1) * math.cos(theta), cy + (r - 1) * math.sin(theta)]
        )

    # 3. Bottom straight edge: right to left
    points.extend([float(w - r), float(h - 1), float(r), float(h - 1)])

    # 4. Left semicircle: pi/2 to 3*pi/2
    cx, cy = float(r), float(h) / 2.0
    for i in range(steps + 1):
        theta = math.pi / 2.0 + (math.pi * i / steps)
        points.extend(
            [cx + (r - 1) * math.cos(theta), cy + (r - 1) * math.sin(theta)]
        )

    return points


def generate_perimeter_path(
    w: int, h: int, r: int, num_arc_points: int = 24
) -> list[tuple[float, float]]:
    """Generate ordered 2D perimeter points for the animated border beam.

    Args:
        w: Width of capsule in pixels (must be > 0).
        h: Height of capsule in pixels (must be > 0).
        r: Corner radius in pixels (0 <= r <= min(w, h) / 2).
        num_arc_points: Density of points along semicircle caps.

    Returns:
        List of (x, y) tuples forming a continuous clockwise perimeter loop.

    Raises:
        ValueError: If dimensions or radius are negative or invalid.
    """
    if w <= 0 or h <= 0:
        raise ValueError(f"Dimensions must be positive: width={w}, height={h}")
    max_radius = min(w, h) // 2
    if r < 0 or r > max_radius:
        raise ValueError(
            f"Radius must be between 0 and {max_radius}, got {r}"
        )
    if num_arc_points < 2:
        raise ValueError(f"num_arc_points must be >= 2, got {num_arc_points}")

    path: list[tuple[float, float]] = []

    # 1. Top edge: left to right (step by 2px)
    for x in range(r, w - r + 1, 2):
        path.append((float(x), 1.5))

    # 2. Right semicircle: -pi/2 to pi/2
    cx, cy = float(w - r), float(h) / 2.0
    for i in range(1, num_arc_points + 1):
        theta = -math.pi / 2.0 + (math.pi * i / num_arc_points)
        path.append(
            (cx + (r - 1.5) * math.cos(theta), cy + (r - 1.5) * math.sin(theta))
        )

    # 3. Bottom edge: right to left (step by 2px)
    for x in range(w - r, r - 1, -2):
        path.append((float(x), float(h - 1.5)))

    # 4. Left semicircle: pi/2 to 3*pi/2
    cx, cy = float(r), float(h) / 2.0
    for i in range(1, num_arc_points + 1):
        theta = math.pi / 2.0 + (math.pi * i / num_arc_points)
        path.append(
            (cx + (r - 1.5) * math.cos(theta), cy + (r - 1.5) * math.sin(theta))
        )

    return path
