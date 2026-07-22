"""Shared configuration for the stickman battle game."""

from __future__ import annotations

from dataclasses import dataclass

# Display
SCREEN_W: int = 1180
SCREEN_H: int = 680
FPS: int = 60
TITLE: str = "Ragdoll Hit - Stickman Stage Mode"

# Physics
GRAVITY: float = 1900.0
MOVE_SPEED: float = 260.0
MOVE_ACCEL: float = 1700.0
MOVE_FRICTION: float = 0.86
JUMP_SPEED: float = 760.0 
MAX_FALL_SPEED: float = 1300.0
MAX_JUMPS: int = 2  # normal jump + one extra mid-air jump

# Stickman geometry
HEAD_R: float = 11.0
TORSO_LEN: float = 46.0
ARM_LEN: float = 34.0
LEG_LEN: float = 38.0
BODY_RADIUS: float = 15.0
HEAD_OFFSET_Y: float = TORSO_LEN + HEAD_R + 2.0

# Limb controls
ARM_ROTATE_SPEED: float = 4.3  # radians per second
LEG_ROTATE_SPEED: float = 3.0
MIN_ARM_ANGLE: float = -3.14
MAX_ARM_ANGLE: float = 3.14
MAX_LEG_POSE: float = 0.75

# Attack controls
ATTACK_SWEEP_RAD: float = 6.283185  # 360 degrees
ATTACK_SWING_TIME: float = 0.2
ATTACK_COOLDOWN: float = 0.2
# Hit knockback — strong enough to visibly launch fighters off platforms.
ATTACK_HIT_KNOCKBACK_X: float = 480.0
ATTACK_HIT_KNOCKBACK_Y: float = 420.0
ATTACK_HIT_STUN: float = 0.38  # seconds of reduced control after being hit
ATTACK_HIT_STUN_MOVE_SCALE: float = 0.15  # movement authority while stunned

# Stickman body animation (melee stage mode)
WALK_BOB_AMP: float = 3.2  # vertical bounce while walking (pixels)
WALK_ARM_SWING: float = 0.35  # off-arm counter-swing while walking (radians)
HIT_FLINCH_LEAN: float = 0.55  # torso lean away from impact while stunned
AIR_LEG_TUCK: float = 0.55  # how much legs tuck when airborne / falling
ATTACK_OFF_ARM_KICK: float = 0.7  # off-arm recoil during a weapon swing
WEAPON_SWAP_FLASH: float = 0.18  # brief raise when cycling weapons

# Health and economy
PLAYER_MAX_HEALTH: float = 140.0
BASE_ENEMY_HEALTH: float = 70.0
COIN_REWARD_PER_LEVEL: tuple[int, ...] = (30, 45, 65, 90, 120, 160)

# Colors
BG_TOP: tuple[int, int, int] = (24, 26, 33)
BG_BOTTOM: tuple[int, int, int] = (40, 44, 58)
GROUND_COLOR: tuple[int, int, int] = (66, 73, 84)
PLATFORM_COLOR: tuple[int, int, int] = (88, 100, 120)
RAMP_COLOR: tuple[int, int, int] = (120, 132, 156)
OBSTACLE_COLOR: tuple[int, int, int] = (190, 70, 70)
UI_TEXT: tuple[int, int, int] = (235, 238, 248)
UI_FAINT: tuple[int, int, int] = (178, 183, 196)
PLAYER_BLUE: tuple[int, int, int] = (76, 155, 255)
ENEMY_RED: tuple[int, int, int] = (238, 82, 82)
ENEMY_YELLOW: tuple[int, int, int] = (240, 212, 90)
ENEMY_BLUE: tuple[int, int, int] = (96, 188, 255)
WHITE: tuple[int, int, int] = (248, 248, 250)


@dataclass(frozen=True, slots=True)
class WeaponStats:
    """Stats describing weapon handling and damage."""

    name: str
    length: float
    thickness: int
    damage: float
    cooldown: float
    sweep_time: float
    color: tuple[int, int, int]


WEAPONS: dict[str, WeaponStats] = {
    "spear": WeaponStats(
        name="Spear",
        length=64.0,
        thickness=4,
        damage=16.0,
        cooldown=0.18,
        sweep_time=0.2,
        color=(208, 214, 226),
    ),
    "trident": WeaponStats(
        name="Trident",
        length=58.0,
        thickness=5,
        damage=22.0,
        cooldown=0.28,
        sweep_time=0.24,
        color=(150, 210, 225),
    ),
    "broadsword": WeaponStats(
        name="Broadsword",
        length=56.0,
        thickness=6,
        damage=24.0,
        cooldown=0.26,
        sweep_time=0.22,
        color=(228, 228, 238),
    ),
    "bow": WeaponStats(
        name="Bow",
        length=50.0,
        thickness=3,
        damage=14.0,
        cooldown=0.16,
        sweep_time=0.18,
        color=(212, 180, 120),
    ),
    "axe": WeaponStats(
        name="Axe",
        length=48.0,
        thickness=7,
        damage=28.0,
        cooldown=0.34,
        sweep_time=0.28,
        color=(176, 182, 192),
    ),
    "javelin": WeaponStats(
        name="Javelin",
        length=68.0,
        thickness=3,
        damage=15.0,
        cooldown=0.17,
        sweep_time=0.19,
        color=(198, 204, 220),
    ),
}

WEAPON_ORDER: tuple[str, ...] = (
    "spear",
    "trident",
    "broadsword",
    "bow",
    "axe",
    "javelin",
)


# ---------------------------------------------------------------------------
# Versus projectile-duel mode
# ---------------------------------------------------------------------------
# Bright silhouette style referencing the throwing/archery stick-figure image.
DUEL_BG_TOP: tuple[int, int, int] = (152, 228, 122)
DUEL_BG_BOTTOM: tuple[int, int, int] = (112, 194, 94)
DUEL_FIGHTER_BLACK: tuple[int, int, int] = (24, 26, 28)
DUEL_PILLAR_COLOR: tuple[int, int, int] = (58, 64, 72)
DUEL_PILLAR_TOP: tuple[int, int, int] = (86, 94, 104)
DAMAGE_RED: tuple[int, int, int] = (240, 38, 30)
DAMAGE_GLOW: tuple[int, int, int] = (255, 60, 45)  # halo drawn behind wounds
DAMAGE_COLOR_GAIN: float = 1.5  # how fast a segment saturates to red visually

# Projectile flight
PROJECTILE_GRAVITY: float = 820.0
THROW_POWER_MIN: float = 620.0
THROW_POWER_MAX: float = 1360.0
THROW_CHARGE_RATE: float = 820.0  # power units gained per second while charging
THROW_COOLDOWN: float = 0.4  # seconds between throws
THROW_ANIM_TIME: float = 0.34  # seconds of throwing-arm swing animation
DUEL_HIT_FLINCH_TIME: float = 0.32  # recoil pose after a projectile lands
DUEL_WALK_STRIDE: float = 0.48  # leg stride amplitude while strafing
DUEL_WALK_BOB: float = 2.8  # vertical bob while strafing (pixels)
DUEL_CHARGE_CROUCH: float = 6.0  # hip drop while charging a throw (pixels)
DUEL_FALL_SPIN: float = 5.5  # limb tumble speed after leaving the pillar
DUEL_WEAPON_SWAP_TIME: float = 0.2  # brief raise when cycling throw weapons

# Pillar dodging (Versus Duel Mode)
DUEL_MOVE_SPEED: float = 210.0  # horizontal dodge speed on the pillar top
DUEL_PILLAR_HALF_WIDTH: float = 48.0  # safe standing range from pillar center
DUEL_FALL_GRAVITY: float = 1600.0  # gravity after stepping off the pillar

# Aiming (elevation above horizontal, radians; positive points upward)
AIM_MIN_ELEV: float = -0.1
AIM_MAX_ELEV: float = 1.48
AIM_ROTATE_SPEED: float = 1.15

# Body-segment damage / death rules
BODY_RED_DEATH_RATIO: float = 0.8  # >80% weighted redness triggers death
HEAD_LETHAL: bool = True  # any direct head wound is fatal

# Per-segment damage multipliers (limbs are the 1x baseline).
LIMB_DAMAGE_MULT: float = 1.0
TORSO_DAMAGE_MULT: float = 2.0  # torso takes double limb damage
HEAD_DAMAGE_MULT: float = 3.0  # head takes triple limb damage


@dataclass(frozen=True, slots=True)
class ThrowWeaponStats:
    """Stats for a thrown/launched projectile weapon."""

    name: str
    damage: float  # redness (0..1) added to the struck body segment
    length: float  # drawn length in pixels
    thickness: int
    speed_scale: float  # multiplies launch power
    color: tuple[int, int, int]


THROW_WEAPONS: dict[str, ThrowWeaponStats] = {
    "spear": ThrowWeaponStats("Spear", 0.34, 60.0, 4, 1.16, (208, 214, 226)),
    "trident": ThrowWeaponStats("Trident", 0.44, 54.0, 6, 1.0, (150, 210, 225)),
    "broadsword": ThrowWeaponStats("Broadsword", 0.52, 52.0, 7, 0.9, (228, 228, 238)),
    "bow": ThrowWeaponStats("Bow", 0.3, 48.0, 3, 1.34, (212, 180, 120)),
    "axe": ThrowWeaponStats("Axe", 0.5, 46.0, 8, 0.88, (176, 182, 192)),
    "javelin": ThrowWeaponStats("Javelin", 0.32, 66.0, 3, 1.28, (198, 204, 220)),
}
THROW_WEAPON_ORDER: tuple[str, ...] = (
    "spear",
    "trident",
    "broadsword",
    "bow",
    "axe",
    "javelin",
)
