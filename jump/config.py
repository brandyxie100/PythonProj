"""Shared settings for JUMP — a Geometry Dash–style auto-runner."""

from __future__ import annotations

import math

# Display
SCREEN_W: int = 960
SCREEN_H: int = 540
FPS: int = 60
TITLE: str = "JUMP"

# World / camera
GROUND_Y: float = 420.0
CEILING_Y: float = 72.0  # lethal top bound while flying the ship
SCROLL_SPEED: float = 380.0  # world units per second
PLAYER_SCREEN_X: float = 180.0  # cube stays here; world scrolls past

# Player cube — exactly two block-heights of jump
CUBE_SIZE: float = 36.0
JUMP_BLOCKS: float = 2.0
GRAVITY: float = 3600.0  # rise gravity
FALL_GRAVITY: float = 5000.0  # heavier fall so landings feel crisp
JUMP_HEIGHT: float = CUBE_SIZE * JUMP_BLOCKS
# Slightly stronger than the continuous formula so discrete steps still clear 2 blocks.
JUMP_VELOCITY: float = -math.sqrt(2.0 * GRAVITY * JUMP_HEIGHT) * 1.08
ROTATE_SPEED: float = 560.0  # degrees per second while airborne (cube)

# Ship gamemode — hold Space to climb, release to dive
SHIP_GRAVITY: float = 1400.0
SHIP_THRUST: float = 2800.0  # upward accel while holding
SHIP_MAX_SPEED: float = 620.0
SHIP_TILT_MAX: float = 55.0  # visual nose tilt in degrees

# Colors — neon geometry on deep navy (GD-inspired)
BG_TOP: tuple[int, int, int] = (18, 22, 48)
BG_BOTTOM: tuple[int, int, int] = (10, 12, 28)
GROUND: tuple[int, int, int] = (40, 48, 88)
GROUND_LINE: tuple[int, int, int] = (90, 220, 255)
CEILING_LINE: tuple[int, int, int] = (255, 140, 90)
CUBE: tuple[int, int, int] = (90, 255, 170)
CUBE_EDGE: tuple[int, int, int] = (220, 255, 240)
SHIP: tuple[int, int, int] = (90, 200, 255)
SHIP_EDGE: tuple[int, int, int] = (210, 240, 255)
SPIKE: tuple[int, int, int] = (255, 70, 110)
BLOCK: tuple[int, int, int] = (70, 120, 255)
BLOCK_EDGE: tuple[int, int, int] = (160, 200, 255)
PORTAL_SHIP: tuple[int, int, int] = (80, 200, 255)
PORTAL_CUBE: tuple[int, int, int] = (120, 255, 140)
UI: tuple[int, int, int] = (230, 240, 255)
UI_DIM: tuple[int, int, int] = (140, 160, 200)
PROGRESS_BG: tuple[int, int, int] = (30, 36, 70)
PROGRESS_FILL: tuple[int, int, int] = (90, 255, 170)
STAR: tuple[int, int, int] = (255, 220, 90)
MENU_BTN: tuple[int, int, int] = (50, 180, 140)
MENU_BTN_HOVER: tuple[int, int, int] = (70, 220, 170)

# Death flash
DEATH_FLASH_TIME: float = 0.55
