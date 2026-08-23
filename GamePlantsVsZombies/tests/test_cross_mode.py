"""Unit tests for Cross-mode recipes, stars, and map merge helpers."""

from __future__ import annotations

import json
from pathlib import Path

from source import constants as c
from source.component.hybrids import (
    FUSION_RECIPES,
    HYBRID_CONFIGS,
    TRAIT_PROFILES,
    display_name_for,
    lookup_fusion,
    recipe_key,
    star_power_mult,
)
from source.component.map import Map


def test_fusion_pea_sunflower() -> None:
    assert lookup_fusion(c.PEASHOOTER, c.SUNFLOWER) == c.PEA_SUNFLOWER
    assert lookup_fusion(c.SUNFLOWER, c.PEASHOOTER) == c.PEA_SUNFLOWER


def test_fusion_unordered_and_same_type_none() -> None:
    assert lookup_fusion(c.WALLNUT, c.CHERRYBOMB) == c.TORCH_NUT
    assert lookup_fusion(c.WALLNUT, c.JALAPENO) == c.TORCH_NUT
    assert lookup_fusion(c.PEASHOOTER, c.PEASHOOTER) is None
    # Unnamed pairs still fuse via fuse_configs (no showcase id)
    assert lookup_fusion(c.PEASHOOTER, c.WALLNUT) is None


def test_star_power_mult_more_than_double() -> None:
    rng = __import__("random").Random(0)
    for _ in range(20):
        m2 = star_power_mult(2, rng)
        assert m2 > 2.0
        m3 = star_power_mult(3, rng)
        assert m3 > 3.0
    assert star_power_mult(1) == 1.0
    assert star_power_mult(99, rng) <= 4.2


def test_any_pair_fuses_and_keeps_traits() -> None:
    from source.component.hybrids import fuse_plant_names

    rng = __import__("random").Random(1)
    cfg = fuse_plant_names(c.PEASHOOTER, c.WALLNUT, rng=rng)
    pea = TRAIT_PROFILES[c.PEASHOOTER]
    nut = TRAIT_PROFILES[c.WALLNUT]
    assert cfg.shoots is True
    assert cfg.health > nut.health
    assert cfg.bullet_damage > pea.bullet_damage
    assert "×" in cfg.display_name or "Pea" in cfg.display_name


def test_fusion_stats_exceed_parents() -> None:
    from source.component.hybrids import fuse_plant_names, TRAIT_PROFILES

    rng = __import__("random").Random(2)
    cfg = fuse_plant_names(c.SUNFLOWER, c.SNOWPEASHOOTER, rng=rng)
    sun = TRAIT_PROFILES[c.SUNFLOWER]
    snow = TRAIT_PROFILES[c.SNOWPEASHOOTER]
    assert cfg.makes_sun and cfg.shoots and cfg.ice
    assert cfg.health > max(sun.health, snow.health)
    assert cfg.bullet_damage > max(sun.bullet_damage, snow.bullet_damage)


def test_named_recipe_still_special() -> None:
    from source.component.hybrids import fuse_plant_names

    cfg = fuse_plant_names(c.PEASHOOTER, c.SUNFLOWER, rng=__import__("random").Random(3))
    assert cfg.name == c.PEA_SUNFLOWER
    assert cfg.shoots and cfg.makes_sun



def test_all_recipes_have_configs() -> None:
    for hybrid in FUSION_RECIPES.values():
        assert hybrid in HYBRID_CONFIGS
        assert HYBRID_CONFIGS[hybrid].display_name

    assert recipe_key(c.SPIKEWEED, c.POTATOMINE) == recipe_key(
        c.POTATOMINE, c.SPIKEWEED
    )


def test_display_name() -> None:
    assert "Pea" in display_name_for(c.PEA_SUNFLOWER)
    assert display_name_for(c.PEASHOOTER) == c.PEASHOOTER


def test_map_show_plant_or_merge() -> None:
    m = Map(c.GRID_X_LEN, c.GRID_Y_LEN)
    # Empty cell works for both APIs
    x, y = m.getMapGridPos(2, 1)
    assert m.showPlant(x, y) is not None
    assert m.showPlantOrMerge(x, y) is not None
    # Occupied: classic showPlant rejects; merge API allows
    m.setMapGridType(2, 1, c.MAP_EXIST)
    assert m.showPlant(x, y) is None
    assert m.showPlantOrMerge(x, y) is not None
    assert m.isOccupied(2, 1)


def test_cross_maps_exist() -> None:
    root = Path(__file__).resolve().parents[1] / "source" / "data" / "map"
    for i in range(1, c.MAX_CROSS_LEVEL + 1):
        path = root / f"cross_{i}.json"
        assert path.exists(), path
        data = json.loads(path.read_text())
        assert c.ZOMBIE_LIST in data
        assert c.INIT_SUN_NAME in data
        assert c.CARD_POOL in data
        names = {z["name"] for z in data[c.ZOMBIE_LIST]}
        # At least one hybrid zombie appears somewhere in the campaign
        if i >= 1:
            assert names


def test_cross_campaign_has_hybrid_zombies() -> None:
    root = Path(__file__).resolve().parents[1] / "source" / "data" / "map"
    all_names: set[str] = set()
    for i in range(1, c.MAX_CROSS_LEVEL + 1):
        data = json.loads((root / f"cross_{i}.json").read_text())
        all_names |= {z["name"] for z in data[c.ZOMBIE_LIST]}
    assert c.EMBER_CONE_ZOMBIE in all_names
    assert c.FLAG_PAPER_ZOMBIE in all_names
    assert c.CONE_BUCKET_ZOMBIE in all_names
