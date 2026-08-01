"""Player cube / ship for JUMP."""

from __future__ import annotations

from typing import Literal

import pygame

import config as c

Gamemode = Literal["cube", "ship"]


class Player:
    """Auto-running icon that switches between cube jump and ship flight."""

    def __init__(self) -> None:
        """Place the icon on the ground at the fixed screen X."""
        self.size = c.CUBE_SIZE
        self.x = c.PLAYER_SCREEN_X
        self.y = c.GROUND_Y - self.size
        self.vy = 0.0
        self.on_ground = True
        self.angle = 0.0  # visual rotation in degrees
        self.alive = True
        self.mode: Gamemode = "cube"

    @property
    def rect(self) -> pygame.Rect:
        """Axis-aligned hitbox used for collisions."""
        return pygame.Rect(int(self.x), int(self.y), int(self.size), int(self.size))

    def set_mode(self, mode: Gamemode) -> None:
        """Switch gamemode and clear grounded state for ship takeoff."""
        if mode == self.mode:
            return
        self.mode = mode
        self.on_ground = False
        if mode == "ship":
            # Nudge off the floor so the ship does not instantly crash.
            self.y = min(self.y, c.GROUND_Y - self.size - 8.0)
            self.vy = -120.0
            self.angle = 0.0
        else:
            self.angle = round(self.angle / 90.0) * 90.0

    def jump(self) -> None:
        """Cube jump when grounded (ignored in ship mode)."""
        if not self.alive or self.mode != "cube":
            return
        if self.on_ground:
            self.vy = c.JUMP_VELOCITY
            self.on_ground = False

    def update(
        self,
        dt: float,
        solid_tops: list[tuple[float, float, float]],
        *,
        holding: bool,
    ) -> None:
        """Integrate cube or ship physics for one frame."""
        if not self.alive:
            return
        if self.mode == "ship":
            self._update_ship(dt, holding)
        else:
            self._update_cube(dt, solid_tops)

    def _update_cube(
        self, dt: float, solid_tops: list[tuple[float, float, float]]
    ) -> None:
        """Jump physics with asymmetric gravity."""
        gravity = c.FALL_GRAVITY if self.vy > 0.0 else c.GRAVITY
        self.vy += gravity * dt
        self.y += self.vy * dt
        self.on_ground = False

        if self.y + self.size >= c.GROUND_Y and self.vy >= 0.0:
            self.y = c.GROUND_Y - self.size
            self.vy = 0.0
            self.on_ground = True
            self.angle = round(self.angle / 90.0) * 90.0

        if self.vy >= 0.0:
            foot = self.y + self.size
            for left, right, top in solid_tops:
                if self.x + self.size <= left or self.x >= right:
                    continue
                if foot >= top and foot - self.vy * dt <= top + 6.0:
                    self.y = top - self.size
                    self.vy = 0.0
                    self.on_ground = True
                    self.angle = round(self.angle / 90.0) * 90.0
                    break

        if not self.on_ground:
            self.angle = (self.angle + c.ROTATE_SPEED * dt) % 360.0

    def _update_ship(self, dt: float, holding: bool) -> None:
        """Hold to climb, release to dive — Geometry Dash ship feel."""
        accel = -c.SHIP_THRUST if holding else c.SHIP_GRAVITY
        self.vy += accel * dt
        self.vy = max(-c.SHIP_MAX_SPEED, min(c.SHIP_MAX_SPEED, self.vy))
        self.y += self.vy * dt
        self.on_ground = False

        # Visual tilt follows vertical speed.
        target = (self.vy / c.SHIP_MAX_SPEED) * c.SHIP_TILT_MAX
        self.angle += (target - self.angle) * min(1.0, 10.0 * dt)

    def kill(self) -> None:
        """Mark the icon as dead."""
        self.alive = False
        self.vy = 0.0

    def reset(self) -> None:
        """Restore the cube to the start pose."""
        self.y = c.GROUND_Y - self.size
        self.vy = 0.0
        self.on_ground = True
        self.angle = 0.0
        self.alive = True
        self.mode = "cube"

    def draw(self, surf: pygame.Surface) -> None:
        """Draw the cube or ship with the current tilt/spin."""
        if self.mode == "ship":
            self._draw_ship(surf)
        else:
            self._draw_cube(surf)

    def _draw_cube(self, surf: pygame.Surface) -> None:
        size = int(self.size)
        cube = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(cube, c.CUBE, pygame.Rect(0, 0, size, size), border_radius=4)
        pygame.draw.rect(
            cube, c.CUBE_EDGE, pygame.Rect(0, 0, size, size), width=3, border_radius=4
        )
        mid = size // 2
        pygame.draw.polygon(
            cube,
            (*c.CUBE_EDGE, 90),
            [(mid, 6), (size - 6, mid), (mid, size - 6), (6, mid)],
        )
        rotated = pygame.transform.rotate(cube, -self.angle)
        rect = rotated.get_rect(center=(self.x + self.size / 2, self.y + self.size / 2))
        surf.blit(rotated, rect)

    def _draw_ship(self, surf: pygame.Surface) -> None:
        w, h = int(self.size + 10), int(self.size)
        ship = pygame.Surface((w, h), pygame.SRCALPHA)
        # Fuselage
        pygame.draw.polygon(
            ship,
            c.SHIP,
            [(4, h // 2), (w - 2, 4), (w - 2, h - 4)],
        )
        pygame.draw.polygon(
            ship,
            c.SHIP_EDGE,
            [(4, h // 2), (w - 2, 4), (w - 2, h - 4)],
            width=2,
        )
        # Cockpit
        pygame.draw.circle(ship, c.SHIP_EDGE, (w - 12, h // 2), 5)
        # Wing
        pygame.draw.polygon(
            ship,
            (60, 140, 200),
            [(10, h // 2), (28, 2), (28, h - 2)],
        )
        rotated = pygame.transform.rotate(ship, -self.angle)
        rect = rotated.get_rect(center=(self.x + self.size / 2, self.y + self.size / 2))
        surf.blit(rotated, rect)
