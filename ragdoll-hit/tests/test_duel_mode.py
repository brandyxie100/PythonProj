"""Tests for versus-duel stage economy, shop, and pass rules."""

from __future__ import annotations

import pygame

import config as c
from duel_fighter import EmbeddedWeapon
from duel_mode import VersusScene, _TOTAL_STAGES, duel_stage


def _embed(scene: VersusScene) -> EmbeddedWeapon:
    enemy = scene._enemy
    return EmbeddedWeapon("spear", enemy.x, enemy.ground_y, 0.0)


def test_enemy_respawn_uses_different_weapon() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    weapons = [scene._enemy.weapon_key]
    for _ in range(40):
        scene._spawn_enemy()
        weapons.append(scene._enemy.weapon_key)
    for previous, current in zip(weapons, weapons[1:]):
        assert previous != current


def test_enemy_respawns_at_same_pillar_location() -> None:
    scene = VersusScene()
    original_x = scene._enemy.x
    original_y = scene._enemy.ground_y
    scene._spawn_enemy()
    assert scene._enemy.x == original_x
    assert scene._enemy.ground_y == original_y


def test_all_duel_stages_have_coin_goals() -> None:
    for number in range(1, _TOTAL_STAGES + 1):
        spec = duel_stage(number)
        assert spec.number == number
        assert spec.coin_goal > 0


def test_hit_coin_rates_follow_limb_torso_head_ladder() -> None:
    assert c.hit_coins_for_segment("leg_front") == c.HIT_COINS_LIMB
    assert c.hit_coins_for_segment("arm_throw") == c.HIT_COINS_LIMB
    assert c.hit_coins_for_segment("torso") == c.HIT_COINS_TORSO
    assert c.hit_coins_for_segment("head") == c.HIT_COINS_HEAD
    assert c.HIT_COINS_TORSO == c.HIT_COINS_LIMB * 2
    assert c.HIT_COINS_HEAD == c.HIT_COINS_LIMB * 3


def test_weapon_prices_rise_with_damage() -> None:
    ordered = [c.THROW_WEAPONS[k] for k in c.THROW_WEAPON_ORDER]
    assert ordered[0].price == 0
    for cheaper, pricier in zip(ordered, ordered[1:]):
        assert pricier.price > cheaper.price
        assert pricier.damage > cheaper.damage


def test_stage_starts_with_intro_showing_coin_goal() -> None:
    scene = VersusScene()
    assert scene._intro_popup is not None
    assert scene._intro_popup.coin_goal == duel_stage(1).coin_goal
    assert scene.update(1 / 60) is None  # combat frozen


def test_hitting_enemy_awards_segment_coins() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    before = scene.score
    scene._award_hit_coins("torso")
    assert scene.score == before + c.HIT_COINS_TORSO
    assert scene.stage_earned == c.HIT_COINS_TORSO


def test_hit_spawns_floating_coin_above_enemy_head() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    head_x, head_y = scene._enemy.head_center
    scene._award_hit_coins("leg_front")
    assert len(scene._coin_popups) == 1
    popup = scene._coin_popups[0]
    assert popup.amount == c.HIT_COINS_LIMB
    assert popup.x == head_x
    assert popup.y < head_y
    scene._update_coin_popups(0.2)
    assert popup.y < head_y - c.HEAD_R - 8.0
    assert scene._display_coins > 0.0


def test_buy_weapon_spends_coins_and_unlocks() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._coins = 18
    assert scene._try_buy_weapon("bow")
    assert "bow" in scene._owned_weapons
    assert scene._player.weapon_key == "bow"
    assert scene.score == 0
    # Cannot buy something still too expensive.
    assert not scene._try_buy_weapon("broadsword")


def test_kill_without_coin_goal_respawns_enemy() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._stage_earned = 0
    scene._enemy.dead = True
    scene.update(1 / 60)
    assert scene._clear_popup is None
    assert not scene._enemy.dead
    assert scene._need_more_banner > 0.0


def test_kill_with_coin_goal_opens_clear_popup() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._stage_earned = duel_stage(1).coin_goal
    scene._enemy.dead = True
    scene.update(1 / 60)
    assert scene._clear_popup is not None
    assert scene._clear_popup.stage_earned >= duel_stage(1).coin_goal


def test_dismissing_clear_popup_shows_next_stage_intro() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._stage_earned = duel_stage(1).coin_goal
    scene._enemy.dead = True
    scene.update(1 / 60)
    scene._dismiss_stage_clear_popup()
    assert scene._stage_no == 2
    assert scene._intro_popup is not None
    assert scene._intro_popup.coin_goal == duel_stage(2).coin_goal


def test_final_stage_popup_finishes_as_win() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._stage_no = _TOTAL_STAGES
    scene._stage_earned = duel_stage(_TOTAL_STAGES).coin_goal
    scene._enemy.dead = True
    scene.update(1 / 60)
    assert scene._clear_popup is not None
    assert scene._clear_popup.is_final
    assert scene._dismiss_stage_clear_popup() == "win"


def test_cycle_only_owned_weapons() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._owned_weapons = {"spear", "bow"}
    scene._player.weapon_key = "spear"
    scene._cycle_owned_weapon()
    assert scene._player.weapon_key == "bow"
    scene._cycle_owned_weapon()
    assert scene._player.weapon_key == "spear"


def test_intro_space_key_starts_stage() -> None:
    scene = VersusScene()
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
    scene.handle_event(event)
    assert scene._intro_popup is None
