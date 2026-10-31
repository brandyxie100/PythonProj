from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame as pg

from main import (
    DUNGEON,
    DungeonGame,
    HOTBAR_SIZE,
    POTION_HEAL,
    SCREEN_H,
    SCREEN_W,
    cast_ray,
    draw_hotbar,
    draw_world,
)


class DungeonGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pg.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pg.quit()

    def test_dungeon_is_enclosed_and_rectangular(self) -> None:
        self.assertTrue(all(len(row) == len(DUNGEON[0]) for row in DUNGEON))
        self.assertTrue(all(cell == "#" for cell in DUNGEON[0]))
        self.assertTrue(all(cell == "#" for cell in DUNGEON[-1]))
        self.assertTrue(all(row[0] == row[-1] == "#" for row in DUNGEON))

    def test_game_starts_with_zombies_and_67_boss(self) -> None:
        game = DungeonGame()
        zombies = [enemy for enemy in game.living_enemies if not enemy.boss]
        boss = next(enemy for enemy in game.living_enemies if enemy.boss)
        self.assertEqual(len(zombies), 3)
        self.assertEqual(boss.name, "67")
        self.assertEqual(boss.hp, 67)
        self.assertEqual(boss.max_hp, 67)

    def test_ray_finds_wall_ahead(self) -> None:
        game = DungeonGame()
        self.assertAlmostEqual(cast_ray(game, 0), 3.5)

    def test_boss_can_be_defeated_and_exit_unlocks(self) -> None:
        game = DungeonGame()
        boss = next(enemy for enemy in game.enemies if enemy.boss)
        for enemy in game.enemies:
            if enemy is not boss:
                enemy.alive = False
        boss.x, boss.y = game.x + 1, game.y
        for _ in range(7):
            game.attack_timer = 0
            self.assertTrue(game.attack())
        self.assertFalse(boss.alive)
        game.x, game.y = 7.5, 13.5
        game.update(0.01, pg.key.get_pressed())
        self.assertTrue(game.won)

    def test_first_person_scene_renders(self) -> None:
        screen = pg.Surface((SCREEN_W, SCREEN_H))
        game = DungeonGame()
        font = pg.font.SysFont("consolas", 17)
        big_font = pg.font.SysFont("consolas", 44, bold=True)
        draw_world(screen, game, font, big_font)
        self.assertEqual(screen.get_size(), (SCREEN_W, SCREEN_H))

    def test_hotbar_slots_select_and_healing_potion_works(self) -> None:
        game = DungeonGame()
        game.select_slot(1)
        game.health = 55
        starting_potions = game.health_potions

        self.assertTrue(game.use_selected_item())
        self.assertEqual(game.health, min(100, 55 + POTION_HEAL))
        self.assertEqual(game.health_potions, starting_potions - 1)
        self.assertEqual(HOTBAR_SIZE, 5)

    def test_potion_is_not_consumed_at_full_health_or_when_empty(self) -> None:
        game = DungeonGame()
        game.select_slot(1)
        starting_potions = game.health_potions

        self.assertFalse(game.use_selected_item())
        self.assertEqual(game.health_potions, starting_potions)

        game.health = 50
        game.health_potions = 0
        self.assertFalse(game.use_selected_item())
        self.assertEqual(game.health, 50)

    def test_hotbar_draws_with_selected_slot_and_item_count(self) -> None:
        screen = pg.Surface((SCREEN_W, SCREEN_H))
        game = DungeonGame()
        game.select_slot(1)
        draw_hotbar(screen, game, pg.font.SysFont("consolas", 17))
        self.assertEqual(screen.get_size(), (SCREEN_W, SCREEN_H))


if __name__ == "__main__":
    unittest.main()
