"""Level obstacles and a handcrafted Geometry Dash–style course."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pygame

import config as c

ObstacleKind = Literal["spike", "block"]


@dataclass(slots=True)
class Obstacle:
    """A world-space hazard or platform.

    Coordinates are relative to the level origin (x increases to the right).
    Spikes kill on any contact. Blocks can be landed on from above; side or
    underside contact kills.
    """

    kind: ObstacleKind
    x: float
    y: float  # top of the object
    w: float
    h: float

    def screen_rect(self, camera_x: float) -> pygame.Rect:
        """Return the axis-aligned rect in screen space."""
        return pygame.Rect(
            int(self.x - camera_x),
            int(self.y),
            int(self.w),
            int(self.h),
        )


def build_level() -> tuple[list[Obstacle], float]:
    """Build the main course and return ``(obstacles, finish_x)``."""
    objs: list[Obstacle] = []
    g = c.GROUND_Y
    s = c.CUBE_SIZE

    def spike(wx: float, *, tall: float = 28.0) -> None:
        objs.append(Obstacle("spike", wx, g - tall, 28.0, tall))

    def block(wx: float, wy: float, w: float = s, h: float = s) -> None:
        objs.append(Obstacle("block", wx, wy, w, h))

    # Intro runway — learn the jump.
    x = 520.0
    spike(x)
    x += 220
    spike(x)
    x += 180
    spike(x)
    spike(x + 40)

    # Low hop onto a block, then off.
    x += 280
    block(x, g - s)
    spike(x + s + 20)
    x += 260
    spike(x)
    spike(x + 36)
    spike(x + 72)

    # Stair climb.
    x += 280
    block(x, g - s)
    block(x + s + 8, g - s * 2)
    block(x + (s + 8) * 2, g - s * 3)
    spike(x + (s + 8) * 3 + 30)
    x += 420

    # Gap with mid-air block landing.
    spike(x)
    block(x + 90, g - s * 2.2)
    spike(x + 200)
    x += 360

    # Spike garden (tight timing).
    for i in range(6):
        spike(x + i * 70)
    x += 6 * 70 + 200

    # Double stack then drop.
    block(x, g - s)
    block(x, g - s * 2)
    spike(x + s + 24)
    spike(x + s + 60)
    x += 320

    # Floating island sequence.
    block(x, g - s * 2.5, w=s * 2)
    block(x + 160, g - s * 3.5, w=s * 2)
    spike(x + 100, tall=22)
    block(x + 340, g - s * 2.0, w=s * 3)
    x += 520

    # Fast spike run into finish.
    for i in range(8):
        gap = 55 if i % 2 == 0 else 95
        spike(x)
        x += gap
    x += 180

    # Victory pad.
    block(x, g - s, w=s * 4)
    finish_x = x + s * 4 + 80
    return objs, finish_x


def draw_obstacle(surf: pygame.Surface, obs: Obstacle, camera_x: float) -> None:
    """Render a spike or block in screen space."""
    rect = obs.screen_rect(camera_x)
    if rect.right < -40 or rect.left > c.SCREEN_W + 40:
        return

    if obs.kind == "spike":
        tip = (rect.centerx, rect.top)
        left = (rect.left, rect.bottom)
        right = (rect.right, rect.bottom)
        pygame.draw.polygon(surf, c.SPIKE, [tip, left, right])
        pygame.draw.polygon(surf, (255, 160, 180), [tip, left, right], width=2)
    else:
        pygame.draw.rect(surf, c.BLOCK, rect, border_radius=3)
        pygame.draw.rect(surf, c.BLOCK_EDGE, rect, width=2, border_radius=3)
        inset = rect.inflate(-8, -8)
        if inset.w > 4 and inset.h > 4:
            pygame.draw.line(
                surf,
                c.BLOCK_EDGE,
                (inset.left, inset.centery),
                (inset.right, inset.centery),
                1,
            )
            pygame.draw.line(
                surf,
                c.BLOCK_EDGE,
                (inset.centerx, inset.top),
                (inset.centerx, inset.bottom),
                1,
            )
