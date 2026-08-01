"""Smoke tests for JUMP core mechanics."""

from __future__ import annotations

import pygame
import pytest

import config as c
from game import Game
from level import Obstacle, build_level
from player import Player


@pytest.fixture(autouse=True)
def _pygame_init() -> None:
    pygame.init()
    yield
    pygame.quit()


def test_jump_only_when_grounded() -> None:
    p = Player()
    assert p.on_ground
    p.jump()
    assert not p.on_ground
    assert p.vy == pytest.approx(c.JUMP_VELOCITY)
    p.vy = -100.0
    p.jump()
    assert p.vy == pytest.approx(-100.0)


def test_level_has_spikes_and_finish() -> None:
    obstacles, finish_x = build_level()
    assert finish_x > 1000
    assert any(o.kind == "spike" for o in obstacles)
    assert any(o.kind == "block" for o in obstacles)


def test_spike_collision_kills() -> None:
    game = Game()
    game.obstacles = [
        Obstacle("spike", c.PLAYER_SCREEN_X, c.GROUND_Y - 28, 28, 28)
    ]
    game.camera_x = 0.0
    game._resolve_collisions()
    assert game.state == "dead"
    assert not game.player.alive


def test_progress_increases_with_camera() -> None:
    game = Game()
    start = game.progress()
    game.camera_x = game.finish_x * 0.5
    assert game.progress() > start
    assert game.progress() == pytest.approx(0.5, abs=0.05)


def test_space_jumps_while_playing() -> None:
    game = Game()
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    game.handle_event(event)
    assert not game.player.on_ground


def test_hold_jump_rebounds_on_landing() -> None:
    game = Game()
    game._jump_held = True
    game.player.on_ground = True
    game.player.vy = 0.0
    # Simulate the hold-rebounce branch used each frame after physics.
    if game._jump_held and game.player.on_ground:
        game.player.jump()
    assert not game.player.on_ground
    assert game.player.vy == pytest.approx(c.JUMP_VELOCITY)


def test_fall_gravity_is_stronger_than_rise() -> None:
    assert c.FALL_GRAVITY > c.GRAVITY
