"""
Angry Birds Clone - Utility Helpers
===================================
Pure math/geometry helpers used by the game (no pygame/pymunk).
Extracted for testability.
"""


def vector(p0: tuple[float, float], p1: tuple[float, float]) -> tuple[float, float]:
    """Calculate the direction vector from point p0 to point p1.

    Args:
        p0: Starting point as (x0, y0).
        p1: Ending point as (x1, y1).

    Returns:
        A tuple (dx, dy) representing the direction vector.
    """
    a = p1[0] - p0[0]
    b = p1[1] - p0[1]
    return (a, b)


def unit_vector(v: tuple[float, float]) -> tuple[float, float]:
    """Normalize a 2D vector to unit length.

    Args:
        v: A 2D vector as (a, b).

    Returns:
        The unit vector (ua, ub) with length 1.
        If the input vector has zero length, returns a near-zero result
        to avoid division by zero.
    """
    h = ((v[0] ** 2) + (v[1] ** 2)) ** 0.5
    if h == 0:
        h = 0.000000000000001  # Prevent division by zero
    ua = v[0] / h
    ub = v[1] / h
    return (ua, ub)


def distance(xo: float, yo: float, x: float, y: float) -> float:
    """Calculate the Euclidean distance between two points.

    Args:
        xo: X coordinate of the first point.
        yo: Y coordinate of the first point.
        x: X coordinate of the second point.
        y: Y coordinate of the second point.

    Returns:
        The straight-line distance between the two points.
    """
    dx = x - xo
    dy = y - yo
    d = ((dx**2) + (dy**2)) ** 0.5
    return d
