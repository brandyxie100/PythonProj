"""Tests for stickman movement and attack controls."""

from __future__ import annotations

import config as c
from stickman import Stickman
from terrain import level_config
from weapon import Weapon


def _player() -> Stickman:
    return Stickman(
        sid=1,
        team="player",
        x=220.0,
        y=500.0,
        color=c.PLAYER_BLUE,
        weapon=Weapon("broadsword"),
        max_health=120.0,
        move_scale=1.0,
        attack_scale=1.0,
    )


def test_double_jump_limit() -> None:
    fighter = _player()
    assert fighter.try_jump()
    assert fighter.try_jump()
    assert not fighter.try_jump()


def test_attack_starts_and_respects_cooldown() -> None:
    fighter = _player()
    assert fighter.try_attack()
    assert not fighter.try_attack()


def test_take_damage_launches_and_stuns() -> None:
    fighter = _player()
    fighter.grounded = True
    fighter.vx = 0.0
    fighter.vy = 0.0
    fighter.take_damage(10.0, 400.0, 350.0)
    assert fighter.vx == 400.0
    assert fighter.vy == -350.0
    assert not fighter.grounded
    assert fighter.is_stunned
    assert not fighter.try_attack()
    assert not fighter.try_jump()


def test_update_lands_on_floor_and_resets_jumps() -> None:
    fighter = _player()
    arena = level_config(1).arena
    fighter.vy = 700.0
    fighter.update(arena, 1 / 30)
    fighter.update(arena, 1 / 30)
    assert fighter.y <= arena.floor_y - c.LEG_LEN + 1.0
    assert fighter.jumps_used == 0
