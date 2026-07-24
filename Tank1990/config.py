"""Tank 1990 — Battle City Legend configuration (NES-inspired)."""

from __future__ import annotations

# Logical tile grid matches classic Battle City (26×26 of 8px tiles).
TILE: int = 8
MAP_W: int = 26
MAP_H: int = 26
SCALE: int = 3  # crisp pixel scale

PLAY_W: int = MAP_W * TILE * SCALE  # 624
PLAY_H: int = MAP_H * TILE * SCALE  # 624
PANEL_W: int = 96
SCREEN_W: int = PLAY_W + PANEL_W
SCREEN_H: int = PLAY_H
FPS: int = 60
TITLE: str = "Tank 1990 — Battle City Legend"

# Tank body is 2×2 tiles (16×16 logical px).
TANK_SIZE: int = TILE * 2
# Wall / brick blocks use the tank footprint as the world unit.
BRICK_UNIT: int = TANK_SIZE
BRICK_CELLS: int = BRICK_UNIT // TILE  # 2×2 fine tiles per brick block

# Speeds in logical pixels per second.
PLAYER_SPEED: float = 48.0
BULLET_SPEED: float = 140.0
ENEMY_SPEED_BASIC: float = 36.0
ENEMY_SPEED_FAST: float = 64.0
ENEMY_SPEED_POWER: float = 40.0
ENEMY_SPEED_ARMOR: float = 28.0

PLAYER_FIRE_CD: float = 0.38
ENEMY_FIRE_CD: float = 1.05
SPAWN_INVULN: float = 2.5
SHIELD_TIME: float = 10.0
FREEZE_TIME: float = 8.0
SHOVEL_TIME: float = 18.0

PLAYER_LIVES: int = 3
ENEMIES_PER_STAGE: int = 20
MAX_ENEMIES_ON_FIELD: int = 4
SPAWN_INTERVAL: float = 2.8

TOTAL_STAGES: int = 15

# Classic palette (Battle City / Famicom vibe)
BLACK: tuple[int, int, int] = (0, 0, 0)
GRAY: tuple[int, int, int] = (99, 99, 99)
STEEL: tuple[int, int, int] = (180, 180, 180)
STEEL_DK: tuple[int, int, int] = (100, 100, 100)
BRICK_R: tuple[int, int, int] = (188, 80, 48)
BRICK_DK: tuple[int, int, int] = (120, 40, 24)
WATER_A: tuple[int, int, int] = (48, 96, 200)
WATER_B: tuple[int, int, int] = (64, 128, 220)
GRASS: tuple[int, int, int] = (32, 140, 48)
GRASS_DK: tuple[int, int, int] = (16, 96, 32)
ICE: tuple[int, int, int] = (176, 220, 240)
ICE_DK: tuple[int, int, int] = (140, 190, 220)
PANEL_BG: tuple[int, int, int] = (99, 99, 99)
UI_WHITE: tuple[int, int, int] = (252, 252, 252)
UI_YELLOW: tuple[int, int, int] = (248, 216, 64)
UI_ORANGE: tuple[int, int, int] = (232, 140, 32)
PLAYER_YELLOW: tuple[int, int, int] = (232, 200, 48)
PLAYER_DK: tuple[int, int, int] = (160, 120, 16)
ENEMY_GRAY: tuple[int, int, int] = (160, 160, 160)
ENEMY_DK: tuple[int, int, int] = (80, 80, 80)
ENEMY_GREEN: tuple[int, int, int] = (64, 160, 64)
ENEMY_RED: tuple[int, int, int] = (200, 48, 48)
EAGLE: tuple[int, int, int] = (200, 160, 48)
EAGLE_DK: tuple[int, int, int] = (120, 80, 16)
EXPLOSION: tuple[int, int, int] = (248, 160, 32)

# Tile codes
T_EMPTY: int = 0
T_BRICK: int = 1
T_STEEL: int = 2
T_WATER: int = 3
T_GRASS: int = 4
T_ICE: int = 5
T_BASE: int = 6  # eagle footprint (2×2 area marked on map)
