"""Capsule geometry and perimeter path calculation functions."""

from __future__ import annotations

import math


def generate_capsule_points(
    w: int, h: int, r: int, steps: int = 24
) -> list[float]:
    """Generate exact coordinates for a horizontal capsule polygon."""
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
    """Generate ordered 2D perimeter points for the animated border beam."""
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
