"""
Ship Shooter - Bullet Component
===============================
Bullet sprites fired by the player; detect hits on enemies.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from config import res

if TYPE_CHECKING:
    from component.enemy import Enemy

# Constants
BULLET_SIZE: tuple[int, int] = (40, 40)
BULLET_SPEED: float = 2.0
BULLET_OFFSET_X: int = 75
BULLET_OFFSET_Y: int = -2
HIT_RADIUS: int = 30


class Bullet:
    """Bullet fired upward from the player.

    Attributes:
        img: Scaled bullet sprite.
        x: X position.
        y: Y position.
        step: Vertical speed (negative = upward).
    """

    def __init__(self, playerX: float, playerY: float) -> None:
        """Create a bullet at the player's position.

        Args:
            playerX: Player X (center).
            playerY: Player Y (center).
        """
        self.img: pygame.Surface = pygame.image.load(res("bullet_resized.png"))
        self.img = pygame.transform.scale(self.img, BULLET_SIZE)
        self.x: float = playerX + BULLET_OFFSET_X
        self.y: float = playerY + BULLET_OFFSET_Y
        self.step: float = BULLET_SPEED

    def show_bullet(self) -> pygame.Surface:
        """Return the bullet sprite for blitting."""
        return self.img

    def get_bullet_x(self) -> float:
        """Return current X position."""
        return self.x

    def get_bullet_y(self) -> float:
        """Return current Y position."""
        return self.y

    def move_bullet(self) -> None:
        """Move bullet upward."""
        self.y -= self.step

    def hit(self, enemies: list["Enemy"]) -> "Enemy | None":
        """Check if bullet hits any enemy.

        Args:
            enemies: List of Enemy sprites.

        Returns:
            The hit Enemy, or None if no hit.
        """
        for e in enemies:
            dist = math.dist(
                (self.x, self.y),
                (e.get_enemy_x(), e.get_enemy_y()),
            )
            if dist < HIT_RADIUS:
                return e
        return None

    def bao_sound(self) -> None:
        """Play explosion sound on hit."""
        sound = pygame.mixer.Sound(res("minecraft-tnt-explosion.mp3"))
        sound.play()
