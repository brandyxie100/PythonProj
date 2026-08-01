"""Shared settings for JUMP — a Geometry Dash–style auto-runner."""

from __future__ import annotations

# Display
SCREEN_W: int = 960
SCREEN_H: int = 540
FPS: int = 60
TITLE: str = "JUMP"

# World / camera
GROUND_Y: float = 420.0
SCROLL_SPEED: float = 380.0  # world units per second
PLAYER_SCREEN_X: float = 180.0  # cube stays here; world scrolls past

# Player cube — snappy GD-like arc (~1.8 cube heights)
CUBE_SIZE: float = 36.0
GRAVITY: float = 3800.0  # rise gravity
FALL_GRAVITY: float = 5200.0  # heavier fall so landings feel crisp
JUMP_VELOCITY: float = -720.0
ROTATE_SPEED: float = 560.0  # degrees per second while airborne

# Colors — neon geometry on deep navy (GD-inspired)
BG_TOP: tuple[int, int, int] = (18, 22, 48)
BG_BOTTOM: tuple[int, int, int] = (10, 12, 28)
GROUND: tuple[int, int, int] = (40, 48, 88)
GROUND_LINE: tuple[int, int, int] = (90, 220, 255)
CUBE: tuple[int, int, int] = (90, 255, 170)
CUBE_EDGE: tuple[int, int, int] = (220, 255, 240)
SPIKE: tuple[int, int, int] = (255, 70, 110)
BLOCK: tuple[int, int, int] = (70, 120, 255)
BLOCK_EDGE: tuple[int, int, int] = (160, 200, 255)
UI: tuple[int, int, int] = (230, 240, 255)
UI_DIM: tuple[int, int, int] = (140, 160, 200)
PROGRESS_BG: tuple[int, int, int] = (30, 36, 70)
PROGRESS_FILL: tuple[int, int, int] = (90, 255, 170)
STAR: tuple[int, int, int] = (255, 220, 90)

# Death flash
DEATH_FLASH_TIME: float = 0.55
