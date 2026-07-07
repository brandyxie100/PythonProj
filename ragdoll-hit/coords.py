"""Coordinate helpers for drawing and geometry."""

from __future__ import annotations


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t
