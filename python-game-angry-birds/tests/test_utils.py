"""
Unit tests for game utility functions (vector, unit_vector, distance).
"""

import pytest

from utils import distance, unit_vector, vector


def test_vector_from_origin_returns_point_as_vector() -> None:
    """Direction from (0,0) to (3,4) is (3, 4)."""
    assert vector((0, 0), (3, 4)) == (3.0, 4.0)


def test_vector_between_two_points_returns_difference() -> None:
    """Direction from (1,2) to (5,7) is (4, 5)."""
    assert vector((1, 2), (5, 7)) == (4.0, 5.0)


def test_vector_reversed_returns_negated() -> None:
    """Direction from p1 to p0 is negative of direction from p0 to p1."""
    p0, p1 = (10, 20), (30, 50)
    assert vector(p1, p0) == (-20.0, -30.0)


def test_unit_vector_normalizes_to_length_one() -> None:
    """Unit vector of (3, 4) has length 1."""
    u = unit_vector((3.0, 4.0))
    assert abs((u[0] ** 2 + u[1] ** 2) ** 0.5 - 1.0) < 1e-9
    assert abs(u[0] - 0.6) < 1e-9 and abs(u[1] - 0.8) < 1e-9


def test_unit_vector_zero_vector_returns_safe_small_vector() -> None:
    """Zero vector does not divide by zero; returns finite result."""
    u = unit_vector((0.0, 0.0))
    assert u[0] != float("inf") and u[1] != float("inf")
    assert abs(u[0]) < 1 and abs(u[1]) < 1


def test_distance_same_point_returns_zero() -> None:
    """Distance from (1, 2) to (1, 2) is 0."""
    assert distance(1.0, 2.0, 1.0, 2.0) == 0.0


def test_distance_horizontal_line_returns_absolute_difference() -> None:
    """Distance from (0, 0) to (5, 0) is 5."""
    assert distance(0.0, 0.0, 5.0, 0.0) == 5.0


def test_distance_two_points_returns_pythagorean_distance() -> None:
    """Distance from (0, 0) to (3, 4) is 5."""
    assert distance(0.0, 0.0, 3.0, 4.0) == 5.0
