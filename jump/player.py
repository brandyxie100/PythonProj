"""Player cube for JUMP."""

from __future__ import annotations

import pygame

import config as c


class Player:
    """Auto-running cube that jumps with Space when grounded."""

    def __init__(self) -> None:
        """Place the cube on the ground at the fixed screen X."""
        self.size = c.CUBE_SIZE
        self.x = c.PLAYER_SCREEN_X
        self.y = c.GROUND_Y - self.size
        self.vy = 0.0
        self.on_ground = True
        self.angle = 0.0  # visual rotation in degrees
        self.alive = True

    @property
    def rect(self) -> pygame.Rect:
        """Axis-aligned hitbox used for collisions."""
        return pygame.Rect(int(self.x), int(self.y), int(self.size), int(self.size))

    def jump(self) -> None:
        """Launch upward if standing on ground or a platform."""
        if self.alive and self.on_ground:
            self.vy = c.JUMP_VELOCITY
            self.on_ground = False

    def update(self, dt: float, solid_tops: list[tuple[float, float, float]]) -> None:
        """Integrate gravity and land on the ground or platform tops.

        ``solid_tops`` is a list of ``(left, right, top_y)`` screen-space
        rectangles the cube may stand on.
        """
        if not self.alive:
            return

        # Stronger gravity while falling makes the cube snap back to the ground.
        gravity = c.FALL_GRAVITY if self.vy > 0.0 else c.GRAVITY
        self.vy += gravity * dt
        self.y += self.vy * dt
        self.on_ground = False

        # Ground plane.
        if self.y + self.size >= c.GROUND_Y and self.vy >= 0.0:
            self.y = c.GROUND_Y - self.size
            self.vy = 0.0
            self.on_ground = True
            self.angle = round(self.angle / 90.0) * 90.0

        # Platform tops (land only when falling onto them).
        if self.vy >= 0.0:
            foot = self.y + self.size
            for left, right, top in solid_tops:
                if self.x + self.size <= left or self.x >= right:
                    continue
                # Accept a landing if the foot crossed the top this frame.
                if foot >= top and foot - self.vy * dt <= top + 6.0:
                    self.y = top - self.size
                    self.vy = 0.0
                    self.on_ground = True
                    self.angle = round(self.angle / 90.0) * 90.0
                    break

        if not self.on_ground:
            self.angle = (self.angle + c.ROTATE_SPEED * dt) % 360.0

    def kill(self) -> None:
        """Mark the cube as dead."""
        self.alive = False
        self.vy = 0.0

    def reset(self) -> None:
        """Restore the cube to the start pose."""
        self.y = c.GROUND_Y - self.size
        self.vy = 0.0
        self.on_ground = True
        self.angle = 0.0
        self.alive = True

    def draw(self, surf: pygame.Surface) -> None:
        """Draw a rotating neon cube."""
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
