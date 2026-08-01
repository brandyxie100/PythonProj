"""Player icons: cube, ship, ball, and UFO gamemodes."""

from __future__ import annotations

import math
from typing import Literal

import pygame

import config as c

Gamemode = Literal["cube", "ship", "ball", "ufo"]


class Player:
    """Auto-running icon that switches gamemode through portals."""

    def __init__(self) -> None:
        """Place the icon on the ground at the fixed screen X."""
        self.size = c.CUBE_SIZE
        self.x = c.PLAYER_SCREEN_X
        self.y = c.GROUND_Y - self.size
        self.vy = 0.0
        self.on_ground = True
        self.angle = 0.0
        self.alive = True
        self.mode: Gamemode = "cube"
        self.gravity_dir: float = 1.0  # +1 normal, -1 inverted (ball)

    @property
    def rect(self) -> pygame.Rect:
        """Axis-aligned hitbox used for collisions."""
        return pygame.Rect(int(self.x), int(self.y), int(self.size), int(self.size))

    def set_mode(self, mode: Gamemode) -> None:
        """Switch gamemode and set a safe starting pose."""
        if mode == self.mode:
            return
        self.mode = mode
        self.gravity_dir = 1.0
        self.on_ground = False
        if mode == "ship":
            # Lift off so the ship does not instantly kiss the floor.
            self.y = min(self.y, c.GROUND_Y - self.size - 10.0)
            self.y = max(self.y, c.CEILING_Y + 10.0)
            self.vy = -80.0
            self.angle = 0.0
        elif mode == "ball":
            self.angle = 0.0
            # Keep current height; ball can stick to floor or ceiling.
            if self.y + self.size >= c.GROUND_Y - 2:
                self.on_ground = True
                self.y = c.GROUND_Y - self.size
            elif self.y <= c.CEILING_Y + 2:
                self.on_ground = True
                self.y = c.CEILING_Y
                self.gravity_dir = -1.0
        elif mode == "ufo":
            self.y = min(self.y, c.GROUND_Y - self.size - 6.0)
            self.vy = 0.0
            self.angle = 0.0
        else:
            self.angle = round(self.angle / 90.0) * 90.0

    def jump(self) -> None:
        """Apply the click/tap action for the current gamemode."""
        if not self.alive:
            return
        if self.mode == "cube":
            if self.on_ground:
                self.vy = c.JUMP_VELOCITY
                self.on_ground = False
        elif self.mode == "ball":
            # Invert gravity — ball falls the other way.
            self.gravity_dir *= -1.0
            self.on_ground = False
            self.vy = 0.0
        elif self.mode == "ufo":
            # Mid-air jump allowed (flappy / GD UFO).
            self.vy = c.UFO_JUMP_VELOCITY
            self.on_ground = False
        # Ship ignores taps — it is hold-controlled.

    def update(
        self,
        dt: float,
        solid_tops: list[tuple[float, float, float]],
        solid_bottoms: list[tuple[float, float, float]],
        *,
        holding: bool,
    ) -> None:
        """Integrate physics for the active gamemode."""
        if not self.alive:
            return
        if self.mode == "ship":
            self._update_ship(dt, holding)
        elif self.mode == "ball":
            self._update_ball(dt, solid_tops, solid_bottoms)
        elif self.mode == "ufo":
            self._update_ufo(dt)
        else:
            self._update_cube(dt, solid_tops)

    def _update_cube(
        self, dt: float, solid_tops: list[tuple[float, float, float]]
    ) -> None:
        """Click to jump 2 blocks when grounded."""
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
        """Hold Space → fly up; release → fly down."""
        accel = -c.SHIP_THRUST if holding else c.SHIP_GRAVITY
        self.vy += accel * dt
        self.vy = max(-c.SHIP_MAX_SPEED, min(c.SHIP_MAX_SPEED, self.vy))
        self.y += self.vy * dt
        self.on_ground = False
        target = (self.vy / c.SHIP_MAX_SPEED) * c.SHIP_TILT_MAX
        self.angle += (target - self.angle) * min(1.0, 10.0 * dt)

    def _update_ball(
        self,
        dt: float,
        solid_tops: list[tuple[float, float, float]],
        solid_bottoms: list[tuple[float, float, float]],
    ) -> None:
        """Gravity toward floor or ceiling; click flips direction."""
        g = c.GRAVITY * self.gravity_dir
        # Fall gravity when moving with gravity.
        if self.vy * self.gravity_dir > 0.0:
            g = c.FALL_GRAVITY * self.gravity_dir
        self.vy += g * dt
        self.y += self.vy * dt
        self.on_ground = False
        self.angle = (self.angle + c.BALL_SPIN_SPEED * dt * self.gravity_dir) % 360.0

        if self.gravity_dir > 0.0:
            if self.y + self.size >= c.GROUND_Y and self.vy >= 0.0:
                self.y = c.GROUND_Y - self.size
                self.vy = 0.0
                self.on_ground = True
            if self.vy >= 0.0:
                foot = self.y + self.size
                for left, right, top in solid_tops:
                    if self.x + self.size <= left or self.x >= right:
                        continue
                    if foot >= top and foot - self.vy * dt <= top + 6.0:
                        self.y = top - self.size
                        self.vy = 0.0
                        self.on_ground = True
                        break
        else:
            if self.y <= c.CEILING_Y and self.vy <= 0.0:
                self.y = c.CEILING_Y
                self.vy = 0.0
                self.on_ground = True
            if self.vy <= 0.0:
                head = self.y
                for left, right, bottom in solid_bottoms:
                    if self.x + self.size <= left or self.x >= right:
                        continue
                    if head <= bottom and head - self.vy * dt >= bottom - 6.0:
                        self.y = bottom
                        self.vy = 0.0
                        self.on_ground = True
                        break

    def _update_ufo(self, dt: float) -> None:
        """Click jumps 2 blocks anytime; gravity pulls down between clicks."""
        gravity = c.FALL_GRAVITY if self.vy > 0.0 else c.GRAVITY
        self.vy += gravity * dt
        self.y += self.vy * dt
        self.on_ground = False
        if self.y + self.size >= c.GROUND_Y and self.vy >= 0.0:
            self.y = c.GROUND_Y - self.size
            self.vy = 0.0
            self.on_ground = True
        # Soft bob tilt
        self.angle = max(-25.0, min(25.0, self.vy * 0.04))

    def kill(self) -> None:
        """Mark the icon as dead."""
        self.alive = False
        self.vy = 0.0

    def reset(self) -> None:
        """Restore the cube at the start of the level."""
        self.y = c.GROUND_Y - self.size
        self.vy = 0.0
        self.on_ground = True
        self.angle = 0.0
        self.alive = True
        self.mode = "cube"
        self.gravity_dir = 1.0

    def draw(self, surf: pygame.Surface) -> None:
        """Draw the active icon."""
        drawers = {
            "cube": self._draw_cube,
            "ship": self._draw_ship,
            "ball": self._draw_ball,
            "ufo": self._draw_ufo,
        }
        drawers[self.mode](surf)

    def _blit_rotated(
        self, surf: pygame.Surface, sprite: pygame.Surface, angle: float
    ) -> None:
        rotated = pygame.transform.rotate(sprite, -angle)
        rect = rotated.get_rect(center=(self.x + self.size / 2, self.y + self.size / 2))
        surf.blit(rotated, rect)

    def _draw_cube(self, surf: pygame.Surface) -> None:
        size = int(self.size)
        cube = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(cube, c.CUBE_EDGE, pygame.Rect(0, 0, size, size), border_radius=3)
        pygame.draw.rect(
            cube, c.CUBE, pygame.Rect(3, 3, size - 6, size - 6), border_radius=2
        )
        inner = size // 3
        pygame.draw.rect(
            cube,
            c.CUBE_CORE,
            pygame.Rect(size // 2 - inner // 2, size // 2 - inner // 2, inner, inner),
            border_radius=2,
        )
        pygame.draw.circle(cube, (255, 255, 255), (size // 2, size // 2), 2)
        self._blit_rotated(surf, cube, self.angle)

    def _draw_ship(self, surf: pygame.Surface) -> None:
        """Blocky spaceship matching the reference icon."""
        w, h = int(self.size + 14), int(self.size)
        ship = pygame.Surface((w, h), pygame.SRCALPHA)
        # Nose
        pygame.draw.polygon(
            ship, c.SHIP, [(w - 2, h // 2), (w - 14, 4), (w - 14, h - 4)]
        )
        pygame.draw.polygon(
            ship, c.SHIP_EDGE, [(w - 2, h // 2), (w - 14, 4), (w - 14, h - 4)], 2
        )
        # Body
        body = pygame.Rect(10, 6, w - 26, h - 12)
        pygame.draw.rect(ship, c.SHIP, body, border_radius=2)
        pygame.draw.rect(ship, c.SHIP_EDGE, body, width=2, border_radius=2)
        # Cockpit window
        pygame.draw.rect(
            ship, c.SHIP_WINDOW, pygame.Rect(body.centerx - 6, body.y + 4, 12, body.h - 8)
        )
        # Tail fins
        pygame.draw.rect(ship, c.SHIP, pygame.Rect(2, 2, 10, 8))
        pygame.draw.rect(ship, c.SHIP, pygame.Rect(2, h - 10, 10, 8))
        pygame.draw.rect(ship, c.SHIP_EDGE, pygame.Rect(2, 2, 10, 8), 1)
        pygame.draw.rect(ship, c.SHIP_EDGE, pygame.Rect(2, h - 10, 10, 8), 1)
        self._blit_rotated(surf, ship, self.angle)

    def _draw_ball(self, surf: pygame.Surface) -> None:
        """Gear / buzzsaw ball."""
        size = int(self.size + 4)
        ball = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        r = size // 2 - 1
        teeth = 10
        points: list[tuple[int, int]] = []
        for i in range(teeth * 2):
            ang = math.pi * i / teeth
            rad = r if i % 2 == 0 else r - 5
            points.append((cx + int(math.cos(ang) * rad), cy + int(math.sin(ang) * rad)))
        pygame.draw.polygon(ball, c.BALL, points)
        pygame.draw.polygon(ball, c.BALL_EDGE, points, 2)
        pygame.draw.circle(ball, c.BALL_CORE, (cx, cy), r // 2)
        pygame.draw.circle(ball, c.BALL_EDGE, (cx, cy), r // 2, 2)
        self._blit_rotated(surf, ball, self.angle)

    def _draw_ufo(self, surf: pygame.Surface) -> None:
        """Classic saucer UFO."""
        w, h = int(self.size + 12), int(self.size)
        ufo = pygame.Surface((w, h), pygame.SRCALPHA)
        # Dome
        pygame.draw.ellipse(ufo, c.UFO_DOME, pygame.Rect(w // 2 - 10, 2, 20, 16))
        pygame.draw.ellipse(ufo, c.UFO_EDGE, pygame.Rect(w // 2 - 10, 2, 20, 16), 2)
        # Saucer body
        pygame.draw.ellipse(ufo, c.UFO, pygame.Rect(2, h // 2 - 6, w - 4, 18))
        pygame.draw.ellipse(ufo, c.UFO_EDGE, pygame.Rect(2, h // 2 - 6, w - 4, 18), 2)
        pygame.draw.circle(ufo, (255, 255, 255), (w // 2, h // 2 + 2), 4)
        self._blit_rotated(surf, ufo, self.angle)
