"""Smoke tests for Tank Stars."""

from __future__ import annotations

import pygame
import pytest

import config as c
from blast import Blast, BlastSystem
from game import Game
from stages import stage_spec
from tanks import Shell, Tank
from terrain import Terrain


@pytest.fixture(autouse=True)
def _pygame_init() -> None:
    pygame.init()
    yield
    pygame.quit()


def test_twenty_stages_defined() -> None:
    assert c.MAX_STAGES == 20
    s1 = stage_spec(1)
    s20 = stage_spec(20)
    assert s1.enemy_count == 1
    assert s20.enemy_count == 2
    assert s20.ai_skill > s1.ai_skill


def test_terrain_crater_lowers_surface() -> None:
    t = Terrain(1, seed=42)
    x = 400
    before = t.height_at(x)
    t.carve_crater(float(x), before, 40)
    assert t.height_at(x) > before


def test_blast_spawns_many_particles() -> None:
    b = Blast(200, 300, power=1.0)
    assert len(b.particles) >= c.BLAST_SPARK_COUNT
    sys = BlastSystem()
    sys.spawn(100, 100, power=1.2)
    assert len(sys.blasts) == 1
    for _ in range(90):
        sys.update(0.05)
    assert sys.blasts == []


def test_shell_hits_ground() -> None:
    terrain = Terrain(1, seed=1)
    y0 = terrain.height_at(300) - 5
    shell = Shell(300, y0, 0, 200, team="player")
    hit = False
    for _ in range(60):
        if shell.update(1 / 60, 0.0, terrain):
            hit = True
            break
    assert hit
    assert not shell.alive


def test_game_starts_on_title() -> None:
    game = Game()
    assert game.state == "title"
    assert game.stage_no == 1
    assert len(game.enemies) == 1


def test_stage_8_has_two_enemies() -> None:
    game = Game()
    game._load_stage(8)
    assert len(game.enemies) == 2


def test_fire_enters_wait_and_spawns_blast_on_impact() -> None:
    game = Game()
    game.state = "playing"
    game.player.power = 40
    game.player.aim = 0.9
    game._fire(game.player)
    assert game.turn == "wait"
    assert game.shells
    # Drop shell into ground immediately
    shell = game.shells[0]
    shell.x = 400
    shell.y = game.terrain.height_at(400) + 2
    shell.vx = 0
    shell.vy = 0
    game._update_shells(0.016)
    assert shell.exploded
    assert game.blasts.blasts
