"""Coordinate helpers and pymunk space utilities."""

from __future__ import annotations

import config as c
import pymunk


def pygame_to_pymunk(x: float, y: float) -> tuple[float, float]:
    """Convert pygame screen coordinates to pymunk world coordinates.

    Args:
        x: Horizontal screen position.
        y: Vertical screen position (down-positive).

    Returns:
        Tuple of pymunk x and y (up-positive).
    """
    return x, float(c.SCREEN_H) - y


def pymunk_to_pygame(pos: pymunk.Vec2d) -> tuple[int, int]:
    """Convert a pymunk position to pygame screen coordinates.

    Args:
        pos: Position in pymunk space.

    Returns:
        Integer pygame (x, y) with Y down-positive.
    """
    return int(pos.x), int(c.SCREEN_H - pos.y)


def pygame_y_to_pymunk(y: float) -> float:
    """Convert a single pygame Y value to pymunk Y."""
    return float(c.SCREEN_H) - y
