"""Tests for the versus-duel fighter damage and death rules."""

from __future__ import annotations

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
