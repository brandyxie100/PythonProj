"""Tests for the versus-duel fighter damage and death rules."""

from __future__ import annotations

import pytest

from duel_fighter import DuelFighter, EmbeddedWeapon


def _fighter() -> DuelFighter:
    return DuelFighter(team="enemy", x=500.0, ground_y=452.0, facing=-1, weapon_key="spear")


def _embed(fighter: DuelFighter) -> EmbeddedWeapon:
    return EmbeddedWeapon("spear", fighter.x, fighter.ground_y, 0.0)


def test_head_hit_is_instantly_lethal() -> None:
    fighter = _fighter()
    fighter.apply_hit("head", 0.05, _embed(fighter))
    assert fighter.dead


def test_single_body_hit_is_not_lethal() -> None:
    fighter = _fighter()
    fighter.apply_hit("torso", 0.5, _embed(fighter))
    assert not fighter.dead


def test_over_eighty_percent_red_kills() -> None:
    fighter = _fighter()
    # Saturate torso + both legs + both arms without ever touching the head.
    for name in ("torso", "leg_front", "leg_back", "arm_throw", "arm_off"):
        fighter.apply_hit(name, 1.0, _embed(fighter))
    assert fighter.body_red_ratio() >= 0.8
    assert fighter.dead


def test_damage_multipliers_scale_by_segment() -> None:
    fighter = _fighter()
    base = 0.1
    fighter.apply_hit("leg_front", base, _embed(fighter))
    fighter.apply_hit("torso", base, _embed(fighter))
    # Head hit is lethal, but redness is still recorded before death is set.
    fighter.apply_hit("head", base, _embed(fighter))
    assert fighter.segments["leg_front"].redness == pytest.approx(base)  # 1x
    assert fighter.segments["torso"].redness == pytest.approx(base * 2)  # 2x
    assert fighter.segments["head"].redness == pytest.approx(base * 3)  # 3x


def test_hit_test_detects_head_and_torso() -> None:
    fighter = DuelFighter("player", 300.0, 452.0, 1, "spear")
    assert fighter.hit_test(fighter.head_center) == "head"
    assert fighter.hit_test(fighter.neck) in {"torso", "head"}


def test_reset_health_clears_damage() -> None:
    fighter = _fighter()
    fighter.apply_hit("torso", 0.5, _embed(fighter))
    fighter.reset_health()
    assert fighter.body_red_ratio() == 0.0
    assert not fighter.embedded
    assert not fighter.dead


def test_strafe_moves_on_pillar() -> None:
    fighter = DuelFighter("player", 320.0, 452.0, 1, "spear")
    fighter.apply_move_axis(1, 0.016)
    fighter.update(0.1)
    assert fighter.x > fighter.anchor_x
    assert not fighter.falling


def test_stepping_past_pillar_edge_starts_fall() -> None:
    import config as c

    fighter = DuelFighter("player", 320.0, 452.0, 1, "spear")
    fighter.x = fighter.anchor_x + c.DUEL_PILLAR_HALF_WIDTH + 1.0
    fighter.update(0.016)
    assert fighter.falling


def test_falling_off_screen_is_fatal() -> None:
    import config as c

    fighter = DuelFighter("player", 320.0, 452.0, 1, "spear")
    fighter._begin_fall()
    fighter.ground_y = c.SCREEN_H + 100.0
    fighter.update(0.016)
    assert fighter.dead


def test_reset_health_returns_to_pillar_center() -> None:
    fighter = DuelFighter("player", 320.0, 452.0, 1, "spear")
    fighter.x = 380.0
    fighter._begin_fall()
    fighter.reset_health()
    assert fighter.x == fighter.anchor_x
    assert not fighter.falling
    assert fighter.ground_y == fighter.pillar_top_y


def test_strafe_advances_walk_phase() -> None:
    fighter = DuelFighter("player", 320.0, 452.0, 1, "spear")
    before = fighter.walk_phase
    fighter.apply_move_axis(1, 0.016)
    fighter.update(0.05)
    assert fighter.walk_phase > before


def test_apply_hit_starts_flinch_animation() -> None:
    fighter = DuelFighter("player", 320.0, 452.0, 1, "spear")
    fighter.apply_hit("torso", 0.2, _embed(fighter))
    assert fighter.hit_flinch_timer > 0.0
    assert fighter.hit_flinch_dir == -1.0


def test_safe_knockback_moves_but_stays_on_pillar() -> None:
    import config as c

    fighter = DuelFighter("enemy", 900.0, 452.0, -1, "spear")
    start_x = fighter.x
    moved = False
    for _ in range(40):
        fighter.x = start_x
        fighter.apply_safe_knockback()
        max_offset = c.DUEL_PILLAR_HALF_WIDTH * c.DUEL_HIT_KNOCKBACK_SAFE
        assert abs(fighter.x - fighter.anchor_x) <= max_offset + 1e-6
        assert not fighter.falling
        if abs(fighter.x - start_x) > 0.5:
            moved = True
    assert moved


def test_safe_knockback_shifts_embedded_weapons() -> None:
    fighter = DuelFighter("enemy", 900.0, 452.0, -1, "spear")
    embed = _embed(fighter)
    fighter.embedded.append(embed)
    before = embed.x
    fighter.apply_safe_knockback()
    assert embed.x == pytest.approx(before + (fighter.x - fighter.anchor_x))


def test_falling_advances_fall_phase() -> None:
    fighter = DuelFighter("player", 320.0, 452.0, 1, "spear")
    fighter._begin_fall()
    before = fighter.fall_phase
    fighter.update(0.05)
    assert fighter.fall_phase > before


def test_cycle_weapon_triggers_swap_animation() -> None:
    fighter = DuelFighter("player", 320.0, 452.0, 1, "spear")
    fighter.cycle_weapon()
    assert fighter.weapon_key != "spear"
    assert fighter.weapon_swap_timer > 0.0
