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
# Base fall speed; actual per-frame fall uses a small random multiplier
ENEMY_FALL_SPEED: float = 0.35
# How aggressively enemies try to move toward the player when attacking (pixels per frame)
ENEMY_ATTACK_SPEED: float = 1.2
# Chance (0..1) per frame that an enemy will attempt an attack move toward player
ENEMY_ATTACK_CHANCE: float = 0.02


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

    def change_y(self, player_x: float | None = None) -> None:
        """Move enemy downward and occasionally attack horizontally.

        Args:
            player_x: Optional player X position; when provided the enemy may
                steer horizontally toward the player to perform an attack.
        """
        # Apply a small random multiplier so fall speed varies per frame/enemy
        fall_multiplier = random.uniform(1.0, 2.2)
        self.y += ENEMY_FALL_SPEED * fall_multiplier

        # Occasionally attempt a targeted attack toward the player's X
        if player_x is not None and random.random() < ENEMY_ATTACK_CHANCE:
            # Move horizontally toward player with some randomness
            direction = 1.0 if player_x > self.x else -1.0
            jitter = random.uniform(0.5, 1.5)
            self.x += direction * ENEMY_ATTACK_SPEED * jitter

        # Small random lateral drift so movement feels less linear
        drift = random.uniform(-0.8, 0.8)
        self.x += drift

    def change_step(self) -> None:
        """Reverse horizontal direction (currently unused)."""
        self.step *= -1
