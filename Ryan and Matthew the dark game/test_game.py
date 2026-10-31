from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame as pg

from main import (
    DUNGEON,
    BOSS_DAMAGE,
    BOSS_HP,
    DungeonGame,
    HOTBAR_SIZE,
    POTION_HEAL,
    SCREEN_H,
    SCREEN_W,
    ZOMBIE_DAMAGE,
    ZOMBIE_HP,
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
        self.assertEqual(boss.hp, BOSS_HP)
        self.assertEqual(boss.max_hp, BOSS_HP)
        self.assertGreater(BOSS_HP, 67)
        self.assertGreater(ZOMBIE_HP, 30)

    def test_zombie_and_boss_deal_increased_contact_damage(self) -> None:
        game = DungeonGame()
        zombie = next(enemy for enemy in game.enemies if not enemy.boss)
        zombie.x, zombie.y = game.x + 0.5, game.y
        game.update(0.01, pg.key.get_pressed())
        self.assertEqual(game.health, 100 - ZOMBIE_DAMAGE)

        game.health = 100
        game.enemies = [enemy for enemy in game.enemies if enemy.boss]
        boss = game.enemies[0]
        boss.x, boss.y = game.x + 0.5, game.y
        game.update(0.01, pg.key.get_pressed())
        self.assertEqual(game.health, 100 - BOSS_DAMAGE)

    def test_defeated_zombie_drops_collectible_weapon_or_armor(self) -> None:
        game = DungeonGame()
        zombie = next(enemy for enemy in game.enemies if not enemy.boss)
        for enemy in game.enemies:
            if enemy is not zombie:
                enemy.alive = False
        zombie.x, zombie.y = game.x + 1, game.y

        for _ in range(3):
            game.attack_timer = 0
            self.assertTrue(game.attack())

        self.assertFalse(zombie.alive)
        self.assertEqual(len(game.loot_drops), 1)
        drop = game.loot_drops[0]
        self.assertIn(drop.loot.kind, ("weapon", "armor"))
        drop.x, drop.y = game.x, game.y
        game._collect_loot()
        self.assertEqual(game.loot_drops, [])
        if drop.loot.kind == "weapon":
            self.assertEqual(game.weapon_name, drop.loot.name)
            self.assertEqual(game.weapon_bonus, drop.loot.value)
        else:
            self.assertEqual(game.armor_name, drop.loot.name)
            self.assertEqual(game.armor_value, drop.loot.value)

    def test_armor_reduces_zombie_damage_and_boss_has_guaranteed_weapon_drop(self) -> None:
        game = DungeonGame()
        game.armor_value = 4
        zombie = next(enemy for enemy in game.enemies if not enemy.boss)
        zombie.x, zombie.y = game.x + 0.5, game.y
        game.update(0.01, pg.key.get_pressed())
        self.assertEqual(game.health, 100 - (ZOMBIE_DAMAGE - 4))

        boss = next(enemy for enemy in game.enemies if enemy.boss)
        game._drop_loot(boss)
        boss_drop = game.loot_drops[-1]
        self.assertEqual(boss_drop.loot.kind, "weapon")
        self.assertEqual(boss_drop.loot.name, "67's Cleaver")
        self.assertGreater(boss_drop.loot.value, 6)

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
        hits_needed = (BOSS_HP + 9) // 10
        for _ in range(hits_needed):
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

    def test_held_item_draws_for_blade_and_potion(self) -> None:
        from main import draw_held_item

        screen = pg.Surface((SCREEN_W, SCREEN_H))
        game = DungeonGame()
        game.select_slot(0)
        draw_held_item(screen, game)
        game.select_slot(1)
        draw_held_item(screen, game)
        game.select_slot(2)
        draw_held_item(screen, game)
        self.assertEqual(screen.get_size(), (SCREEN_W, SCREEN_H))


if __name__ == "__main__":
    unittest.main()
