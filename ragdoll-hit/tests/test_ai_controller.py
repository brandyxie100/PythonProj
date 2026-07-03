"""Tests for enemy AI state machine."""

from __future__ import annotations

import config as c
from ai_controller import AIController, AIState


def test_update_far_target_approaches() -> None:
    """Enemy should move when player is outside attack range."""
    ai = AIController()
    move, jump, attack = ai.update(self_x=100.0, target_x=500.0, distance=500.0)
    assert move == 1
    assert attack is False


def test_update_in_attack_range_swings() -> None:
    """Enemy should attack when close enough and off cooldown."""
    ai = AIController()
    _, _, attack = ai.update(self_x=300.0, target_x=320.0, distance=c.AI_ATTACK_RANGE - 10)
    assert attack is True
    assert ai.state == AIState.RECOVER


def test_update_recover_waits_before_reapproach() -> None:
    """Recover state should idle briefly after attacking."""
    ai = AIController()
    ai.update(self_x=300.0, target_x=320.0, distance=50.0)
    move, _, attack = ai.update(self_x=300.0, target_x=320.0, distance=50.0)
    assert move == 0
    assert attack is False
