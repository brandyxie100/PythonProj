"""Tests for enemy AI control output."""

from __future__ import annotations

import config as c
from ai_controller import EnemyAI
from stickman import Stickman
from terrain import level_config
from weapon import Weapon


def _enemy() -> Stickman:
    return Stickman(
        sid=2,
        team="enemy",
        x=800.0,
        y=500.0,
        color=c.ENEMY_RED,
        weapon=Weapon("javelin"),
        max_health=100.0,
        move_scale=1.0,
        attack_scale=1.0,
    )


def _player() -> Stickman:
    return Stickman(
        sid=1,
        team="player",
        x=200.0,
        y=500.0,
        color=c.PLAYER_BLUE,
        weapon=Weapon("broadsword"),
        max_health=120.0,
        move_scale=1.0,
        attack_scale=1.0,
    )


def test_ai_moves_toward_player_when_far() -> None:
    arena = level_config(1).arena
    ai = EnemyAI(aggressiveness=1.0)
    move, jump, attack, _, _ = ai.update(_enemy(), _player(), arena, 1 / 60)
    assert move == -1
    assert not jump
    assert not attack


def test_ai_attacks_when_in_range() -> None:
    arena = level_config(1).arena
    ai = EnemyAI(aggressiveness=1.2)
    enemy = _enemy()
    player = _player()
    enemy.x = 260.0
    move, jump, attack, _, _ = ai.update(enemy, player, arena, 1 / 60)
    assert move in (-1, 0, 1)
    assert not jump
    assert attack
