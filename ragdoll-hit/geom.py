"""Small 2D geometry helpers shared by hit-testing code."""

from __future__ import annotations

import math

Point = tuple[float, float]


def distance(a: Point, b: Point) -> float:
    """Euclidean distance between two points."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_segment_distance(p: Point, a: Point, b: Point) -> float:
    """Shortest distance from point ``p`` to segment ``ab``."""
    abx = b[0] - a[0]
    aby = b[1] - a[1]
    ab_len_sq = abx * abx + aby * aby
    if ab_len_sq <= 1e-9:
        return distance(p, a)
    t = ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / ab_len_sq
    t = max(0.0, min(1.0, t))
    nearest = (a[0] + abx * t, a[1] + aby * t)
    return distance(p, nearest)


def point_in_circle(p: Point, center: Point, radius: float) -> bool:
    """Return True when ``p`` lies within ``radius`` of ``center``."""
    return distance(p, center) <= radius


def point_near_segment(p: Point, a: Point, b: Point, radius: float) -> bool:
    """Return True when ``p`` lies within ``radius`` of segment ``ab``."""
    return point_segment_distance(p, a, b) <= radius
