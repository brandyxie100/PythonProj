"""Tests for ragdoll anatomy and damage handling."""

from __future__ import annotations

import pymunk
import pytest

import config as c
from ragdoll import Ragdoll


@pytest.fixture
def space() -> pymunk.Space:
    """Empty pymunk space for ragdoll construction."""
    return pymunk.Space()


def test_ragdoll_builds_ten_body_parts(space: pymunk.Space) -> None:
    """Ragdoll should create all planned anatomical segments."""
    doll = Ragdoll(space, 200, 400, team="player", colour=c.PLAYER_COL)
    assert len(doll.bodies) == len(Ragdoll.PART_NAMES)
    assert set(doll.bodies.keys()) == set(Ragdoll.PART_NAMES)


def test_take_hit_reduces_health_and_staggers(space: pymunk.Space) -> None:
    """Large hits should subtract health and enter stagger state."""
    doll = Ragdoll(space, 200, 400, team="enemy", colour=c.ENEMY_COL)
    before = doll.health
    doll.take_hit("torso", c.STAGGER_DAMAGE_THRESHOLD, pymunk.Vec2d(100, 0))
    assert doll.health < before
    assert doll.stagger_frames > 0


def test_take_hit_applies_knockback(space: pymunk.Space) -> None:
    """Impulse should change body velocity."""
    doll = Ragdoll(space, 200, 400, team="enemy", colour=c.ENEMY_COL)
    torso = doll.torso
    torso.velocity = (0, 0)
    doll.take_hit("torso", 5.0, pymunk.Vec2d(250, 0))
    assert torso.velocity.x != 0.0
