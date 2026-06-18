"""Unit tests for loot chest reward application."""

from __future__ import annotations

import os
import sys
import unittest

# Allow imports from stickman_battle package root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

pygame.init()

import config as c
from entities import ChestPickup, Player, apply_chest_reward, chest_reward_label


class TestChestRewards(unittest.TestCase):
    """Verify chest grants exactly one reward per collection."""

    def _make_player(self) -> Player:
        """Create a player with known starting state."""
        return Player(x=100.0, y=500.0, health=100.0, weapon_name="sword")

    def test_chest_reward_label_bow(self) -> None:
        """Bow label includes arrow count."""
        self.assertEqual(chest_reward_label("bow"), f"Bow x{c.BOW_ARROWS_PER_SET}")

    def test_chest_reward_label_grenades(self) -> None:
        """Grenade label shows bonus count."""
        self.assertEqual(
            chest_reward_label("grenades"),
            f"+{c.CHEST_GRENADE_BONUS} Grenades",
        )

    def test_apply_bow_equips_arrows(self) -> None:
        """Bow reward switches weapon and loads arrows."""
        player = self._make_player()
        apply_chest_reward(player, "bow")
        self.assertEqual(player.weapon_name, "bow")
        self.assertEqual(player._arrows_left, c.BOW_ARROWS_PER_SET)

    def test_apply_ak47_equips_rounds(self) -> None:
        """AK-47 reward loads magazine rounds."""
        player = self._make_player()
        apply_chest_reward(player, "ak47")
        self.assertEqual(player.weapon_name, "ak47")
        self.assertEqual(player._rounds_left, c.AK47_ROUNDS_PER_PICKUP)

    def test_apply_melee_weapon(self) -> None:
        """Melee reward switches active weapon."""
        player = self._make_player()
        apply_chest_reward(player, "hammer")
        self.assertEqual(player.weapon_name, "hammer")
        self.assertEqual(player._stored_melee, "hammer")

    def test_add_grenades_respects_cap(self) -> None:
        """Grenade bonus cannot exceed per-match maximum."""
        player = self._make_player()
        player.grenades_left = c.GRENADES_PER_MATCH - 1
        apply_chest_reward(player, "grenades")
        self.assertEqual(player.grenades_left, c.GRENADES_PER_MATCH)

    def test_chest_collect_once(self) -> None:
        """Chest deactivates after first successful collection."""
        player = self._make_player()
        player.x = 200.0
        player.y = 500.0
        chest = ChestPickup(200.0, 500.0, "sword")
        self.assertTrue(chest.try_collect(player))
        self.assertFalse(chest.active)
        self.assertFalse(chest.try_collect(player))


if __name__ == "__main__":
    unittest.main()
