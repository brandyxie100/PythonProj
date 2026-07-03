"""Static terrain segments for stage arenas."""

from __future__ import annotations

import pygame
import pymunk

import config as c
from coords import pygame_to_pymunk, pymunk_to_pygame


class Terrain:
    """Ground line and one raised platform."""

    def __init__(self, space: pymunk.Space) -> None:
        """Add static collision segments to the physics space.

        Args:
            space: Active pymunk space.
        """
        self.space = space
        self.shapes: list[pymunk.Shape] = []
        self._build_ground()
        self._build_platform()

    def _static_segment(
        self,
        pygame_a: tuple[float, float],
        pygame_b: tuple[float, float],
    ) -> pymunk.Segment:
        """Create a static segment between two pygame points."""
        ax, ay = pygame_to_pymunk(*pygame_a)
        bx, by = pygame_to_pymunk(*pygame_b)
        shape = pymunk.Segment(self.space.static_body, (ax, ay), (bx, by), 8)
        shape.friction = c.GROUND_FRICTION
        shape.elasticity = c.GROUND_ELASTICITY
        shape.collision_type = c.COL_TERRAIN
        self.space.add(shape)
        self.shapes.append(shape)
        return shape

    def _build_ground(self) -> None:
        """Full-width floor at GROUND_Y."""
        self._static_segment((0, c.GROUND_Y), (c.SCREEN_W, c.GROUND_Y))

    def _build_platform(self) -> None:
        """Center raised platform from config."""
        x, y, w, h = c.PLATFORM_RECT
        self._static_segment((x, y), (x + w, y))
        self._static_segment((x, y), (x, y - h))
        self._static_segment((x + w, y), (x + w, y - h))

    def draw(self, surf: pygame.Surface) -> None:
        """Draw ground and platform for Milestone 1."""
        pygame.draw.rect(
            surf,
            c.GROUND_COL,
            (0, c.GROUND_Y, c.SCREEN_W, c.SCREEN_H - c.GROUND_Y),
        )
        px, py, pw, ph = c.PLATFORM_RECT
        pygame.draw.rect(surf, c.PLATFORM_COL, (px, py - ph, pw, ph))
        pygame.draw.rect(surf, c.PLATFORM_EDGE, (px, py - ph, pw, ph), 2)

        for shape in self.shapes:
            if isinstance(shape, pymunk.Segment):
                a = pymunk_to_pygame(shape.a)
                b = pymunk_to_pygame(shape.b)
                pygame.draw.line(surf, c.PLATFORM_EDGE, a, b, 3)
