"""Tests for Blumgi Merge."""

from __future__ import annotations

import pygame
import pytest

import config as c
from board import Board
from config import stage_spec
from game import Game
from slime import Slime, slime_sprite


@pytest.fixture(autouse=True)
def _pygame_init() -> None:
    pygame.init()
    yield
    pygame.quit()


def test_hundred_stages() -> None:
    assert c.TOTAL_STAGES == 100
    s1 = stage_spec(1)
    s100 = stage_spec(100)
    assert s100.enemy_hp > s1.enemy_hp
    assert stage_spec(10).name.startswith("BOSS")


def test_merge_two_tier1_makes_tier2() -> None:
    board = Board()
    board.cells[0][0] = Slime(1)
    board.dragging = Slime(1)
    board.drag_from = (0, 1)
    pos = board.cell_center(0, 0)
    result = board.end_drag((int(pos[0]), int(pos[1])))
    assert result == "merge"
    assert board.cells[0][0] is not None
    assert board.cells[0][0].tier == 2


def test_sprites_cache_vivid() -> None:
    a = slime_sprite(1, 48)
    b = slime_sprite(1, 48)
    assert a is b
    assert a.get_width() == 48


def test_buy_costs_gold() -> None:
    game = Game()
    game.state = "prep"
    before = game.gold
    game._try_buy()
    assert game.gold == before - c.SLIME_COST
    assert game.board.count() >= 3


def test_fight_starts() -> None:
    game = Game()
    game.state = "prep"
    game._start_fight()
    assert game.state == "fight"
    assert game.battle is not None
