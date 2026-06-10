"""Stickman Battle — shared constants, difficulty presets, weapon data.

All tuneable values live here so nothing is hard-coded elsewhere.
"""

import pygame

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
FPS: int = 60
SCREEN_W: int = 900
SCREEN_H: int = 600
TITLE: str = "Stickman Battle"

# ---------------------------------------------------------------------------
# Physics
# ---------------------------------------------------------------------------
GRAVITY: float = 0.55
JUMP_VEL: float = -13.5
DOUBLE_JUMP_VEL: float = -11.5   # mid-air jump (slightly weaker)
MAX_CONSECUTIVE_JUMPS: int = 2   # ground jump + one extra mid-air jump
MAX_FALL: float = 16.0
GROUND_FRICTION: float = 0.80  # velocity multiplied per frame when on ground
PLAYER_SPEED: float = 3.5
ATTACK_SPIN_SPEED: float = 0.1  # attack_phase per frame → full 360° swing
WEAPON_HIT_RADIUS: int = 20       # tip hit-detection radius during spin

# ---------------------------------------------------------------------------
# Stickman anatomy (pixels) — shared by all drawn stickmen
# ---------------------------------------------------------------------------
HEAD_R: int = 12
NECK_H: int = 4
TORSO_H: int = 32
UPPER_ARM: int = 12
LOWER_ARM: int = 10
UPPER_LEG: int = 16
LOWER_LEG: int = 12
LINE_W: int = 3

# Bounding-box helpers (derived)
STICK_H: int = HEAD_R * 2 + NECK_H + TORSO_H + UPPER_LEG + LOWER_LEG  # ≈ 88
STICK_W: int = 32

# ---------------------------------------------------------------------------
# Tire
# ---------------------------------------------------------------------------
TIRE_RADIUS: int = 22
TIRE_BOUNCE: float = 0.65  # coefficient of restitution on bounce

# ---------------------------------------------------------------------------
# Spring ball — fixed booster pads
# ---------------------------------------------------------------------------
SPRING_BALL_RADIUS: int = 18
SPRING_BOOST_VEL: float = -19.0   # upward launch (stronger than normal jump)
SPRING_COL       = (255, 210, 50)
SPRING_DARK      = (220, 150, 20)
SPRING_COIL      = (255, 240, 120)

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
# Background
BG_TOP = (15, 45, 85)
BG_BOT = (28, 72, 125)

# Platforms
PLAT_DARK = (12, 40, 72)
PLAT_EDGE = (0, 200, 240)       # cyan top edge  (like reference screenshot)
PLAT_GLOW = (80, 220, 255)

# Stickmen
BLUE_COL   = (0, 180, 220)
RED_COL    = (220, 50, 50)
YELLOW_COL = (220, 190, 0)

# Tires
TIRE_COL = (210, 40, 40)
TIRE_IN  = (155, 18, 18)

# HUD / UI
HP_RED    = (180, 30, 30)
HP_GREEN  = (50, 200, 50)
HP_BORDER = (200, 200, 200)
WHITE     = (255, 255, 255)
BLACK     = (0, 0, 0)
GRAY      = (120, 120, 120)
DARK_GRAY = (50, 50, 60)
UI_BG     = (15, 20, 40)
UI_BORDER = (70, 90, 130)

# ---------------------------------------------------------------------------
# Input — player key mapping
# ---------------------------------------------------------------------------
KEY_LEFT  = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_JUMP  = pygame.K_UP
KEY_LEFT2 = pygame.K_a
KEY_RIGHT2 = pygame.K_d
KEY_JUMP2 = pygame.K_w
KEY_ATK   = pygame.K_z
KEY_ATK2  = pygame.K_j
KEY_GRENADE = pygame.K_b

# ---------------------------------------------------------------------------
# Bow & arrows — ranged pickup weapon
# ---------------------------------------------------------------------------
BOW_PICKUP_DURATION_F: int = FPS * 10   # 10-second countdown
BOW_ARROWS_PER_SET: int = 20
BOW_SPAWN_CHANCE: float = 0.85          # chance to spawn after an enemy kill
BOW_PICKUP_RADIUS: int = 28
ARROW_SPEED: float = 14.0
ARROW_GRAVITY: float = 0.1
ARROW_DAMAGE: float = 20.0
ARROW_KNOCKBACK: float = 3.0
BOW_COL = (250, 110, 55)
BOW_STRING = (220, 220, 220)
BOW_SHINE = (255, 240, 120)
BOW_GLOW = (255, 200, 50)

# ---------------------------------------------------------------------------
# AK-47 — rifle rounds (obtained from loot chest)
# ---------------------------------------------------------------------------
AK47_ROUNDS_PER_PICKUP: int = 30
AK47_BULLET_SPEED: float = 22.0
AK47_BULLET_GRAVITY: float = 0
AK47_FIRE_COOLDOWN_F: int = 3               # automatic fire rate
AK47_RECOIL_FRAMES: int = 5
AK47_COL = (55, 50, 45)
AK47_WOOD = (110, 75, 40)
AK47_METAL = (90, 95, 100)
AK47_GLOW = (80, 220, 120)
AK47_SHINE = (180, 255, 200)
AK47_MUZZLE_FLASH = (255, 230, 100)
AK47_CASING = (220, 180, 60)

# ---------------------------------------------------------------------------
# Loot chest — recurring mystery spawn every 20 seconds
# ---------------------------------------------------------------------------
CHEST_SPAWN_INTERVAL_F: int = FPS * 20
CHEST_PICKUP_RADIUS: int = 32
CHEST_GRENADE_BONUS: int = 3
CHEST_TOAST_FRAMES: int = FPS * 2
CHEST_REWARD_TYPES: list[str] = [
    "bow",
    "ak47",
    "sword",
    "hammer",
    "pickaxe",
    "grenades",
]
CHEST_WOOD = (140, 90, 45)
CHEST_GOLD = (255, 210, 60)
CHEST_GLOW = (255, 180, 40)
CHEST_DARK = (90, 55, 25)

# ---------------------------------------------------------------------------
# Grenades
# ---------------------------------------------------------------------------
GRENADES_PER_MATCH: int = 6
GRENADE_DAMAGE: float = 24.0      # must exceed sword damage (12.0)
GRENADE_RADIUS: float = 78.0
GRENADE_CONTACT_PAD: int = 8      # body inflate for contact detonation
GRENADE_FUSE_F: int = 95          # ~1.6 seconds
GRENADE_COOLDOWN_F: int = 75
GRENADE_THROW_MIN_VY: float = -12.0
GRENADE_THROW_MAX_VY: float = -8.0
GRENADE_BOUNCE: float = 0.55
GRENADE_AIR_DRAG: float = 0.995
GRENADE_COL = (70, 95, 70)
GRENADE_PIN = (210, 210, 210)

# Blast palette — vivid red / orange fireball
GRENADE_EXPLODE_CORE   = (255, 250, 180)   # white-hot flash
GRENADE_EXPLODE_INNER  = (255, 200, 40)    # bright orange
GRENADE_EXPLODE_MID    = (255, 90, 15)     # vivid red-orange
GRENADE_EXPLODE_OUTER  = (230, 35, 8)      # deep red
GRENADE_EXPLODE_SMOKE  = (140, 25, 10)     # dark ember edge
GRENADE_PARTICLE_COLORS = [
    (255, 220, 60),
    (255, 150, 20),
    (255, 80, 10),
    (220, 40, 5),
    (255, 100, 30),
]
GRENADE_BLAST_PARTICLE_COUNT: int = 42
GRENADE_EXPLOSION_LIFE_F: int = 24   # frames of blast + particle animation

# ---------------------------------------------------------------------------
# Weapons: name → attribute dict
# ---------------------------------------------------------------------------
WEAPONS: dict[str, dict] = {
    "sword": dict(
        label="Sword",
        color=(200, 210, 235),
        guard_color=(170, 175, 195),
        reach=48,
        damage=12.0,
        cooldown_f=1,   # frames between attacks (faster than other melee)
        spin_speed=0.1,  # full 360° spin completes in ~18 frames
        knockback=4.0,
    ),
    "hammer": dict(
        label="Hammer",
        color=(160, 110, 55),
        guard_color=(200, 150, 80),
        reach=34,
        damage=22.0,
        cooldown_f=10,
        knockback=8.0,
    ),
    "pickaxe": dict(
        label="Pickaxe",
        color=(185, 185, 190),
        guard_color=(140, 140, 145),
        reach=42,
        damage=16.0,
        cooldown_f=5,
        knockback=5.5,
    ),
    "bow": dict(
        label="Bow",
        color=BOW_COL,
        guard_color=BOW_STRING,
        reach=36,
        damage=ARROW_DAMAGE,
        cooldown_f=18,
        knockback=ARROW_KNOCKBACK,
    ),
    "ak47": dict(
        label="AK-47",
        color=AK47_METAL,
        guard_color=AK47_WOOD,
        reach=52,
        damage=ARROW_DAMAGE,
        cooldown_f=AK47_FIRE_COOLDOWN_F,
        knockback=ARROW_KNOCKBACK,
    ),
}

# ---------------------------------------------------------------------------
# Difficulty presets
# ---------------------------------------------------------------------------
DIFFICULTIES: dict[str, dict] = {
    "easy": dict(
        enemy_count=2,
        enemy_health=60.0,
        enemy_speed=1.8,
        enemy_damage=5.0,
        enemy_attack_cd=70,   # frames
        player_health=150.0,
        player_damage_mult=1.5,
        enemy_weapons=["sword"],
        enemy_grenade_cooldown=180,
        enemy_grenade_chance=0.32,
    ),
    "normal": dict(
        enemy_count=3,
        enemy_health=100.0,
        enemy_speed=2.8,
        enemy_damage=10.0,
        enemy_attack_cd=55,
        player_health=100.0,
        player_damage_mult=1.0,
        enemy_weapons=["sword", "pickaxe"],
        enemy_grenade_cooldown=130,
        enemy_grenade_chance=0.52,
    ),
    "hard": dict(
        enemy_count=5,
        enemy_health=150.0,
        enemy_speed=4.0,
        enemy_damage=18.0,
        enemy_attack_cd=40,
        player_health=70.0,
        player_damage_mult=0.8,
        enemy_weapons=["sword", "pickaxe", "hammer"],
        enemy_grenade_cooldown=90,
        enemy_grenade_chance=0.74,
    ),
}
