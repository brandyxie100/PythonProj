"""Shared settings for Tank Stars — side-view artillery duels."""

from __future__ import annotations

# Display
SCREEN_W: int = 1100
SCREEN_H: int = 640
FPS: int = 60
TITLE: str = "Tank Stars"

# World
GROUND_COLOR: tuple[int, int, int] = (62, 120, 58)
GROUND_DARK: tuple[int, int, int] = (42, 88, 40)
SKY_TOP: tuple[int, int, int] = (120, 190, 255)
SKY_BOTTOM: tuple[int, int, int] = (210, 235, 255)
DIRT_LAYER: int = 18

# Tank
TANK_W: int = 46
TANK_H: int = 28
TANK_MAX_HP: int = 100
MOVE_SPEED: float = 95.0
AIM_SPEED: float = 1.35  # rad/s
POWER_SPEED: float = 55.0  # % per second while charging
POWER_MIN: float = 18.0
POWER_MAX: float = 100.0
BARREL_LEN: float = 34.0
GRAVITY: float = 520.0
SHOT_SPEED_SCALE: float = 9.2  # power * scale = muzzle speed

# Combat
MAX_STAGES: int = 20
PLAYER_LIVES: int = 3
TURN_WIND_MAX: float = 45.0  # horizontal wind force
AI_AIM_NOISE: float = 0.08
AI_POWER_NOISE: float = 6.0

# Blast animation
BLAST_RING_COUNT: int = 4
BLAST_SPARK_COUNT: int = 28
BLAST_SMOKE_COUNT: int = 16
BLAST_DEBRIS_COUNT: int = 14
BLAST_DURATION: float = 0.85
CRATER_RADIUS: float = 38.0

# Colors
PLAYER_BODY: tuple[int, int, int] = (55, 160, 90)
PLAYER_TRIM: tuple[int, int, int] = (30, 100, 55)
ENEMY_BODY: tuple[int, int, int] = (200, 75, 70)
ENEMY_TRIM: tuple[int, int, int] = (130, 40, 40)
UI: tuple[int, int, int] = (245, 248, 255)
UI_DIM: tuple[int, int, int] = (40, 55, 70)
HP_GREEN: tuple[int, int, int] = (70, 210, 90)
HP_RED: tuple[int, int, int] = (230, 70, 60)
POWER_YELLOW: tuple[int, int, int] = (255, 200, 50)
