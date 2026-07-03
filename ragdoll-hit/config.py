"""Ragdoll Hit — shared constants and weapon definitions.

All tuneable gameplay values live here so nothing is hard-coded elsewhere.
"""

from __future__ import annotations

from typing import TypedDict

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
FPS: int = 60
SCREEN_W: int = 1024
SCREEN_H: int = 600
TITLE: str = "Ragdoll Hit"

# ---------------------------------------------------------------------------
# Physics (pymunk space uses Y-up; draw flips to pygame Y-down)
# ---------------------------------------------------------------------------
GRAVITY: tuple[float, float] = (0.0, -1200.0)
PHYSICS_DT: float = 1.0 / FPS
PHYSICS_SUBSTEPS: int = 3

# Collision type IDs
COL_TERRAIN: int = 1
COL_BODY: int = 2
COL_WEAPON: int = 3

# ---------------------------------------------------------------------------
# Ragdoll anatomy (pixels, pymunk units == screen pixels when drawn)
# ---------------------------------------------------------------------------
HEAD_R: float = 14.0
TORSO_W: float = 22.0
TORSO_H: float = 36.0
UPPER_LIMB: float = 22.0
LOWER_LIMB: float = 20.0
LIMB_THICK: float = 8.0

PART_MASS_HEAD: float = 1.2
PART_MASS_TORSO: float = 4.0
PART_MASS_LIMB: float = 1.0

MAX_HEALTH: float = 100.0
STAGGER_DAMAGE_THRESHOLD: float = 8.0
STAGGER_DURATION_F: int = 45
GET_UP_DURATION_F: int = 30

MOVE_FORCE: float = 2800.0
JUMP_IMPULSE: float = 420.0
GROUND_FRICTION: float = 0.9
GROUND_ELASTICITY: float = 0.05

# Torso stabilizer (keeps ragdoll upright until staggered)
STABILIZER_STIFFNESS: float = 8000.0
STABILIZER_DAMPING: float = 400.0

# Joint limits (radians)
ELBOW_MIN: float = -2.4
ELBOW_MAX: float = 0.2
KNEE_MIN: float = -0.2
KNEE_MAX: float = 2.2

# ---------------------------------------------------------------------------
# Damage
# ---------------------------------------------------------------------------
MIN_IMPACT_SPEED: float = 80.0
DAMAGE_VELOCITY_SCALE: float = 0.08

# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------
AI_APPROACH_RANGE: float = 280.0
AI_ATTACK_RANGE: float = 95.0
AI_ATTACK_COOLDOWN_F: int = 50
AI_RECOVER_F: int = 35

# ---------------------------------------------------------------------------
# Terrain (pygame Y coordinates)
# ---------------------------------------------------------------------------
GROUND_Y: int = 540
PLATFORM_RECT: tuple[int, int, int, int] = (380, 420, 220, 24)

# Spawn positions (pygame x, pygame y)
PLAYER_SPAWN: tuple[float, float] = (180.0, 480.0)
ENEMY_SPAWN: tuple[float, float] = (820.0, 480.0)

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
BG_TOP: tuple[int, int, int] = (18, 18, 22)
BG_BOT: tuple[int, int, int] = (32, 32, 38)
PLAYER_COL: tuple[int, int, int] = (240, 240, 245)
ENEMY_COL: tuple[int, int, int] = (220, 80, 80)
JOINT_COL: tuple[int, int, int] = (200, 200, 210)
GROUND_COL: tuple[int, int, int] = (70, 72, 78)
PLATFORM_COL: tuple[int, int, int] = (90, 92, 100)
PLATFORM_EDGE: tuple[int, int, int] = (160, 165, 175)
HEALTH_BG: tuple[int, int, int] = (40, 40, 45)
HEALTH_PLAYER: tuple[int, int, int] = (60, 200, 90)
HEALTH_ENEMY: tuple[int, int, int] = (220, 60, 60)
UI_TEXT: tuple[int, int, int] = (235, 235, 240)


class WeaponStats(TypedDict):
    """Stats for a weapon type."""

    label: str
    length: float
    mass: float
    thickness: float
    damage_mult: float
    swing_speed: float
    swing_duration_f: int
    colour: tuple[int, int, int]


WEAPON_DATA: dict[str, WeaponStats] = {
    "staff": {
        "label": "Staff",
        "length": 72.0,
        "mass": 1.8,
        "thickness": 6.0,
        "damage_mult": 1.0,
        "swing_speed": 9.0,
        "swing_duration_f": 18,
        "colour": (220, 180, 60),
    },
}

DEFAULT_WEAPON: str = "staff"
