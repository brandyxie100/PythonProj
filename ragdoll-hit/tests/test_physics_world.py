"""Tests for damage calculation and physics world collision routing."""

from __future__ import annotations

import pymunk
import pytest

import config as c
from physics_world import (
    BODY_SHAPE_OWNER,
    WEAPON_SHAPE_OWNER,
    PhysicsWorld,
    compute_damage,
)


def test_compute_damage_below_threshold_returns_zero() -> None:
    """Weak impacts should not deal damage."""
    assert compute_damage(c.MIN_IMPACT_SPEED - 1.0, 1.0) == 0.0


def test_compute_damage_scales_with_velocity() -> None:
    """Faster impacts should deal more damage."""
    low = compute_damage(120.0, 1.0)
    high = compute_damage(240.0, 1.0)
    assert high > low > 0.0


def test_compute_damage_scales_with_weapon_weight() -> None:
    """Heavier weapons should multiply damage output."""
    light = compute_damage(200.0, 1.0)
    heavy = compute_damage(200.0, 2.0)
    assert heavy == pytest.approx(light * 2.0)


def test_physics_world_step_advances_space() -> None:
    """Space stepping should move dynamic bodies under gravity."""
    world = PhysicsWorld()
    body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 10))
    body.position = 100, 400
    shape = pymunk.Circle(body, 10)
    world.space.add(body, shape)
    y_before = body.position.y
    world.step()
    assert body.position.y < y_before


def test_physics_world_drain_hits_starts_empty() -> None:
    """No collisions means no pending hits."""
    world = PhysicsWorld()
    world.step()
    assert world.drain_hits() == []
