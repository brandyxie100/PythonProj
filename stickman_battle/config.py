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
ATTACK_SPIN_SPEED: float = 0.035  # attack_phase per frame → full 360° swing
WEAPON_HIT_RADIUS: int = 16       # tip hit-detection radius during spin

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
        cooldown_f=30,   # frames between attacks
        knockback=4.0,
    ),
    "hammer": dict(
        label="Hammer",
        color=(160, 110, 55),
        guard_color=(200, 150, 80),
        reach=34,
        damage=22.0,
        cooldown_f=50,
        knockback=8.0,
    ),
    "pickaxe": dict(
        label="Pickaxe",
        color=(185, 185, 190),
        guard_color=(140, 140, 145),
        reach=42,
        damage=16.0,
        cooldown_f=38,
        knockback=5.5,
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
    ),
}
