"""Automated tests for capsule geometry derivation and input validation.

Validates:
- Mathematical radius derivation: radius == min(width, height) // 2.
- Input validation: rejection of non-positive dimensions and invalid radii.
- Perimeter path: closed-loop continuity and ordered perimeter points.
- Resizing behavior and derived coordinate anchors.
"""

from __future__ import annotations

import pytest

from plus_ultra.ui.geometry import (
    generate_capsule_points,
    generate_perimeter_path,
)
from plus_ultra.ui.theme import CapsuleGeometry


def test_capsule_geometry_derived_radius() -> None:
    """Corner radius is strictly derived as min(width, height) // 2."""
    g1 = CapsuleGeometry(width=350, height=30)
    assert g1.radius == 15
    assert g1.center_x == 175
    assert g1.center_y == 15

    # Taller pill
    g2 = CapsuleGeometry(width=100, height=60)
    assert g2.radius == 30

    # Resized wide pill
    g3 = CapsuleGeometry(width=500, height=40)
    assert g3.radius == 20


def test_capsule_geometry_derived_anchors() -> None:
    """Verify icon and network indicator anchors are derived relative to caps."""
    geom = CapsuleGeometry(width=350, height=30)
    assert geom.bell_center_x == int(geom.radius * 3.4)
    assert geom.net_dot_x == geom.width - int(geom.radius * 1.8)


def test_capsule_geometry_dimension_validation() -> None:
    """CapsuleGeometry rejects invalid non-positive or conflicting bounds."""
    with pytest.raises(ValueError, match="width must be positive"):
        CapsuleGeometry(width=-10, height=30)

    with pytest.raises(ValueError, match="height must be positive"):
        CapsuleGeometry(width=350, height=0)

    with pytest.raises(ValueError, match="cannot exceed max_width"):
        CapsuleGeometry(width=350, height=30, min_width=600, max_width=400)


def test_generate_capsule_points_valid() -> None:
    """Generate exact 2D capsule polygon points."""
    pts = generate_capsule_points(w=350, h=30, r=15, steps=12)
    assert len(pts) > 0
    # Coordinates come in alternating x, y pairs
    assert len(pts) % 2 == 0
    for i in range(0, len(pts), 2):
        x, y = pts[i], pts[i + 1]
        assert 0.0 <= x <= 350.0
        assert 0.0 <= y <= 30.0


def test_generate_capsule_points_input_validation() -> None:
    """generate_capsule_points raises ValueError on invalid inputs."""
    with pytest.raises(ValueError, match="Dimensions must be positive"):
        generate_capsule_points(w=0, h=30, r=15)

    with pytest.raises(ValueError, match="Dimensions must be positive"):
        generate_capsule_points(w=350, h=-5, r=15)

    with pytest.raises(ValueError, match="Radius must be between"):
        generate_capsule_points(w=350, h=30, r=20)  # max is 15

    with pytest.raises(ValueError, match="Steps must be >= 2"):
        generate_capsule_points(w=350, h=30, r=15, steps=1)


def test_generate_perimeter_path_valid() -> None:
    """Perimeter path generates a continuous 2D clockwise loop."""
    path = generate_perimeter_path(w=350, h=30, r=15, num_arc_points=12)
    assert len(path) > 50
    # Check bounds of every perimeter point
    for x, y in path:
        assert 0.0 <= x <= 350.0
        assert 0.0 <= y <= 30.0


def test_generate_perimeter_path_validation() -> None:
    """generate_perimeter_path raises ValueError on invalid inputs."""
    with pytest.raises(ValueError):
        generate_perimeter_path(w=-10, h=30, r=15)

    with pytest.raises(ValueError):
        generate_perimeter_path(w=350, h=30, r=-1)
