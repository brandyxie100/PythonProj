"""Unit tests for spike spawn and kill logic (no display needed)."""

from __future__ import annotations

import os

# Headless-friendly before pygame import in game
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame as pg

pg.init()

from game import Game, Spike  # noqa: E402
import config as c  # noqa: E402


def test_spike_becomes_lethal_after_warning() -> None:
    warn = 700
    spike = Spike(rect=pg.Rect(0, 0, 20, 28), born_ms=0, warning_ms=warn, warning=True)
    assert spike.is_lethal() is False
    assert spike.update(warn) is True
    assert spike.warning is False
    assert spike.is_lethal() is True


def test_spike_despawns() -> None:
    warn = 700
    spike = Spike(rect=pg.Rect(0, 0, 20, 28), born_ms=0, warning_ms=warn, warning=True)
    assert spike.update(warn + c.SPIKE_LIFE_MS + 1) is False


def test_game_has_ten_levels() -> None:
    g = Game(rng=__import__("random").Random(0))
    assert c.MAX_LEVEL == 10
    assert len(g._layouts) == 10
    assert len(c.LEVEL_SPAWN_MS) == 10
    assert len(c.LEVEL_WARNING_MS) == 10
    assert c.LEVEL_SPAWN_MS[-1] >= 700  # hard, not impossible
    assert c.LEVEL_WARNING_MS[-1] >= 400
    assert g.level_index == 0


def test_soft_kill_respawns() -> None:
    g = Game(rng=__import__("random").Random(1))
    sx, sy = g.layout.spawn
    g.x = 400
    g.soft_kill(now_ms=1000)
    assert g.x == float(sx)
    assert "SPIKE" in g.message


def test_jump_from_ground_sets_upward_velocity() -> None:
    g = Game(rng=__import__("random").Random(2))
    assert g.on_ground is True
    g.request_jump(now_ms=100)
    assert g.vy == c.JUMP_VEL
    assert g.on_ground is False


def test_jump_buffer_fires_after_landing() -> None:
    g = Game(rng=__import__("random").Random(3))
    g.on_ground = False
    g.vy = 100
    g.coyote_until = 0
    g.request_jump(now_ms=50)  # buffered while airborne
    assert g.vy == 100  # not yet
    g.on_ground = True
    g._try_consume_jump(60)
    assert g.vy == c.JUMP_VEL
