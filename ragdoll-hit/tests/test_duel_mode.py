"""Tests for versus-duel stage economy, shop, and pass rules."""

from __future__ import annotations

import pygame

import config as c
from duel_fighter import DuelFighter, EmbeddedWeapon
from duel_mode import VersusScene, _TOTAL_STAGES, duel_stage


def _embed(scene: VersusScene) -> EmbeddedWeapon:
    enemy = scene._enemy
    return EmbeddedWeapon("spear", enemy.x, enemy.ground_y, 0.0)


def test_enemy_respawn_uses_different_weapon() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    weapons = [scene._enemy.weapon_key]
    for _ in range(40):
        scene._spawn_enemies()
        weapons.append(scene._enemy.weapon_key)
    for previous, current in zip(weapons, weapons[1:]):
        assert previous != current


def test_enemy_respawns_at_same_pillar_location() -> None:
    scene = VersusScene()
    original_x = scene._enemy.x
    original_y = scene._enemy.ground_y
    scene._spawn_enemies()
    assert scene._enemy.x == original_x
    assert scene._enemy.ground_y == original_y


def test_all_duel_stages_have_coin_goals() -> None:
    assert _TOTAL_STAGES == 30
    for number in range(1, _TOTAL_STAGES + 1):
        spec = duel_stage(number)
        assert spec.number == number
        assert spec.coin_goal > 0
        assert spec.dual_enemies == (number >= c.DUEL_DUAL_ENEMY_FROM)


def test_latter_half_stages_spawn_two_enemies() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._load_stage(c.DUEL_DUAL_ENEMY_FROM, show_intro=False)
    assert len(scene._enemies) == 2
    assert scene._enemies[1].pillar_top_y < scene._enemies[0].pillar_top_y


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


def test_defense_gear_prices_rise_with_protection() -> None:
    helms = [c.HELMETS[k] for k in c.HELMET_ORDER]
    shields = [c.SHIELDS[k] for k in c.SHIELD_ORDER]
    for cheaper, pricier in zip(helms, helms[1:]):
        assert pricier.price > cheaper.price
        assert pricier.damage_factor < cheaper.damage_factor
    for cheaper, pricier in zip(shields, shields[1:]):
        assert pricier.price > cheaper.price
        assert pricier.damage_factor < cheaper.damage_factor


def test_stage_starts_with_intro_showing_coin_goal() -> None:
    scene = VersusScene()
    assert scene._intro_popup is not None
    assert scene._intro_popup.coin_goal == duel_stage(1).coin_goal
    assert scene.update(1 / 60) is None  # combat frozen


def test_hitting_enemy_awards_segment_coins() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    before = scene.score
    scene._award_hit_coins("torso", scene._enemy)
    assert scene.score == before + c.HIT_COINS_TORSO
    assert scene.stage_earned == c.HIT_COINS_TORSO


def test_hit_spawns_floating_coin_above_enemy_head() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    head_x, head_y = scene._enemy.head_center
    scene._award_hit_coins("leg_front", scene._enemy)
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
    assert not scene._try_buy_weapon("broadsword")


def test_defense_shop_hidden_before_stage_six() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    assert scene._stage_no < c.DUEL_DEFENSE_SHOP_FROM
    assert not scene._defense_shop_unlocked
    scene._load_stage(c.DUEL_DEFENSE_SHOP_FROM, show_intro=False)
    assert scene._defense_shop_unlocked


def test_buy_helmet_reduces_head_lethality() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._coins = 55
    assert scene._try_buy_helmet("leather_helm")
    fighter = scene._player
    assert fighter.helmet_key == "leather_helm"
    fighter.apply_hit(
        "head",
        0.05,
        EmbeddedWeapon("spear", fighter.x, fighter.ground_y, 0.0),
    )
    assert not fighter.dead  # helmet blocks instant lethal while intact


def test_shield_reduces_torso_damage() -> None:
    bare = DuelFighter("player", 100.0, 452.0, 1, "spear")
    tank = DuelFighter("player", 200.0, 452.0, 1, "spear")
    tank.equip_shield("wood_shield")
    embed = EmbeddedWeapon("spear", 0.0, 0.0, 0.0)
    bare.apply_hit("torso", 0.2, embed)
    tank.apply_hit("torso", 0.2, EmbeddedWeapon("spear", 0.0, 0.0, 0.0))
    assert tank.segments["torso"].redness < bare.segments["torso"].redness


def test_kill_without_coin_goal_respawns_enemy() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._stage_earned = 0
    for enemy in scene._enemies:
        enemy.dead = True
    scene.update(1 / 60)
    assert scene._clear_popup is None
    assert not scene._all_enemies_dead()
    assert scene._need_more_banner > 0.0


def test_kill_with_coin_goal_opens_clear_popup() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._stage_earned = duel_stage(1).coin_goal
    for enemy in scene._enemies:
        enemy.dead = True
    scene.update(1 / 60)
    assert scene._clear_popup is not None
    assert scene._clear_popup.stage_earned >= duel_stage(1).coin_goal


def test_dismissing_clear_popup_shows_next_stage_intro() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._stage_earned = duel_stage(1).coin_goal
    for enemy in scene._enemies:
        enemy.dead = True
    scene.update(1 / 60)
    scene._dismiss_stage_clear_popup()
    assert scene._stage_no == 2
    assert scene._intro_popup is not None
    assert scene._intro_popup.coin_goal == duel_stage(2).coin_goal


def test_final_stage_popup_finishes_as_win() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    scene._load_stage(_TOTAL_STAGES, show_intro=False)
    scene._stage_earned = duel_stage(_TOTAL_STAGES).coin_goal
    for enemy in scene._enemies:
        enemy.dead = True
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
