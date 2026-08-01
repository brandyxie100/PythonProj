"""Core Geometry Dash–style gameplay loop for JUMP."""

from __future__ import annotations

import pygame

import config as c
from level import Obstacle, build_level, draw_obstacle
from player import Player


class Game:
    """One continuous auto-scrolling run with restart-on-death."""

    def __init__(self) -> None:
        """Load the course and reset run stats."""
        self._font = pygame.font.SysFont("Arial", 28, bold=True)
        self._small = pygame.font.SysFont("Arial", 18)
        self._huge = pygame.font.SysFont("Arial", 54, bold=True)
        self.player = Player()
        self.obstacles: list[Obstacle] = []
        self.finish_x = 0.0
        self.camera_x = 0.0
        self.attempts = 1
        self.best_progress = 0.0
        self.state: str = "playing"  # playing | dead | won
        self.death_timer = 0.0
        self._pulse = 0.0
        self._jump_held = False
        self._reset_level()

    def _reset_level(self) -> None:
        """Rebuild obstacles and put the camera / cube at the start."""
        self.obstacles, self.finish_x = build_level()
        self.camera_x = 0.0
        self.player.reset()
        self.state = "playing"
        self.death_timer = 0.0

    def progress(self) -> float:
        """Return completion ratio in ``0..1`` based on camera position."""
        if self.finish_x <= 1.0:
            return 0.0
        # Player world X ≈ camera + fixed screen X.
        world_x = self.camera_x + c.PLAYER_SCREEN_X
        return max(0.0, min(1.0, world_x / self.finish_x))

    def handle_event(self, event: pygame.event.Event) -> None:
        """Track jump hold; Space also restarts after death / win."""
        jump_keys = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
        if event.type == pygame.KEYUP and event.key in jump_keys:
            self._jump_held = False
            return
        if event.type != pygame.KEYDOWN or event.key not in jump_keys:
            return

        self._jump_held = True
        if self.state == "playing":
            self.player.jump()
        elif self.state == "dead" and self.death_timer <= 0.0:
            self.attempts += 1
            self._reset_level()
        elif self.state == "won":
            self.attempts += 1
            self._reset_level()

    def update(self, dt: float) -> None:
        """Advance scroll, physics, and win/lose checks."""
        self._pulse += dt
        # Keep hold state in sync even if KEYUP was missed (focus loss, etc.).
        keys = pygame.key.get_pressed()
        self._jump_held = bool(
            keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        )

        if self.state == "dead":
            self.death_timer = max(0.0, self.death_timer - dt)
            return
        if self.state == "won":
            return

        self.camera_x += c.SCROLL_SPEED * dt

        # Collect platform tops in screen space for landing.
        solid_tops: list[tuple[float, float, float]] = []
        for obs in self.obstacles:
            if obs.kind != "block":
                continue
            rect = obs.screen_rect(self.camera_x)
            solid_tops.append((float(rect.left), float(rect.right), float(rect.top)))

        self.player.update(dt, solid_tops)
        # Hold Space → bounce again the instant you touch ground (GD-style).
        if self._jump_held and self.player.on_ground:
            self.player.jump()
        self._resolve_collisions()

        pct = self.progress()
        self.best_progress = max(self.best_progress, pct)
        if pct >= 1.0:
            self.state = "won"

    def _resolve_collisions(self) -> None:
        """Kill the cube on spikes or unsafe block contact."""
        prect = self.player.rect
        # Slightly shrink hitbox so jumps feel fair (classic GD feel).
        hit = prect.inflate(-6, -6)

        for obs in self.obstacles:
            rect = obs.screen_rect(self.camera_x)
            if not hit.colliderect(rect):
                continue

            if obs.kind == "spike":
                self._die()
                return

            # Block: safe if standing on top; otherwise lethal.
            foot = prect.bottom
            on_top = (
                self.player.vy >= 0.0
                and foot <= rect.top + 10
                and prect.right > rect.left + 4
                and prect.left < rect.right - 4
            )
            if on_top:
                continue
            self._die()
            return

    def _die(self) -> None:
        """Enter the death state with a short pause before restart."""
        if self.state != "playing":
            return
        self.player.kill()
        self.state = "dead"
        self.death_timer = c.DEATH_FLASH_TIME

    def draw(self, surf: pygame.Surface) -> None:
        """Render background, course, cube, and HUD."""
        self._draw_background(surf)
        self._draw_ground(surf)
        for obs in self.obstacles:
            draw_obstacle(surf, obs, self.camera_x)
        self._draw_finish(surf)
        if self.player.alive:
            self.player.draw(surf)
        else:
            self._draw_death_burst(surf)
        self._draw_hud(surf)
        if self.state == "dead" and self.death_timer <= 0.0:
            self._draw_center_banner(surf, "CRASHED", "Press SPACE to retry")
        elif self.state == "won":
            self._draw_center_banner(surf, "COMPLETE!", "Press SPACE to run again")

    def _draw_background(self, surf: pygame.Surface) -> None:
        for y in range(c.SCREEN_H):
            t = y / c.SCREEN_H
            color = tuple(
                int(c.BG_TOP[i] + (c.BG_BOTTOM[i] - c.BG_TOP[i]) * t) for i in range(3)
            )
            pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))

        # Parallax grid lines scrolling with the camera.
        spacing = 48
        offset = int(self.camera_x * 0.35) % spacing
        for x in range(-offset, c.SCREEN_W + spacing, spacing):
            pygame.draw.line(surf, (28, 34, 70), (x, 0), (x, int(c.GROUND_Y)))
        for y in range(40, int(c.GROUND_Y), spacing):
            pygame.draw.line(surf, (28, 34, 70), (0, y), (c.SCREEN_W, y))

    def _draw_ground(self, surf: pygame.Surface) -> None:
        pygame.draw.rect(
            surf,
            c.GROUND,
            pygame.Rect(0, int(c.GROUND_Y), c.SCREEN_W, c.SCREEN_H - int(c.GROUND_Y)),
        )
        pygame.draw.line(
            surf, c.GROUND_LINE, (0, int(c.GROUND_Y)), (c.SCREEN_W, int(c.GROUND_Y)), 3
        )
        # Moving ground ticks.
        tick = 40
        off = int(self.camera_x) % tick
        for x in range(-off, c.SCREEN_W + tick, tick):
            pygame.draw.line(
                surf,
                (60, 70, 120),
                (x, int(c.GROUND_Y) + 8),
                (x, int(c.GROUND_Y) + 22),
                2,
            )

    def _draw_finish(self, surf: pygame.Surface) -> None:
        fx = int(self.finish_x - self.camera_x)
        if -20 < fx < c.SCREEN_W + 20:
            pygame.draw.line(
                surf, c.STAR, (fx, int(c.GROUND_Y) - 120), (fx, int(c.GROUND_Y)), 4
            )
            # Checkered flag stripes.
            for i in range(6):
                color = c.STAR if i % 2 == 0 else (30, 30, 40)
                pygame.draw.rect(
                    surf, color, pygame.Rect(fx, int(c.GROUND_Y) - 120 + i * 12, 28, 12)
                )

    def _draw_death_burst(self, surf: pygame.Surface) -> None:
        """Simple expanding ring where the cube died."""
        cx = int(self.player.x + self.player.size / 2)
        cy = int(self.player.y + self.player.size / 2)
        t = 1.0 - (self.death_timer / c.DEATH_FLASH_TIME)
        radius = int(10 + t * 50)
        alpha = max(0, int(220 * (1.0 - t)))
        ring = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*c.SPIKE, alpha), (radius + 2, radius + 2), radius, 4)
        surf.blit(ring, (cx - radius - 2, cy - radius - 2))

    def _draw_hud(self, surf: pygame.Surface) -> None:
        pct = self.progress()
        bar = pygame.Rect(80, 24, c.SCREEN_W - 160, 14)
        pygame.draw.rect(surf, c.PROGRESS_BG, bar, border_radius=7)
        fill_w = int(bar.w * pct)
        if fill_w > 0:
            pygame.draw.rect(
                surf,
                c.PROGRESS_FILL,
                pygame.Rect(bar.x, bar.y, fill_w, bar.h),
                border_radius=7,
            )
        pygame.draw.rect(surf, c.UI_DIM, bar, width=2, border_radius=7)

        label = self._small.render(f"{int(pct * 100)}%", True, c.UI)
        surf.blit(label, (bar.right + 10, bar.y - 2))

        att = self._small.render(f"Attempt {self.attempts}", True, c.UI_DIM)
        surf.blit(att, (20, 50))
        best = self._small.render(
            f"Best {int(self.best_progress * 100)}%", True, c.UI_DIM
        )
        surf.blit(best, (20, 72))

        hint = self._small.render("HOLD SPACE = keep jumping", True, c.UI_DIM)
        surf.blit(hint, (c.SCREEN_W - hint.get_width() - 20, 50))

        title = self._font.render("JUMP", True, c.GROUND_LINE)
        surf.blit(title, (20, 16))

    def _draw_center_banner(self, surf: pygame.Surface, title: str, subtitle: str) -> None:
        overlay = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surf.blit(overlay, (0, 0))
        t = self._huge.render(title, True, c.UI)
        s = self._font.render(subtitle, True, c.UI_DIM)
        surf.blit(t, t.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 - 24)))
        surf.blit(s, s.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 + 36)))
