"""
Ship Shooter - Player Component
==============================
Player sprite with health bar, movement, and asset loading.
"""

from __future__ import annotations

import pygame

from config import res

# Constants
PLAYER_INITIAL_X: int = 400
PLAYER_INITIAL_Y: int = 450
PLAYER_STEP: float = 1.5
HEALTH_BAR_WIDTH: int = 100
HEALTH_BAR_HEIGHT: int = 10
HEALTH_BAR_OFFSET_X: int = 50
HEALTH_BAR_OFFSET_Y: int = -15


class Player:
    """Player-controlled ship at the bottom of the screen.

    Attributes:
        health: Current hit points.
        max_health: Maximum hit points.
        x: X position (center).
        y: Y position (center).
        step: Movement speed per frame.
    """

    def __init__(self) -> None:
        """Create a new player at default position."""
        self.health: int = 100
        self.max_health: int = 100
        self.x: float = float(PLAYER_INITIAL_X)
        self.y: float = float(PLAYER_INITIAL_Y)
        self.img: pygame.Surface = pygame.image.load(res("player-removebg-preview.png"))
        self.step: float = PLAYER_STEP

    def show_player(self) -> pygame.Surface:
        """Return the player sprite for blitting."""
        return self.img

    def change_x(self, step: float) -> None:
        """Move player horizontally by step."""
        self.x += step

    def get_player_x(self) -> float:
        """Return current X position."""
        return self.x

    def get_player_y(self) -> float:
        """Return current Y position."""
        return self.y

    def move_left(self) -> None:
        """Move player left by one step."""
        self.x -= self.step

    def move_right(self) -> None:
        """Move player right by one step."""
        self.x += self.step

    def draw_health_bar(self, surface: pygame.Surface) -> None:
        """Draw health bar above the player.

        Red background = missing health; green foreground = current health.

        Args:
            surface: Pygame surface to draw on.
        """
        bar_x = self.x + HEALTH_BAR_OFFSET_X
        bar_y = self.y + HEALTH_BAR_OFFSET_Y
        health_ratio = self.health / self.max_health

        # Red background (full bar)
        pygame.draw.rect(
            surface, (255, 0, 0),
            (bar_x, bar_y, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT),
        )
        # Green foreground (current health)
        pygame.draw.rect(
            surface, (0, 255, 0),
            (bar_x, bar_y, HEALTH_BAR_WIDTH * health_ratio, HEALTH_BAR_HEIGHT),
        )
        # Border
        pygame.draw.rect(
            surface, (0, 0, 0),
            (bar_x, bar_y, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT), 2,
        )
