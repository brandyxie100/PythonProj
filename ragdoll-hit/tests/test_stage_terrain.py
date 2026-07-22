"""Tests for elaborate stage terrain layouts."""

from __future__ import annotations

from terrain import level_config


def test_each_level_has_rich_walkable_terrain() -> None:
    """Later levels should offer denser platforms and ramps for vertical combat."""
    min_platforms = {1: 4, 2: 6, 3: 7, 4: 8, 5: 10, 6: 12}
    min_ramps = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
    for level, need_p in min_platforms.items():
        arena = level_config(level).arena
        assert len(arena.platforms) >= need_p, f"Level {level} needs more platforms"
        assert len(arena.ramps) >= min_ramps[level], f"Level {level} needs more ramps"


def test_platforms_are_above_floor_and_on_screen() -> None:
    for level in range(1, 7):
        arena = level_config(level).arena
        for plat in arena.platforms:
            assert plat.top < arena.floor_y
            assert plat.left >= 0
            assert plat.right <= 1180
            assert plat.top > 80


def test_enemy_spawns_sit_on_walkable_surfaces() -> None:
    """Enemy feet should land near a platform top or the floor."""
    for level in range(1, 7):
        cfg = level_config(level)
        for _spawn, (x, y) in cfg.enemy_spawns:
            foot = y + 38.0  # LEG_LEN
            surfaces = cfg.arena._surface_candidates(x)
            assert any(abs(foot - s) < 3.0 for s in surfaces), (
                f"Level {level} enemy at x={x} not on a surface"
            )
