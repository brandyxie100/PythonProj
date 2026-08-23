"""
Cross-mode hybrid recipes, trait fusion, and star-merge multipliers.

Same-type merges use star levels with a >2x attack roll plus random variance.
Different-type fusions always produce a new creature that keeps both parents'
traits and strictly stronger stats.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from .. import constants as c

# Star 2 is always more than double; star 3 is well above triple.
STAR_MULT_BASE: dict[int, float] = {1: 1.0, 2: 2.45, 3: 3.75}
STAR_VARIANCE_MIN: float = -0.08
STAR_VARIANCE_MAX: float = 0.32
FUSION_STAT_BONUS: float = 1.22  # offspring exceed the sum of parents


@dataclass(slots=True)
class HybridConfig:
    """Behavior flags for a HybridPlant (named recipe or dynamic cross)."""

    name: str
    display_name: str
    primary_sprite: str
    tint: tuple[int, int, int]
    health: int = c.PLANT_HEALTH
    shoots: bool = False
    ice: bool = False
    burst: int = 1
    shoot_interval: int = 2000
    bullet_damage: int = c.BULLET_DAMAGE_NORMAL
    makes_sun: bool = False
    sun_interval: int = c.FLOWER_SUN_INTERVAL
    torch: bool = False
    spikes: bool = False
    spike_damage: int = 1
    spike_interval: int = 2000
    mine: bool = False
    mine_arm_ms: int = 8000
    explode: bool = False
    explode_y_range: int = 0
    explode_x_range: int = c.GRID_X_SIZE
    colorkey_white: bool = False
    overlay_sprite: str | None = None


# Base-plant trait sheets used when fusing any pair.
TRAIT_PROFILES: dict[str, HybridConfig] = {
    c.SUNFLOWER: HybridConfig(
        c.SUNFLOWER, "SunFlower", c.SUNFLOWER, (255, 220, 80),
        makes_sun=True, sun_interval=c.FLOWER_SUN_INTERVAL,
    ),
    c.PEASHOOTER: HybridConfig(
        c.PEASHOOTER, "Peashooter", c.PEASHOOTER, (120, 200, 90),
        shoots=True, burst=1, bullet_damage=1,
    ),
    c.SNOWPEASHOOTER: HybridConfig(
        c.SNOWPEASHOOTER, "SnowPea", c.SNOWPEASHOOTER, (140, 210, 255),
        shoots=True, ice=True, burst=1, bullet_damage=1,
    ),
    c.WALLNUT: HybridConfig(
        c.WALLNUT, "Wall-Nut", c.WALLNUT, (200, 170, 90),
        health=c.WALLNUT_HEALTH,
    ),
    c.CHERRYBOMB: HybridConfig(
        c.CHERRYBOMB, "Cherry Bomb", c.CHERRYBOMB, (255, 80, 80),
        explode=True, explode_y_range=1, explode_x_range=c.GRID_X_SIZE,
    ),
    c.REPEATERPEA: HybridConfig(
        c.REPEATERPEA, "Repeater", c.REPEATERPEA, (80, 180, 80),
        shoots=True, burst=2, bullet_damage=1,
    ),
    c.THREEPEASHOOTER: HybridConfig(
        c.THREEPEASHOOTER, "Threepeater", c.THREEPEASHOOTER, (90, 200, 110),
        shoots=True, burst=3, bullet_damage=1,
    ),
    c.POTATOMINE: HybridConfig(
        c.POTATOMINE, "Potato Mine", c.POTATOMINE, (210, 190, 90),
        mine=True, colorkey_white=True, health=c.PLANT_HEALTH + 1,
    ),
    c.SPIKEWEED: HybridConfig(
        c.SPIKEWEED, "Spikeweed", c.SPIKEWEED, (90, 160, 80),
        spikes=True, spike_damage=1, colorkey_white=True,
    ),
    c.JALAPENO: HybridConfig(
        c.JALAPENO, "Jalapeno", c.JALAPENO, (255, 90, 40),
        explode=True, explode_y_range=0, explode_x_range=377, colorkey_white=True,
    ),
    c.PUFFSHROOM: HybridConfig(
        c.PUFFSHROOM, "Puff-Shroom", c.PUFFSHROOM, (180, 140, 200),
        shoots=True, burst=1, shoot_interval=1400, colorkey_white=True,
    ),
    c.SCAREDYSHROOM: HybridConfig(
        c.SCAREDYSHROOM, "Scaredy-Shroom", c.SCAREDYSHROOM, (160, 200, 160),
        shoots=True, burst=1, colorkey_white=True,
    ),
    c.SUNSHROOM: HybridConfig(
        c.SUNSHROOM, "Sun-Shroom", c.SUNSHROOM, (255, 230, 140),
        makes_sun=True, sun_interval=18000, colorkey_white=True,
    ),
    c.CHOMPER: HybridConfig(
        c.CHOMPER, "Chomper", c.CHOMPER, (80, 160, 80),
        health=c.PLANT_HEALTH + 4,
    ),
    c.SQUASH: HybridConfig(
        c.SQUASH, "Squash", c.SQUASH, (80, 180, 80),
        colorkey_white=True, health=c.PLANT_HEALTH + 2,
    ),
    c.ICESHROOM: HybridConfig(
        c.ICESHROOM, "Ice-Shroom", c.ICESHROOM, (160, 220, 255),
        ice=True, explode=True, explode_y_range=2, explode_x_range=c.SCREEN_WIDTH,
        colorkey_white=True,
    ),
    c.HYPNOSHROOM: HybridConfig(
        c.HYPNOSHROOM, "Hypno-Shroom", c.HYPNOSHROOM, (220, 120, 220),
        colorkey_white=True,
    ),
}

# Named showcase hybrids (still built from fused parent traits at spawn time).
HYBRID_CONFIGS: dict[str, HybridConfig] = {
    c.PEA_SUNFLOWER: HybridConfig(
        name=c.PEA_SUNFLOWER,
        display_name="Pea-Sunflower",
        primary_sprite=c.PEASHOOTER,
        overlay_sprite=c.SUNFLOWER,
        tint=(255, 230, 80),
        shoots=True,
        makes_sun=True,
        sun_interval=16000,
        bullet_damage=2,
        health=c.PLANT_HEALTH + 4,
    ),
    c.PEA_GATLING: HybridConfig(
        name=c.PEA_GATLING,
        display_name="Pea Gatling",
        primary_sprite=c.REPEATERPEA,
        overlay_sprite=c.PEASHOOTER,
        tint=(120, 255, 140),
        shoots=True,
        burst=3,
        shoot_interval=1300,
        bullet_damage=2,
        health=c.PLANT_HEALTH + 3,
    ),
    c.SUN_CANNON: HybridConfig(
        name=c.SUN_CANNON,
        display_name="Sun Cannon",
        primary_sprite=c.SUNFLOWER,
        overlay_sprite=c.REPEATERPEA,
        tint=(255, 180, 60),
        shoots=True,
        burst=2,
        shoot_interval=2400,
        bullet_damage=3,
        makes_sun=True,
        sun_interval=17000,
        health=c.PLANT_HEALTH + 4,
    ),
    c.TORCH_NUT: HybridConfig(
        name=c.TORCH_NUT,
        display_name="Torch-Nut",
        primary_sprite=c.WALLNUT,
        overlay_sprite=c.CHERRYBOMB,
        tint=(255, 120, 40),
        health=c.WALLNUT_HEALTH + 18,
        torch=True,
        explode=True,
        explode_y_range=0,
        explode_x_range=c.GRID_X_SIZE,
    ),
    c.FROST_REPEATER: HybridConfig(
        name=c.FROST_REPEATER,
        display_name="Frost Repeater",
        primary_sprite=c.SNOWPEASHOOTER,
        overlay_sprite=c.REPEATERPEA,
        tint=(140, 210, 255),
        shoots=True,
        ice=True,
        burst=2,
        shoot_interval=1600,
        bullet_damage=2,
        health=c.PLANT_HEALTH + 3,
    ),
    c.SPIKE_MINE: HybridConfig(
        name=c.SPIKE_MINE,
        display_name="Spike-Mine",
        primary_sprite=c.SPIKEWEED,
        overlay_sprite=c.POTATOMINE,
        tint=(220, 200, 80),
        colorkey_white=True,
        spikes=True,
        spike_damage=2,
        mine=True,
        mine_arm_ms=8000,
        health=c.PLANT_HEALTH + 6,
    ),
}

_FUSION_PAIRS: list[tuple[set[str], str]] = [
    ({c.PEASHOOTER, c.SUNFLOWER}, c.PEA_SUNFLOWER),
    ({c.PEASHOOTER, c.REPEATERPEA}, c.PEA_GATLING),
    ({c.SUNFLOWER, c.REPEATERPEA}, c.SUN_CANNON),
    ({c.WALLNUT, c.CHERRYBOMB}, c.TORCH_NUT),
    ({c.WALLNUT, c.JALAPENO}, c.TORCH_NUT),
    ({c.SNOWPEASHOOTER, c.REPEATERPEA}, c.FROST_REPEATER),
    ({c.SPIKEWEED, c.POTATOMINE}, c.SPIKE_MINE),
]

FUSION_RECIPES: dict[frozenset[str], str] = {
    frozenset(pair): result for pair, result in _FUSION_PAIRS
}


def recipe_key(name_a: str, name_b: str) -> frozenset[str]:
    """Build an unordered recipe key for two plant names."""
    return frozenset({name_a, name_b})


def lookup_fusion(name_a: str, name_b: str) -> str | None:
    """Return a named hybrid id if this pair is a showcase recipe."""
    if name_a == name_b:
        return None
    return FUSION_RECIPES.get(recipe_key(name_a, name_b))


def is_hybrid(name: str) -> bool:
    """True if name is a named Cross-mode hybrid plant id."""
    return name in HYBRID_CONFIGS


def star_power_mult(star: int, rng: random.Random | None = None) -> float:
    """Combat multiplier for a star merge. Star 2 is always > 2.0."""
    star = max(1, min(c.MAX_PLANT_STAR, int(star)))
    if star <= 1:
        return 1.0
    roller = rng if rng is not None else random
    base = STAR_MULT_BASE[star]
    rolled = base + roller.uniform(STAR_VARIANCE_MIN, STAR_VARIANCE_MAX)
    floor = 2.15 if star == 2 else 3.35
    return round(max(floor, rolled), 2)


def display_name_for(plant_name: str) -> str:
    """Human-readable name for toasts / HUD."""
    if plant_name in HYBRID_CONFIGS:
        return HYBRID_CONFIGS[plant_name].display_name
    if plant_name in TRAIT_PROFILES:
        return TRAIT_PROFILES[plant_name].display_name
    return plant_name


def traits_for(name: str, plant_obj: object | None = None) -> HybridConfig:
    """Resolve a trait sheet from a hybrid instance, named hybrid, or base plant."""
    cfg = getattr(plant_obj, "config", None)
    if isinstance(cfg, HybridConfig):
        return cfg
    if name in HYBRID_CONFIGS:
        return HYBRID_CONFIGS[name]
    if name in TRAIT_PROFILES:
        return TRAIT_PROFILES[name]
    return HybridConfig(name, display_name_for(name), name, (200, 200, 200))


def _blend_tint(
    a: tuple[int, int, int], b: tuple[int, int, int]
) -> tuple[int, int, int]:
    return tuple((a[i] + b[i]) // 2 for i in range(3))  # type: ignore[return-value]


def fuse_configs(
    left: HybridConfig,
    right: HybridConfig,
    rng: random.Random | None = None,
) -> HybridConfig:
    """
    Combine two trait sheets into a stronger offspring.

    All boolean abilities are kept (OR). Numeric stats exceed both parents.
    """
    roller = rng if rng is not None else random
    named = lookup_fusion(left.name, right.name)
    if named and named in HYBRID_CONFIGS:
        showcase = HYBRID_CONFIGS[named]
        display = showcase.display_name
        name = named
        primary = showcase.primary_sprite
        overlay = showcase.overlay_sprite
        tint = showcase.tint
    else:
        name = f"Cross_{left.name}_{right.name}"
        display = f"{left.display_name} × {right.display_name}"
        # Prefer the tankier (or shooting) parent as the body.
        if right.health > left.health:
            primary, overlay = right.primary_sprite, left.primary_sprite
        else:
            primary, overlay = left.primary_sprite, right.primary_sprite
        tint = _blend_tint(left.tint, right.tint)

    health = int(round((left.health + right.health) * FUSION_STAT_BONUS))
    health += roller.randint(0, 4)
    health = max(health, max(left.health, right.health) + 3)

    dmg_l, dmg_r = left.bullet_damage, right.bullet_damage
    damage = int(round((dmg_l + dmg_r) * FUSION_STAT_BONUS))
    damage += roller.randint(0, 1)
    damage = max(damage, max(dmg_l, dmg_r) + 1)

    spike = max(left.spike_damage, right.spike_damage)
    if left.spikes and right.spikes:
        spike += 1
    spike = max(spike, max(left.spike_damage, right.spike_damage))

    burst = max(left.burst, right.burst)
    if left.shoots and right.shoots:
        burst = max(burst + 1, burst)

    interval = min(left.shoot_interval, right.shoot_interval)
    interval = max(400, int(interval * 0.82))
    sun_iv = min(left.sun_interval, right.sun_interval)
    sun_iv = max(4000, int(sun_iv * 0.82))

    explode_x = max(left.explode_x_range, right.explode_x_range)
    explode_y = max(left.explode_y_range, right.explode_y_range)
    mine_arm = min(left.mine_arm_ms, right.mine_arm_ms) if (
        left.mine or right.mine
    ) else 8000

    return HybridConfig(
        name=name,
        display_name=display,
        primary_sprite=primary,
        overlay_sprite=overlay if overlay != primary else None,
        tint=tint,
        health=health,
        shoots=left.shoots or right.shoots,
        ice=left.ice or right.ice,
        burst=burst,
        shoot_interval=interval,
        bullet_damage=damage,
        makes_sun=left.makes_sun or right.makes_sun,
        sun_interval=sun_iv,
        torch=left.torch or right.torch or (
            (left.explode or right.explode) and (
                "WallNut" in (left.primary_sprite, right.primary_sprite)
                or left.health >= c.WALLNUT_HEALTH
                or right.health >= c.WALLNUT_HEALTH
            )
        ),
        spikes=left.spikes or right.spikes,
        spike_damage=spike,
        spike_interval=min(left.spike_interval, right.spike_interval),
        mine=left.mine or right.mine,
        mine_arm_ms=mine_arm,
        explode=left.explode or right.explode,
        explode_y_range=explode_y,
        explode_x_range=explode_x,
        colorkey_white=left.colorkey_white or right.colorkey_white,
    )


def fuse_plant_names(
    name_a: str,
    name_b: str,
    plant_a: object | None = None,
    plant_b: object | None = None,
    rng: random.Random | None = None,
) -> HybridConfig:
    """Build a fusion config from two plant ids / instances."""
    return fuse_configs(traits_for(name_a, plant_a), traits_for(name_b, plant_b), rng)
