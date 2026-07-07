"""Tests for weapon hit collision helper."""

from __future__ import annotations

import config as c
from physics_world import weapon_hit
from stickman import Stickman
from weapon import Weapon


def _fighter(sid: int, team: str, x: float, y: float, weapon_name: str) -> Stickman:
    return Stickman(
        sid=sid,
        team=team,
        x=x,
        y=y,
        color=c.PLAYER_BLUE if team == "player" else c.ENEMY_RED,
        weapon=Weapon(weapon_name),
        max_health=120.0,
        move_scale=1.0,
        attack_scale=1.0,
        facing=1 if team == "player" else -1,
    )


def test_weapon_hit_returns_damage_when_target_in_swing_path() -> None:
    attacker = _fighter(1, "player", 240.0, 500.0, "hammer")
    victim = _fighter(2, "enemy", 298.0, 486.0, "stick")
    attacker.arm_main_angle = 0.0
    attacker.try_attack()
    attacker.weapon.attack_timer = attacker.weapon.stats.sweep_time * 0.45
    seg_a, seg_b, _ = attacker.weapon_segment()
    mid_x = (seg_a[0] + seg_b[0]) * 0.5
    mid_y = (seg_a[1] + seg_b[1]) * 0.5
    victim.x = mid_x
    victim.y = mid_y + c.TORSO_LEN * 0.45
    hit = weapon_hit(attacker, victim)
    assert hit is not None
    assert hit.damage > 0


def test_weapon_hit_is_one_per_target_per_swing() -> None:
    attacker = _fighter(1, "player", 240.0, 500.0, "sword")
    victim = _fighter(2, "enemy", 292.0, 485.0, "stick")
    attacker.arm_main_angle = 0.0
    attacker.try_attack()
    first = weapon_hit(attacker, victim)
    second = weapon_hit(attacker, victim)
    assert first is not None
    assert second is None
