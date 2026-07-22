"""Tests for versus-duel scene stage/respawn behavior."""

from __future__ import annotations

from duel_mode import VersusScene


def test_enemy_respawn_uses_different_weapon() -> None:
    scene = VersusScene()
    weapons = [scene._enemy.weapon_key]
    # Each respawn must pick a weapon different from the previous enemy's.
    for _ in range(40):
        scene._load_stage(1)
        weapons.append(scene._enemy.weapon_key)
    for previous, current in zip(weapons, weapons[1:]):
        assert previous != current


def test_enemy_respawns_at_same_pillar_location() -> None:
    scene = VersusScene()
    original_x = scene._enemy.x
    original_y = scene._enemy.ground_y
    scene._load_stage(2)
    assert scene._enemy.x == original_x
    assert scene._enemy.ground_y == original_y
