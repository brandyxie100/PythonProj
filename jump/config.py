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
CEILING_Y: float = 72.0
SCROLL_SPEED: float = 380.0
PLAYER_SCREEN_X: float = 180.0

# Shared jump — exactly two block-heights
CUBE_SIZE: float = 36.0
JUMP_BLOCKS: float = 2.0
GRAVITY: float = 3600.0
FALL_GRAVITY: float = 5000.0
JUMP_HEIGHT: float = CUBE_SIZE * JUMP_BLOCKS
JUMP_VELOCITY: float = -math.sqrt(2.0 * GRAVITY * JUMP_HEIGHT) * 1.08
ROTATE_SPEED: float = 560.0

# Ship — hold Space to fly up, release to fly down
SHIP_GRAVITY: float = 1600.0
SHIP_THRUST: float = 3200.0
SHIP_MAX_SPEED: float = 640.0
SHIP_TILT_MAX: float = 55.0

# Ball — click flips gravity
BALL_SPIN_SPEED: float = 720.0

# UFO — click jumps 2 blocks even mid-air
UFO_JUMP_VELOCITY: float = JUMP_VELOCITY

# Colors
BG_TOP: tuple[int, int, int] = (18, 22, 48)
BG_BOTTOM: tuple[int, int, int] = (10, 12, 28)
GROUND: tuple[int, int, int] = (40, 48, 88)
GROUND_LINE: tuple[int, int, int] = (90, 220, 255)
CEILING_LINE: tuple[int, int, int] = (255, 140, 90)

CUBE: tuple[int, int, int] = (70, 78, 90)
CUBE_EDGE: tuple[int, int, int] = (20, 22, 28)
CUBE_CORE: tuple[int, int, int] = (140, 210, 255)

SHIP: tuple[int, int, int] = (90, 100, 115)
SHIP_EDGE: tuple[int, int, int] = (25, 28, 34)
SHIP_WINDOW: tuple[int, int, int] = (230, 235, 245)

BALL: tuple[int, int, int] = (80, 88, 100)
BALL_EDGE: tuple[int, int, int] = (20, 22, 28)
BALL_CORE: tuple[int, int, int] = (200, 205, 215)

UFO: tuple[int, int, int] = (95, 105, 120)
UFO_EDGE: tuple[int, int, int] = (25, 28, 34)
UFO_DOME: tuple[int, int, int] = (235, 240, 250)

SPIKE: tuple[int, int, int] = (255, 70, 110)
BLOCK: tuple[int, int, int] = (70, 120, 255)
BLOCK_EDGE: tuple[int, int, int] = (160, 200, 255)

# Portal colors from the reference chart
PORTAL_CUBE: tuple[int, int, int] = (60, 220, 90)  # green
PORTAL_SHIP: tuple[int, int, int] = (210, 70, 220)  # purple
PORTAL_BALL: tuple[int, int, int] = (255, 110, 50)  # orange-red
PORTAL_UFO: tuple[int, int, int] = (255, 190, 50)  # yellow

PORTAL_COLORS: dict[str, tuple[int, int, int]] = {
    "cube": PORTAL_CUBE,
    "ship": PORTAL_SHIP,
    "ball": PORTAL_BALL,
    "ufo": PORTAL_UFO,
}

UI: tuple[int, int, int] = (230, 240, 255)
UI_DIM: tuple[int, int, int] = (140, 160, 200)
PROGRESS_BG: tuple[int, int, int] = (30, 36, 70)
PROGRESS_FILL: tuple[int, int, int] = (90, 255, 170)
STAR: tuple[int, int, int] = (255, 220, 90)
MENU_BTN: tuple[int, int, int] = (50, 180, 140)
MENU_BTN_HOVER: tuple[int, int, int] = (70, 220, 170)

DEATH_FLASH_TIME: float = 0.55
