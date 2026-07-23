"""Shared configuration for Versus Projectile Duel Mode."""

from __future__ import annotations

from dataclasses import dataclass

# Display
SCREEN_W: int = 1280
SCREEN_H: int = 720
FPS: int = 60
TITLE: str = "Ragdoll Hit - Versus Projectile Duel"

# Stickman geometry (shared by duel fighters)
HEAD_R: float = 11.0
TORSO_LEN: float = 46.0
ARM_LEN: float = 34.0
LEG_LEN: float = 38.0

# UI colors
UI_TEXT: tuple[int, int, int] = (235, 238, 248)
UI_FAINT: tuple[int, int, int] = (178, 183, 196)
WHITE: tuple[int, int, int] = (248, 248, 250)
ENEMY_YELLOW: tuple[int, int, int] = (240, 212, 90)

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

# Pillar dodging
DUEL_MOVE_SPEED: float = 210.0  # horizontal dodge speed on the pillar top
DUEL_PILLAR_HALF_WIDTH: float = 48.0  # safe standing range from pillar center
DUEL_FALL_GRAVITY: float = 1600.0  # gravity after stepping off the pillar
# Random slide when an enemy is hit — always clamped inside the pillar.
DUEL_HIT_KNOCKBACK_MIN: float = 14.0
DUEL_HIT_KNOCKBACK_MAX: float = 32.0
DUEL_HIT_KNOCKBACK_SAFE: float = 0.82  # max |x - anchor| as a fraction of half-width

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

# Coin payouts for landing a hit on an enemy.
# Matches the 1x / 2x / 3x hurt ladder used for limb / torso / head damage.
HIT_COINS_LIMB: int = 5  # arms and legs
HIT_COINS_TORSO: int = 10  # body — double limb
HIT_COINS_HEAD: int = 15  # head — triple limb
DUEL_STARTER_WEAPON: str = "spear"

# Stage campaign length / dual-enemy breakpoint (latter half).
DUEL_TOTAL_STAGES: int = 30
DUEL_DUAL_ENEMY_FROM: int = 16  # stage 16+ adds a taller second pillar + foe


@dataclass(frozen=True, slots=True)
class ThrowWeaponStats:
    """Stats for a thrown/launched projectile weapon."""

    name: str
    damage: float  # redness (0..1) added to the struck body segment
    length: float  # drawn length in pixels
    thickness: int
    speed_scale: float  # multiplies launch power
    color: tuple[int, int, int]
    price: int  # coin cost to unlock (0 = starter / free)


# Shop ladder: cheaper weapons hit softer; pricier weapons hit harder.
THROW_WEAPONS: dict[str, ThrowWeaponStats] = {
    "spear": ThrowWeaponStats("Spear", 0.28, 60.0, 4, 1.12, (208, 214, 226), 0),
    "bow": ThrowWeaponStats("Bow", 0.34, 48.0, 3, 1.34, (212, 180, 120), 18),
    "javelin": ThrowWeaponStats("Javelin", 0.40, 66.0, 3, 1.28, (198, 204, 220), 32),
    "trident": ThrowWeaponStats("Trident", 0.48, 54.0, 6, 1.0, (150, 210, 225), 50),
    "axe": ThrowWeaponStats("Axe", 0.56, 46.0, 8, 0.88, (176, 182, 192), 72),
    "broadsword": ThrowWeaponStats(
        "Broadsword", 0.68, 52.0, 7, 0.9, (228, 228, 238), 100
    ),
}
THROW_WEAPON_ORDER: tuple[str, ...] = (
    "spear",
    "bow",
    "javelin",
    "trident",
    "axe",
    "broadsword",
)


@dataclass(frozen=True, slots=True)
class DefenseGearStats:
    """Helmet or shield bought to reduce incoming projectile damage."""

    name: str
    kind: str  # "helmet" or "shield"
    price: int
    damage_factor: float  # multiplies damage to protected segments (lower = tankier)
    durability: int  # hits absorbed before the gear breaks
    blocks_lethal: bool  # helmets can cancel instant head-kill while intact
    color: tuple[int, int, int]


# Defense ladder: priced so mid-campaign farming unlocks leather/wood, late
# campaign can afford iron/knight tiers without trivializing broadsword DPS.
# Helmet protects head; shield protects torso + limbs.
HELMETS: dict[str, DefenseGearStats] = {
    "leather_helm": DefenseGearStats(
        "Leather Helm", "helmet", 55, 0.50, 3, True, (150, 110, 70)
    ),
    "iron_helm": DefenseGearStats(
        "Iron Helm", "helmet", 115, 0.32, 5, True, (160, 168, 180)
    ),
    "knight_helm": DefenseGearStats(
        "Knight Helm", "helmet", 210, 0.18, 8, True, (210, 190, 90)
    ),
}
SHIELDS: dict[str, DefenseGearStats] = {
    "wood_shield": DefenseGearStats(
        "Wood Shield", "shield", 50, 0.55, 4, False, (140, 95, 55)
    ),
    "iron_shield": DefenseGearStats(
        "Iron Shield", "shield", 105, 0.38, 6, False, (150, 158, 170)
    ),
    "tower_shield": DefenseGearStats(
        "Tower Shield", "shield", 195, 0.22, 9, False, (90, 120, 150)
    ),
}
HELMET_ORDER: tuple[str, ...] = ("leather_helm", "iron_helm", "knight_helm")
SHIELD_ORDER: tuple[str, ...] = ("wood_shield", "iron_shield", "tower_shield")


def hit_coins_for_segment(segment_name: str) -> int:
    """Return coins awarded for striking a body segment.

    Arms/legs pay the limb rate; torso pays double; head pays triple.
    """
    if segment_name == "head":
        return HIT_COINS_HEAD
    if segment_name == "torso":
        return HIT_COINS_TORSO
    return HIT_COINS_LIMB


def duel_coin_goal(stage: int) -> int:
    """Coin goal for a stage — rises steadily, with a bump after dual enemies."""
    goal = 22 + stage * 7
    if stage >= DUEL_DUAL_ENEMY_FROM:
        goal += (stage - DUEL_DUAL_ENEMY_FROM + 1) * 6
    return goal


def duel_fire_interval(stage: int) -> float:
    """Seconds between enemy throws (faster in later stages)."""
    return max(0.85, 2.65 - (stage - 1) * 0.058)


def duel_aim_noise(stage: int) -> float:
    """AI elevation jitter in radians (tighter aim later)."""
    return max(0.02, 0.21 - (stage - 1) * 0.0065)
