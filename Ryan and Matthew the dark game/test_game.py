from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame as pg

from main import (
    BOSS3_HP,
    DUNGEON,
    BOSS_DAMAGE,
    BOSS_HP,
    BOSS_LOOT,
    CAMPAIGN_KEYS,
    DUNGEON_FIVE,
    DUNGEON_FOUR,
    DUNGEON_THREE,
    DUNGEON_TWO,
    DEPTH_ZOMBIE_LOOT,
    DungeonGame,
    GOLD_SWORD_DAMAGE,
    GOLD_SWORD_LOOT,
    HOTBAR_SIZE,
    POTION_HEAL,
    RESPAWN_DELAY,
    ROOM_MAPS,
    SCREEN_H,
    SCREEN_W,
    VOID_BLADE_LOOT,
    ZOMBIE_DAMAGE,
    ZOMBIE_HP,
    WARDEN_HP,
    cast_ray,
    draw_hotbar,
    draw_menu,
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
        for dungeon in (DUNGEON, DUNGEON_TWO, DUNGEON_THREE, DUNGEON_FOUR, DUNGEON_FIVE):
            self.assertTrue(all(len(row) == len(dungeon[0]) for row in dungeon))
            self.assertTrue(all(cell == "#" for cell in dungeon[0]))
            self.assertTrue(all(cell == "#" for cell in dungeon[-1]))
            self.assertTrue(all(row[0] == row[-1] == "#" for row in dungeon))

    def test_room_catalog_and_campaign_include_boss3(self) -> None:
        self.assertGreaterEqual(len(ROOM_MAPS), 5)
        self.assertEqual(CAMPAIGN_KEYS[-1], "abyss")
        self.assertEqual(BOSS3_HP, 1000)

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

    def test_death_freezes_player_and_enemies_until_respawn(self) -> None:
        game = DungeonGame()
        game.select_slot(1)
        game.health = 40
        game._begin_death()
        player_position = (game.x, game.y)
        enemy_positions = [(enemy.x, enemy.y) for enemy in game.living_enemies]
        potions = game.health_potions

        self.assertEqual(game.respawn_timer, RESPAWN_DELAY)
        game.move(forward=1, sideways=0, dt=1)
        self.assertFalse(game.attack())
        self.assertFalse(game.use_selected_item())
        game.update(4.99, pg.key.get_pressed())
        self.assertEqual((game.x, game.y), player_position)
        self.assertEqual(
            [(enemy.x, enemy.y) for enemy in game.living_enemies],
            enemy_positions,
        )
        self.assertEqual(game.health_potions, potions)
        self.assertEqual(game.health, 0)

    def test_respawn_after_five_seconds_reloads_same_stage_and_keeps_gear(self) -> None:
        game = DungeonGame()
        game._load_stage(1)
        game.weapon_name = "Gold Sword"
        game.weapon_bonus = GOLD_SWORD_DAMAGE
        game.armor_name = "Bone Guard"
        game.armor_value = 4
        game.health_potions = 2
        game.health = 0
        game._begin_death()
        game.update(RESPAWN_DELAY - 0.01, pg.key.get_pressed())
        self.assertEqual(game.health, 0)
        self.assertEqual(game.stage_index, 1)

        game.update(0.01, pg.key.get_pressed())
        self.assertEqual(game.health, 100)
        self.assertEqual(game.stage_index, 1)
        self.assertEqual((game.x, game.y), (2.5, 1.5))
        self.assertEqual(game.weapon_name, "Gold Sword")
        self.assertEqual(game.weapon_bonus, GOLD_SWORD_DAMAGE)
        self.assertEqual(game.armor_name, "Bone Guard")
        self.assertEqual(game.armor_value, 4)
        self.assertEqual(game.health_potions, 2)
        self.assertEqual(len(game.living_enemies), 5)

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
        game.rng.random = lambda: 0.99  # type: ignore[method-assign]
        game._drop_loot(boss)
        boss_drop = game.loot_drops[-1]
        self.assertEqual(boss_drop.loot.kind, "weapon")
        self.assertEqual(boss_drop.loot.name, BOSS_LOOT.name)
        self.assertGreater(boss_drop.loot.value, 6)

    def test_ray_finds_wall_ahead(self) -> None:
        game = DungeonGame()
        self.assertAlmostEqual(cast_ray(game, 0), 3.5)

    def test_clearing_first_dungeon_advances_to_level_two(self) -> None:
        game = DungeonGame()
        game.weapon_name = "Iron Sword"
        game.weapon_bonus = 12
        for enemy in game.enemies:
            enemy.alive = False
        game.update(0.01, pg.key.get_pressed())
        self.assertEqual(game.stage_index, 1)
        self.assertEqual(game.stage_name, "Warden's Depths")
        self.assertEqual(len(game.living_enemies), 5)
        self.assertEqual(game.weapon_name, "Iron Sword")
        self.assertFalse(game.won)

    def test_clearing_level_two_advances_to_boss3_abyss(self) -> None:
        game = DungeonGame()
        game.start_campaign()
        game._load_stage(1)
        for enemy in game.enemies:
            enemy.alive = False
        game.update(0.01, pg.key.get_pressed())
        self.assertFalse(game.won)
        self.assertEqual(game.stage_index, 2)
        self.assertEqual(game.room_key, "abyss")
        boss = next(enemy for enemy in game.living_enemies if enemy.boss)
        self.assertEqual(boss.name, "Boss 3")
        self.assertEqual(boss.hp, BOSS3_HP)
        self.assertEqual(boss.kind, "boss3")

    def test_clearing_boss3_wins_campaign(self) -> None:
        game = DungeonGame()
        game.start_campaign()
        game._load_stage(2)
        for enemy in game.enemies:
            enemy.alive = False
        game.update(0.01, pg.key.get_pressed())
        self.assertTrue(game.won)

    def test_single_room_mode_wins_without_campaign_advance(self) -> None:
        game = DungeonGame()
        game.start_room("crossroads")
        self.assertFalse(game.campaign_mode)
        for enemy in game.enemies:
            enemy.alive = False
        game.update(0.01, pg.key.get_pressed())
        self.assertTrue(game.won)
        self.assertEqual(game.room_key, "crossroads")

    def test_boss3_grants_void_blade(self) -> None:
        game = DungeonGame()
        game.start_room("abyss")
        boss = next(enemy for enemy in game.enemies if enemy.kind == "boss3")
        for enemy in game.enemies:
            if enemy is not boss:
                enemy.alive = False
        boss.x, boss.y = game.x + 1, game.y
        game.weapon_bonus = 30
        hits = (BOSS3_HP + 39) // 40
        for _ in range(hits):
            game.attack_timer = 0
            game.attack()
        self.assertFalse(boss.alive)
        self.assertEqual(game.weapon_name, VOID_BLADE_LOOT.name)
        self.assertEqual(game.weapon_bonus, VOID_BLADE_LOOT.value)

    def test_menu_draws(self) -> None:
        screen = pg.Surface((SCREEN_W, SCREEN_H))
        draw_menu(screen, pg.font.SysFont("consolas", 17), pg.font.SysFont("consolas", 44, bold=True), 0)
        self.assertEqual(screen.get_size(), (SCREEN_W, SCREEN_H))

    def test_level_two_boss_has_100_health_and_drops_gold_sword(self) -> None:
        game = DungeonGame()
        game._load_stage(1)
        boss = next(enemy for enemy in game.enemies if enemy.boss)
        for enemy in game.enemies:
            if enemy is not boss:
                enemy.alive = False
        self.assertEqual(boss.hp, WARDEN_HP)
        self.assertEqual(boss.max_hp, 600)

        game.weapon_name = "Iron Sword"
        game.weapon_bonus = 12
        boss.x, boss.y = game.x + 1, game.y
        hits_needed = (WARDEN_HP + 21) // 22
        for _ in range(hits_needed):
            game.attack_timer = 0
            self.assertTrue(game.attack())

        self.assertFalse(boss.alive)
        self.assertEqual(game.weapon_name, GOLD_SWORD_LOOT.name)
        self.assertEqual(game.weapon_bonus, GOLD_SWORD_DAMAGE)
        self.assertIn("replaces your Iron Sword", game.message)

    def test_level_two_zombies_drop_stronger_equipment(self) -> None:
        game = DungeonGame()
        game._load_stage(1)
        zombie = next(enemy for enemy in game.enemies if not enemy.boss)

        for _ in range(20):
            game._drop_loot(zombie)

        dropped_names = {drop.loot.name for drop in game.loot_drops}
        self.assertEqual(dropped_names, {loot.name for loot in DEPTH_ZOMBIE_LOOT})
        self.assertEqual(
            next(loot.value for loot in DEPTH_ZOMBIE_LOOT if loot.kind == "weapon"),
            30,
        )
        self.assertGreater(
            next(loot.value for loot in DEPTH_ZOMBIE_LOOT if loot.kind == "armor"),
            4,
        )

    def test_selected_equipped_weapon_attacks_and_weapon_name_selects_appearance(self) -> None:
        game = DungeonGame()
        zombie = next(enemy for enemy in game.enemies if not enemy.boss)
        for enemy in game.enemies:
            if enemy is not zombie:
                enemy.alive = False
        zombie.x, zombie.y = game.x + 1, game.y
        game.weapon_name = "Gold Sword"
        game.weapon_bonus = GOLD_SWORD_DAMAGE
        game.select_slot(2)

        self.assertTrue(game.use_selected_item())
        self.assertEqual(zombie.hp, ZOMBIE_HP - 15 - GOLD_SWORD_DAMAGE)

        from main import draw_held_item

        screen = pg.Surface((SCREEN_W, SCREEN_H))
        draw_held_item(screen, game)
        self.assertEqual(screen.get_size(), (SCREEN_W, SCREEN_H))

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

    def test_minecraft_style_sword_surface_builds(self) -> None:
        from main import build_minecraft_sword_surface

        for name in ("Crypt Blade", "Iron Sword", "Diamond Sword", "Gold Sword"):
            surf = build_minecraft_sword_surface(name, pixel=4)
            self.assertEqual(surf.get_size(), (64, 64))
            # Opaque pixels exist (sword is not blank)
            self.assertTrue(any(surf.get_at((x, y)).a > 0 for x in range(64) for y in range(64)))


if __name__ == "__main__":
    unittest.main()
