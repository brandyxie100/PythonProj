"""Tests for the shared geometry helpers."""

from __future__ import annotations

import math

from geom import point_in_circle, point_near_segment, point_segment_distance


def test_point_segment_distance_perpendicular() -> None:
    dist = point_segment_distance((5.0, 3.0), (0.0, 0.0), (10.0, 0.0))
    assert math.isclose(dist, 3.0, abs_tol=1e-6)


def test_point_segment_distance_beyond_endpoint() -> None:
    dist = point_segment_distance((-4.0, 0.0), (0.0, 0.0), (10.0, 0.0))
    assert math.isclose(dist, 4.0, abs_tol=1e-6)


def test_point_near_segment_within_radius() -> None:
    assert point_near_segment((5.0, 2.0), (0.0, 0.0), (10.0, 0.0), 3.0)
    assert not point_near_segment((5.0, 6.0), (0.0, 0.0), (10.0, 0.0), 3.0)


def test_point_in_circle() -> None:
    assert point_in_circle((1.0, 1.0), (0.0, 0.0), 2.0)
    assert not point_in_circle((3.0, 0.0), (0.0, 0.0), 2.0)
