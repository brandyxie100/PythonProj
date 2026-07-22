"""Tests for versus-duel scene stage/respawn behavior."""

from __future__ import annotations

import pygame

from duel_fighter import EmbeddedWeapon
from duel_mode import VersusScene, _TOTAL_STAGES, duel_stage


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


def test_all_duel_stages_are_defined() -> None:
    for number in range(1, _TOTAL_STAGES + 1):
        spec = duel_stage(number)
        assert spec.number == number
        assert spec.reward > 0


def test_killing_enemy_opens_score_popup() -> None:
    scene = VersusScene()
    scene._enemy.apply_hit(
        "head",
        1.0,
        EmbeddedWeapon("spear", scene._enemy.x, scene._enemy.ground_y, 0.0),
    )
    assert scene._enemy.dead
    result = scene.update(1 / 60)
    assert result is None
    assert scene._clear_popup is not None
    assert scene._clear_popup.cleared_stage == 1
    assert scene._clear_popup.reward == duel_stage(1).reward
    assert scene.score == duel_stage(1).reward
    # Combat stays frozen while the popup is open.
    assert scene.update(1 / 60) is None
    assert scene._stage_no == 1


def test_dismissing_popup_advances_to_next_stage() -> None:
    scene = VersusScene()
    scene._enemy.dead = True
    scene.update(1 / 60)
    assert scene._clear_popup is not None
    scene._dismiss_stage_clear_popup()
    assert scene._clear_popup is None
    assert scene._stage_no == 2
    assert not scene._enemy.dead


def test_final_stage_popup_finishes_as_win() -> None:
    scene = VersusScene()
    scene._stage_no = _TOTAL_STAGES
    scene._enemy.dead = True
    scene.update(1 / 60)
    assert scene._clear_popup is not None
    assert scene._clear_popup.is_final
    result = scene._dismiss_stage_clear_popup()
    assert result == "win"


def test_popup_space_key_continues() -> None:
    scene = VersusScene()
    scene._enemy.dead = True
    scene.update(1 / 60)
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
    scene.handle_event(event)
    assert scene._stage_no == 2
    assert scene._clear_popup is None
