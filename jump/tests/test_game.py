"""Smoke tests for JUMP core mechanics."""

from __future__ import annotations

import math

import pygame
import pytest

import config as c
from game import Game
from level import Obstacle, LEVEL_NAME, build_level
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
    p = Player()
    start = p.y
    p.jump()
    min_y = p.y
    for _ in range(300):
        p.update(1 / 60, [], [], holding=False)
        min_y = min(min_y, p.y)
        if p.on_ground and p.y >= start - 1.0:
            break
    assert (start - min_y) >= c.CUBE_SIZE * 1.95


def test_jump_only_when_grounded() -> None:
    p = Player()
    p.jump()
    assert not p.on_ground
    assert p.vy == pytest.approx(c.JUMP_VELOCITY)
    assert p.air_jumps_left == 1


def test_cube_double_jump_mid_air() -> None:
    p = Player()
    p.jump()
    assert p.air_jumps_left == 1
    p.vy = 50.0  # falling
    p.jump()
    assert p.air_jumps_left == 0
    assert p.vy == pytest.approx(c.DOUBLE_JUMP_VELOCITY)
    # Third press does nothing to velocity.
    p.vy = 80.0
    p.jump()
    assert p.vy == pytest.approx(80.0)


def test_level_name() -> None:
    assert LEVEL_NAME == "Stereo Madness"


def test_level_is_stereo_madness() -> None:
    obstacles, portals, orbs, finish_x = build_level()
    assert finish_x > 2000
    assert any(o.kind == "spike" for o in obstacles)
    assert any(o.kind == "yellow" for o in orbs)
    modes = [p.mode for p in portals]
    assert modes[0] == "ship"
    assert modes[-1] == "cube"
    assert "ship" in modes and "cube" in modes


def test_yellow_orb_boosts_mid_air() -> None:
    game = Game()
    from level import Orb

    game.orbs = [
        Orb("yellow", c.PLAYER_SCREEN_X + 8, c.GROUND_Y - 80)
    ]
    game.player.on_ground = False
    game.player.y = c.GROUND_Y - 100
    game.player.vy = 100.0
    game.player.jump()  # arms click buffer
    game._try_orbs()
    assert game.orbs[0].used
    assert game.player.vy == pytest.approx(c.JUMP_VELOCITY)


def test_player_hitbox_smaller_than_sprite() -> None:
    p = Player()
    assert p.hitbox.width < p.rect.width
    assert p.hitbox.height < p.rect.height


def test_ship_portal_is_purple() -> None:
    assert c.PORTAL_SHIP == (210, 70, 220)


def test_spike_collision_kills() -> None:
    game = Game()
    # Place a wide spike centered on the player's shrunk hitbox.
    game.obstacles = [
        Obstacle("spike", c.PLAYER_SCREEN_X - 4, c.GROUND_Y - 28, 44, 28)
    ]
    game.camera_x = 0.0
    game._resolve_collisions()
    assert game.state == "dead"


def test_progress_increases_with_camera() -> None:
    game = Game()
    game.camera_x = game.finish_x * 0.5
    assert game.progress() == pytest.approx(0.5, abs=0.05)


def test_ship_hold_flies_up_release_flies_down() -> None:
    p = Player()
    p.set_mode("ship")
    start = p.y
    for _ in range(25):
        p.update(1 / 60, [], [], holding=True)
    assert p.y < start  # up
    assert p.vy < 0.0
    # Coast through remaining upward speed, then gravity wins.
    for _ in range(90):
        p.update(1 / 60, [], [], holding=False)
    assert p.vy > 0.0  # flying down


def test_ship_hits_ceiling_and_dies() -> None:
    game = Game()
    game.player.set_mode("ship")
    game.player.y = c.CEILING_Y - 2
    game._resolve_collisions()
    assert game.state == "dead"


def test_purple_portal_switches_to_ship() -> None:
    game = Game()
    ship_portal = next(p for p in game.portals if p.mode == "ship")
    game.camera_x = ship_portal.x - c.PLAYER_SCREEN_X
    game._check_portals()
    assert game.player.mode == "ship"


def test_ball_inverts_gravity() -> None:
    p = Player()
    p.set_mode("ball")
    assert p.gravity_dir == 1.0
    p.jump()
    assert p.gravity_dir == -1.0


def test_ufo_jumps_mid_air() -> None:
    p = Player()
    p.set_mode("ufo")
    p.on_ground = False
    p.vy = 200.0
    p.jump()
    assert p.vy == pytest.approx(c.UFO_JUMP_VELOCITY)


def test_menu_play_on_space() -> None:
    menu = MainMenu()
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    assert menu.choice == "play"


def test_esc_requests_menu() -> None:
    game = Game()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert game.request_menu
