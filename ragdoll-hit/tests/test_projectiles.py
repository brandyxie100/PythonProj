"""Tests for parabolic projectile motion."""

from __future__ import annotations

import config as c
from projectiles import Projectile, spawn_projectile


def test_projectile_follows_parabola() -> None:
    proj = spawn_projectile("spear", "player", (0.0, 400.0), 0.9, 1, 800.0)
    start_vy = proj.vy
    apex_y = proj.y
    for _ in range(30):
        proj.update(1.0 / 60.0, ground_y=c.SCREEN_H + 100)
        apex_y = min(apex_y, proj.y)
    # It should rise (y decreases) then gravity pulls it back down.
    assert apex_y < 400.0
    assert proj.vy > start_vy  # gravity increased downward velocity over time


def test_projectile_dies_on_ground() -> None:
    proj = Projectile("bow", "player", x=0.0, y=0.0, vx=0.0, vy=100.0)
    for _ in range(600):
        proj.update(1.0 / 60.0, ground_y=200.0)
        if proj.dead:
            break
    assert proj.dead
    assert proj.y >= 200.0


def test_launch_speed_scales_with_weapon() -> None:
    fast = spawn_projectile("bow", "player", (0.0, 0.0), 0.0, 1, 1000.0)
    slow = spawn_projectile("broadsword", "player", (0.0, 0.0), 0.0, 1, 1000.0)
    assert abs(fast.vx) > abs(slow.vx)
