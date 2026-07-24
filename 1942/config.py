"""1942 — Midway Atoll vertical shooter configuration."""

from __future__ import annotations

# Display
SCREEN_W: int = 480
SCREEN_H: int = 720
FPS: int = 60
TITLE: str = "1942 — Midway Atoll"

# World scroll (pixels per second)
OCEAN_SCROLL_BASE: float = 90.0
CLOUD_SCROLL: float = 40.0

# Player
PLAYER_SPEED: float = 280.0
PLAYER_MAX_HP: int = 3
PLAYER_FIRE_COOLDOWN: float = 0.18
PLAYER_LOOP_COOLDOWN: float = 3.5
PLAYER_LOOP_DURATION: float = 0.85
PLAYER_INVULN_AFTER_HIT: float = 1.6
PLAYER_BOMB_COUNT_START: int = 2

# Combat
PLAYER_BULLET_SPEED: float = 520.0
ENEMY_BULLET_SPEED: float = 210.0
BOMB_CLEAR_RADIUS: float = 220.0

# Colors — Pacific theater palette
OCEAN_DEEP: tuple[int, int, int] = (18, 72, 118)
OCEAN_MID: tuple[int, int, int] = (32, 110, 158)
OCEAN_FOAM: tuple[int, int, int] = (120, 190, 210)
SAND: tuple[int, int, int] = (210, 190, 140)
ATOLL_GREEN: tuple[int, int, int] = (56, 120, 72)
SKY_HAZE: tuple[int, int, int] = (170, 200, 220)
UI_WHITE: tuple[int, int, int] = (240, 244, 248)
UI_GOLD: tuple[int, int, int] = (240, 200, 70)
UI_RED: tuple[int, int, int] = (220, 60, 50)
UI_DIM: tuple[int, int, int] = (160, 175, 190)
PLAYER_BLUE: tuple[int, int, int] = (70, 110, 180)
PLAYER_NAVY: tuple[int, int, int] = (35, 55, 95)
ENEMY_OLIVE: tuple[int, int, int] = (90, 110, 55)
ENEMY_DARK: tuple[int, int, int] = (50, 60, 35)
BOSS_STEEL: tuple[int, int, int] = (90, 95, 105)
EXPLOSION_ORANGE: tuple[int, int, int] = (255, 140, 40)
EXPLOSION_YELLOW: tuple[int, int, int] = (255, 220, 80)

# Economy / upgrades
SCORE_FIGHTER: int = 100
SCORE_BOMBER: int = 250
SCORE_INTERCEPTOR: int = 150
SCORE_DIVE: int = 200
SCORE_GUNBOAT: int = 300
SCORE_BOSS: int = 5000
UPGRADE_COST_BASE: int = 800

# Missions
TOTAL_MISSIONS: int = 20
