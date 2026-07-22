"""Tests that stage levels 1-6 use the new weapon variants."""

from __future__ import annotations

import config as c
from terrain import level_config


def test_all_levels_use_new_weapon_variants() -> None:
    allowed = set(c.WEAPON_ORDER)
    for level in range(1, 7):
        cfg = level_config(level)
        for spawn, _pos in cfg.enemy_spawns:
            assert spawn.weapon_name in allowed, (
                f"Level {level} still uses old weapon {spawn.weapon_name!r}"
            )


def test_weapon_order_matches_detailed_variants() -> None:
    assert c.WEAPON_ORDER == (
        "spear",
        "trident",
        "broadsword",
        "bow",
        "axe",
        "javelin",
    )
