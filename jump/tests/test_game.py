"""Smoke tests for JUMP core mechanics."""

from __future__ import annotations

import math

import pygame
import pytest

import config as c
from game import Game
from level import Obstacle, build_level
from menu import MainMenu
from player import Player


@pytest.fixture(autouse=True)
def _pygame_init() -> None:
    pygame.init()
    yield
    pygame.quit()


def test_jump_height_is_two_blocks() -> None:
    expected = -math.sqrt(2.0 * c.GRAVITY * c.CUBE_SIZE * 2.0) * 1.08
    assert c.JUMP_VELOCITY == pytest.approx(expected)
    assert c.JUMP_HEIGHT == pytest.approx(c.CUBE_SIZE * 2.0)
    # Simulated apex clears ~2 block heights.
    p = Player()
    start = p.y
    p.jump()
    min_y = p.y
    for _ in range(300):
        p.update(1 / 60, [], holding=False)
        min_y = min(min_y, p.y)
        if p.on_ground and p.y >= start - 1.0:
            break
    assert (start - min_y) >= c.CUBE_SIZE * 1.95


def test_jump_only_when_grounded() -> None:
    p = Player()
    assert p.on_ground
    p.jump()
    assert not p.on_ground
    assert p.vy == pytest.approx(c.JUMP_VELOCITY)
    p.vy = -100.0
    p.jump()
    assert p.vy == pytest.approx(-100.0)


def test_level_has_spikes_portals_and_finish() -> None:
    obstacles, portals, finish_x = build_level()
    assert finish_x > 1000
    assert any(o.kind == "spike" for o in obstacles)
    assert any(o.kind == "block" for o in obstacles)
    assert any(p.mode == "ship" for p in portals)
    assert any(p.mode == "cube" for p in portals)


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
    if game._jump_held and game.player.on_ground:
        game.player.jump()
    assert not game.player.on_ground
    assert game.player.vy == pytest.approx(c.JUMP_VELOCITY)


def test_fall_gravity_is_stronger_than_rise() -> None:
    assert c.FALL_GRAVITY > c.GRAVITY


def test_ship_hold_climbs() -> None:
    p = Player()
    p.set_mode("ship")
    start_y = p.y
    for _ in range(20):
        p.update(1 / 60, [], holding=True)
    assert p.y < start_y


def test_ship_hits_ceiling_and_dies() -> None:
    game = Game()
    game.player.set_mode("ship")
    game.player.y = c.CEILING_Y - 2
    game._resolve_collisions()
    assert game.state == "dead"


def test_portal_switches_to_ship() -> None:
    game = Game()
    ship_portal = next(p for p in game.portals if p.mode == "ship")
    game.camera_x = ship_portal.x - c.PLAYER_SCREEN_X
    game._check_portals()
    assert game.player.mode == "ship"
    assert ship_portal.triggered


def test_menu_play_on_space() -> None:
    menu = MainMenu()
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    assert menu.choice == "play"


def test_esc_requests_menu() -> None:
    game = Game()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert game.request_menu
