"""Core Geometry Dash–style gameplay loop for JUMP."""

from __future__ import annotations

import pygame

import config as c
from level import Obstacle, build_level, draw_obstacle, draw_orb, draw_portal
from player import Player


class Game:
    """One continuous auto-scrolling run with restart-on-death."""

    def __init__(self, level_index: Optional[int] = None, start_mode: str = "cube") -> None:
        """Load the course and reset run stats."""
        self._font = pygame.font.SysFont("Arial", 28, bold=True)
        self._small = pygame.font.SysFont("Arial", 18)
        self._huge = pygame.font.SysFont("Arial", 54, bold=True)
        self.player = Player()
        self.obstacles: list[Obstacle] = []
        self.portals = []
        self.orbs = []
        self.finish_x = 0.0
        self.current_level_name = ""
        self.camera_x = 0.0
        self.attempts = 1
        self.best_progress = 0.0
        self.state: str = "playing"
        self.death_timer = 0.0
        self._pulse = 0.0
        self._jump_held = False
        self.request_menu = False
        self._selected_level_index = level_index
        self._start_mode = start_mode
        self._reset_level()

    def _reset_level(self) -> None:
        """Rebuild obstacles/portals/orbs and put the camera / icon at the start."""
        self.obstacles, self.portals, self.orbs, self.finish_x, self.current_level_name = build_level(
            self._selected_level_index
        )
        self.camera_x = 0.0
        self.player.reset()
        if self._start_mode != "cube":
            self.player.set_mode(self._start_mode)
        self.state = "playing"
        self.death_timer = 0.0
        self.request_menu = False

    def progress(self) -> float:
        """Return completion ratio in ``0..1`` based on camera position."""
        if self.finish_x <= 1.0:
            return 0.0
        world_x = self.camera_x + c.PLAYER_SCREEN_X
        return max(0.0, min(1.0, world_x / self.finish_x))

    def handle_event(self, event: pygame.event.Event) -> None:
        """Track hold for ship; Space activates mode action / retry; Esc → menu."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.request_menu = True
            return

        jump_keys = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
        if event.type == pygame.KEYUP and event.key in jump_keys:
            self._jump_held = False
            return
        if event.type != pygame.KEYDOWN or event.key not in jump_keys:
            return

        self._jump_held = True
        if self.state == "playing":
            self.player.jump()
            self._try_orbs()
        elif self.state == "dead" and self.death_timer <= 0.0:
            self.attempts += 1
            self._reset_level()
        elif self.state == "won":
            self.attempts += 1
            self._reset_level()

    def update(self, dt: float) -> None:
        """Advance scroll, physics, portals, and win/lose checks."""
        self._pulse += dt
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
        self._check_portals()

        solid_tops: list[tuple[float, float, float]] = [
            (0.0, float(c.SCREEN_W), float(c.GROUND_Y))
        ]
        solid_bottoms: list[tuple[float, float, float]] = [
            (0.0, float(c.SCREEN_W), float(c.CEILING_Y))
        ]
        slope_surfaces: list[tuple[float, float, float, float, str]] = []
        if self.player.mode in ("cube", "ball", "ship", "ufo", "wave"):
            for obs in self.obstacles:
                if obs.kind == "block":
                    rect = obs.screen_rect(self.camera_x)
                    solid_tops.append(
                        (float(rect.left), float(rect.right), float(rect.top))
                    )
                    solid_bottoms.append(
                        (float(rect.left), float(rect.right), float(rect.bottom))
                    )
                elif obs.kind == "slope":
                    rect = obs.screen_rect(self.camera_x)
                    slope_surfaces.append(
                        (
                            float(rect.left),
                            float(rect.right),
                            float(rect.top),
                            float(rect.bottom),
                            obs.slope_dir,
                        )
                    )

        self.player.update(
            dt,
            solid_tops,
            solid_bottoms,
            slope_surfaces,
            holding=self._jump_held,
        )
        self._try_orbs()
        # Cube hold-to-rebounce (ship uses continuous hold thrust instead).
        if (
            self.player.mode == "cube"
            and self._jump_held
            and self.player.on_ground
        ):
            self.player.jump()
        self._resolve_collisions()

        pct = self.progress()
        self.best_progress = max(self.best_progress, pct)
        if pct >= 1.0:
            self.state = "won"

    def _try_orbs(self) -> None:
        """Activate an overlapping orb when a click was buffered recently."""
        if self.player.click_buffer <= 0.0:
            return
        hit = self.player.hitbox
        for orb in self.orbs:
            if orb.used:
                continue
            if hit.colliderect(orb.hit_rect(self.camera_x)):
                orb.used = True
                self.player.activate_orb(orb.kind)
                return

    def _check_portals(self) -> None:
        """Switch gamemode when the icon crosses an unused portal."""
        world_x = self.camera_x + c.PLAYER_SCREEN_X + self.player.size * 0.5
        for portal in self.portals:
            if portal.triggered:
                continue
            if world_x >= portal.x:
                portal.triggered = True
                self.player.set_mode(portal.mode)

    def _safe_on_slope(self, obs: Obstacle, prect: pygame.Rect) -> bool:
        if self.player.mode in ("ship", "ufo"):
            return False
        if self.player.mode == "ball" and self.player.gravity_dir < 0.0:
            return False

        slope_y = obs.slope_y_at(self.camera_x, prect.centerx)
        if slope_y is None:
            return False

        drawn = obs.screen_rect(self.camera_x)
        if (
            self.player.vy >= 0.0
            and prect.bottom >= slope_y - 2
            and prect.bottom <= slope_y + 12
            and prect.right > drawn.left + 4
            and prect.left < drawn.right - 4
        ):
            return True
        return False

    def _needs_ceiling(self) -> bool:
        """Ceiling is active for ship, inverted ball, UFO, and wave flight."""
        return self.player.mode in ("ship", "ball", "ufo", "wave")

    def _resolve_collisions(self) -> None:
        """Kill on spikes, unsafe blocks, or bound hits for flight modes."""
        mode = self.player.mode

        if mode == "ball" or mode == "wave":
            # Ball and wave may travel up and down; crushing past bounds kills.
            if self.player.y + self.player.size > c.GROUND_Y + 2:
                self._die()
                return
            if self.player.y < c.CEILING_Y - 2:
                self._die()
                return

        prect = self.player.rect
        hit = self.player.hitbox

        for obs in self.obstacles:
            rect = obs.hit_rect(self.camera_x)
            if not hit.colliderect(rect):
                continue

            if obs.kind == "spike":
                self._die()
                return

            if obs.kind == "slope":
                continue

            drawn = obs.screen_rect(self.camera_x)
            if mode == "ball" and self.player.gravity_dir < 0.0:
                on_ceiling_side = (
                    self.player.vy <= 0.0
                    and prect.top >= drawn.bottom - 10
                    and prect.right > drawn.left + 4
                    and prect.left < drawn.right - 4
                )
                if on_ceiling_side:
                    continue
                self._die()
                return

            foot = prect.bottom
            on_top = (
                self.player.vy >= 0.0
                and foot <= drawn.top + 10
                and prect.right > drawn.left + 4
                and prect.left < drawn.right - 4
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
        """Render background, course, icon, and HUD."""
        self._draw_background(surf)
        self._draw_ground(surf)
        if self._needs_ceiling():
            self._draw_ceiling(surf)
        for portal in self.portals:
            draw_portal(surf, portal, self.camera_x, self._pulse)
        for orb in self.orbs:
            draw_orb(surf, orb, self.camera_x, self._pulse)
        for obs in self.obstacles:
            draw_obstacle(surf, obs, self.camera_x)
        self._draw_finish(surf)
        if self.player.alive:
            self.player.draw(surf)
        else:
            self._draw_death_burst(surf)
        self._draw_hud(surf)
        if self.state == "dead" and self.death_timer <= 0.0:
            self._draw_center_banner(
                surf, "CRASHED", "SPACE retry  ·  Esc menu"
            )
        elif self.state == "won":
            self._draw_center_banner(
                surf, "COMPLETE!", "SPACE again  ·  Esc menu"
            )

    def _draw_background(self, surf: pygame.Surface) -> None:
        for y in range(c.SCREEN_H):
            t = y / c.SCREEN_H
            color = tuple(
                int(c.BG_TOP[i] + (c.BG_BOTTOM[i] - c.BG_TOP[i]) * t) for i in range(3)
            )
            pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))
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

    def _draw_ceiling(self, surf: pygame.Surface) -> None:
        pygame.draw.rect(
            surf, c.GROUND, pygame.Rect(0, 0, c.SCREEN_W, int(c.CEILING_Y))
        )
        pygame.draw.line(
            surf,
            c.CEILING_LINE,
            (0, int(c.CEILING_Y)),
            (c.SCREEN_W, int(c.CEILING_Y)),
            3,
        )

    def _draw_finish(self, surf: pygame.Surface) -> None:
        fx = int(self.finish_x - self.camera_x)
        if -20 < fx < c.SCREEN_W + 20:
            pygame.draw.line(
                surf, c.STAR, (fx, int(c.GROUND_Y) - 120), (fx, int(c.GROUND_Y)), 4
            )
            for i in range(6):
                color = c.STAR if i % 2 == 0 else (30, 30, 40)
                pygame.draw.rect(
                    surf, color, pygame.Rect(fx, int(c.GROUND_Y) - 120 + i * 12, 28, 12)
                )

    def _draw_death_burst(self, surf: pygame.Surface) -> None:
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

        mode = self.player.mode
        mode_color = c.PORTAL_COLORS[mode]
        mode_txt = self._small.render(f"MODE: {mode.upper()}", True, mode_color)
        surf.blit(mode_txt, (20, 94))

        hints = {
            "cube": "SPACE jump · tap again mid-air for double jump",
            "ship": "HOLD = fly up  ·  RELEASE = fly down",
            "ball": "SPACE = invert gravity",
            "ufo": "SPACE = jump anytime (2 blocks)",
            "wave": "SPACE to reverse vertical direction",
        }
        hint = self._small.render(hints[mode], True, c.UI_DIM)
        surf.blit(hint, (c.SCREEN_W - hint.get_width() - 20, 50))

        title = self._font.render(self.current_level_name or "UNKNOWN LEVEL", True, c.GROUND_LINE)
        surf.blit(title, (20, 16))

    def _draw_center_banner(
        self, surf: pygame.Surface, title: str, subtitle: str
    ) -> None:
        overlay = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surf.blit(overlay, (0, 0))
        t = self._huge.render(title, True, c.UI)
        s = self._font.render(subtitle, True, c.UI_DIM)
        surf.blit(t, t.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 - 24)))
        surf.blit(s, s.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 + 36)))
