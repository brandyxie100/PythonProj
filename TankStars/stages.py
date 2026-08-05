"""Stage definitions for the 20-stage Tank Stars campaign."""

from __future__ import annotations

from dataclasses import dataclass

import config as c


@dataclass(frozen=True, slots=True)
class StageSpec:
    """Difficulty knobs for one stage."""

    number: int
    name: str
    enemy_hp: int
    enemy_count: int  # 1 or 2 foes
    wind_scale: float
    ai_skill: float  # 0..1 (higher = better aim)
    blast_bonus: float  # scales explosion FX / crater


STAGE_NAMES: tuple[str, ...] = (
    "Dusty Duel",
    "Rolling Hills",
    "Crosswind Creek",
    "Broken Bridge",
    "Sunset Ridge",
    "Twin Peaks",
    "Iron Valley",
    "Storm Front",
    "Crater Lake",
    "High Ground",
    "Sandstorm",
    "Echo Canyon",
    "Night Watch",
    "Fortress Gap",
    "Thunder Pass",
    "Last Outpost",
    "Scorched Earth",
    "Siege Line",
    "Final Approach",
    "Champion Arena",
)


def stage_spec(number: int) -> StageSpec:
    """Build escalating specs for stages 1..20."""
    if number < 1 or number > c.MAX_STAGES:
        raise ValueError(f"stage {number} out of range 1..{c.MAX_STAGES}")
    idx = number - 1
    # Second tank appears from stage 8 onward.
    enemies = 1 if number < 8 else 2
    enemy_hp = int(c.TANK_MAX_HP * (0.75 + idx * 0.04))
    if enemies == 2:
        enemy_hp = int(enemy_hp * 0.85)
    return StageSpec(
        number=number,
        name=STAGE_NAMES[idx],
        enemy_hp=enemy_hp,
        enemy_count=enemies,
        wind_scale=0.35 + idx * 0.035,
        ai_skill=min(0.95, 0.35 + idx * 0.03),
        blast_bonus=1.0 + idx * 0.04,
    )
