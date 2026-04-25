"""
Ship Shooter - Enemy Component
==============================
Enemy sprites that descend and reset when off-screen or on collision.
"""

from __future__ import annotations

import random

import pygame

from config import res

# Constants
ENEMY_SIZE: tuple[int, int] = (80, 80)
ENEMY_SPAWN_X_MIN: int = 10
ENEMY_SPAWN_X_MAX: int = 750
ENEMY_SPAWN_Y_MIN: int = 0
ENEMY_SPAWN_Y_MAX: int = 10
ENEMY_STEP_MIN: float = 1.0
ENEMY_STEP_MAX: float = 1.5
ENEMY_FALL_SPEED: float = 2.5


class Enemy:
    """Enemy ship that descends from the top.

    Attributes:
        img: Scaled enemy sprite.
        x: X position.
        y: Y position.
        step: Horizontal movement step (unused in current logic).
    """

    def __init__(self) -> None:
        """Create a new enemy at random spawn position."""
        self.img: pygame.Surface = pygame.image.load(res("enemy.png"))
        self.img = pygame.transform.scale(self.img, ENEMY_SIZE)
        self.x: float = float(random.randint(ENEMY_SPAWN_X_MIN, ENEMY_SPAWN_X_MAX))
        self.y: float = float(random.randint(ENEMY_SPAWN_Y_MIN, ENEMY_SPAWN_Y_MAX))
        self.step: float = random.uniform(ENEMY_STEP_MIN, ENEMY_STEP_MAX)

    def show_ememy(self) -> pygame.Surface:
        """Return the enemy sprite for blitting."""
        return self.img

    def reset(self) -> None:
        """Respawn enemy at random top position."""
        self.x = float(random.randint(ENEMY_SPAWN_X_MIN, ENEMY_SPAWN_X_MAX))
        self.y = float(random.randint(ENEMY_SPAWN_Y_MIN, ENEMY_SPAWN_Y_MAX))

    def get_enemy_x(self) -> float:
        """Return current X position."""
        return self.x

    def get_enemy_y(self) -> float:
        """Return current Y position."""
        return self.y

    def change_x(self) -> None:
        """Move enemy horizontally (currently unused)."""
        self.x += self.step

    def change_y(self) -> None:
        """Move enemy downward."""
        self.y += ENEMY_FALL_SPEED

    def change_step(self) -> None:
        """Reverse horizontal direction (currently unused)."""
        self.step *= -1
