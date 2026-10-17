"""Spike Troll gameplay: platforms, exit, random lethal spikes."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import pygame as pg

import config as c


@dataclass
class Spike:
    """A floor spike: warning flash, then solid and lethal."""

    rect: pg.Rect
    born_ms: int
    warning: bool = True

    def update(self, now_ms: int) -> bool:
        """Advance state. Return False when the spike should despawn."""
        age = now_ms - self.born_ms
        if self.warning and age >= c.WARNING_MS:
            self.warning = False
        if age >= c.WARNING_MS + c.SPIKE_LIFE_MS:
            return False
        return True

    def is_lethal(self) -> bool:
        return not self.warning

    def draw(self, surf: pg.Surface) -> None:
        color = c.WARNING if self.warning else c.SPIKE
        # Triangle spike pointing up
        mid_x = self.rect.centerx
        pts = [
            (self.rect.left, self.rect.bottom),
            (self.rect.right, self.rect.bottom),
            (mid_x, self.rect.top),
        ]
        pg.draw.polygon(surf, color, pts)
        if self.warning:
            # Pulsing outline
            pg.draw.polygon(surf, c.TEXT, pts, 2)


@dataclass
class LevelLayout:
    """Static geometry for one room."""

    floors: list[pg.Rect]
    platforms: list[pg.Rect]
    exit_rect: pg.Rect
    spawn: tuple[int, int]


def _layouts() -> list[LevelLayout]:
    """Three short troll rooms."""
    ground = pg.Rect(0, c.SCREEN_H - 48, c.SCREEN_W, 48)
    return [
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(180, 340, 140, 18),
                pg.Rect(420, 280, 140, 18),
            ],
            exit_rect=pg.Rect(c.SCREEN_W - 70, c.SCREEN_H - 48 - 64, 40, 64),
            spawn=(60, c.SCREEN_H - 48 - c.PLAYER_H),
        ),
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(120, 360, 100, 18),
                pg.Rect(300, 300, 100, 18),
                pg.Rect(480, 240, 100, 18),
                pg.Rect(620, 320, 120, 18),
            ],
            exit_rect=pg.Rect(c.SCREEN_W - 70, 320 - 64, 40, 64),
            spawn=(40, c.SCREEN_H - 48 - c.PLAYER_H),
        ),
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(90, 380, 90, 18),
                pg.Rect(250, 320, 90, 18),
                pg.Rect(410, 260, 90, 18),
                pg.Rect(560, 200, 90, 18),
                pg.Rect(680, 340, 100, 18),
            ],
            exit_rect=pg.Rect(c.SCREEN_W - 60, 340 - 64, 40, 64),
            spawn=(50, c.SCREEN_H - 48 - c.PLAYER_H),
        ),
    ]


@dataclass
class Game:
    """Owns player physics, spikes, and level flow."""

    level_index: int = 0
    won: bool = False
    dead: bool = False
    message: str = ""
    message_until: int = 0
    spikes: list[Spike] = field(default_factory=list)
    next_spike_ms: int = 0
    rng: random.Random = field(default_factory=random.Random)
    _layouts: list[LevelLayout] = field(default_factory=_layouts)

    x: float = 60.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = False
    coyote_until: int = 0
    jump_buffer_until: int = 0

    def __post_init__(self) -> None:
        self.reset_level(keep_message=False)

    @property
    def layout(self) -> LevelLayout:
        return self._layouts[self.level_index]

    @property
    def player_rect(self) -> pg.Rect:
        return pg.Rect(int(self.x), int(self.y), c.PLAYER_W, c.PLAYER_H)

    def reset_level(self, keep_message: bool = True) -> None:
        """Respawn player; clear spikes."""
        sx, sy = self.layout.spawn
        self.x, self.y = float(sx), float(sy)
        self.vx = self.vy = 0.0
        self.on_ground = True  # spawn stands on floor
        self.coyote_until = 0
        self.jump_buffer_until = 0
        self.spikes.clear()
        self.dead = False
        self.next_spike_ms = 0
        if not keep_message:
            self.message = ""

    def soft_kill(self, now_ms: int) -> None:
        """Troll death — restart current room."""
        self.dead = True
        self.message = "SPIKE GOT YOU — try again"
        self.message_until = now_ms + 1200
        self.reset_level(keep_message=True)

    def advance_level(self, now_ms: int) -> None:
        if self.level_index + 1 >= c.MAX_LEVEL:
            self.won = True
            self.message = "You survived the troll."
            return
        self.level_index += 1
        self.message = f"Level {self.level_index + 1} — spikes get meaner"
        self.message_until = now_ms + 1500
        self.reset_level(keep_message=True)

    def solids(self) -> list[pg.Rect]:
        return [*self.layout.floors, *self.layout.platforms]

    def _spawn_spike(self, now_ms: int) -> None:
        """Pick a random solid top edge and plant a spike."""
        surfaces = self.solids()
        surface = self.rng.choice(surfaces)
        # Keep off the exit pad a bit
        exit_r = self.layout.exit_rect
        for _ in range(12):
            w = 22
            left = self.rng.randint(surface.left, max(surface.left, surface.right - w))
            rect = pg.Rect(left, surface.top - 28, w, 28)
            # Don't spawn on player or exit
            if rect.colliderect(self.player_rect.inflate(40, 20)):
                continue
            if rect.colliderect(exit_r.inflate(30, 10)):
                continue
            self.spikes.append(Spike(rect=rect, born_ms=now_ms, warning=True))
            return

    def handle_input(self, keys: pg.key.ScancodeWrapper) -> None:
        if self.won:
            return
        self.vx = 0.0
        if keys[pg.K_a] or keys[pg.K_LEFT]:
            self.vx = -c.MOVE_SPEED
        if keys[pg.K_d] or keys[pg.K_RIGHT]:
            self.vx = c.MOVE_SPEED

    def request_jump(self, now_ms: int) -> None:
        """Queue a jump (Up / Space / W). Applied when grounded or in coyote."""
        if self.won or self.dead:
            return
        self.jump_buffer_until = now_ms + c.JUMP_BUFFER_MS
        self._try_consume_jump(now_ms)

    def _can_jump(self, now_ms: int) -> bool:
        return self.on_ground or now_ms <= self.coyote_until

    def _try_consume_jump(self, now_ms: int) -> None:
        if self.jump_buffer_until < now_ms:
            return
        if not self._can_jump(now_ms):
            return
        self.vy = c.JUMP_VEL
        self.on_ground = False
        self.coyote_until = 0
        self.jump_buffer_until = 0

    def _feet_on_solid(self) -> bool:
        """True if a solid sits just under the player's feet (no overlap required)."""
        feet = pg.Rect(
            int(self.x) + 2,
            int(self.y) + c.PLAYER_H,
            c.PLAYER_W - 4,
            c.FEET_PROBE,
        )
        return any(feet.colliderect(s) for s in self.solids())

    def update(self, dt: float, now_ms: int) -> None:
        if self.won:
            return

        if self.message and now_ms > self.message_until:
            self.message = ""

        # Schedule spikes
        interval = c.LEVEL_SPAWN_MS[self.level_index]
        if self.next_spike_ms == 0:
            self.next_spike_ms = now_ms + interval // 2
        elif now_ms >= self.next_spike_ms:
            self._spawn_spike(now_ms)
            jitter = self.rng.randint(-300, 400)
            self.next_spike_ms = now_ms + max(600, interval + jitter)

        # Spike lifecycle
        self.spikes = [s for s in self.spikes if s.update(now_ms)]

        # Physics — remember prior Y to resolve collision side correctly
        prev_bottom = self.y + c.PLAYER_H
        was_grounded = self.on_ground

        self.vy += c.GRAVITY * dt
        self.x += self.vx * dt
        self._resolve_x()
        self.y += self.vy * dt
        self._resolve_y(prev_bottom)

        # Feet probe catches "standing flush" cases colliderect misses
        if self.vy >= 0 and self._feet_on_solid():
            self.on_ground = True
            # Snap to surface so we don't sink
            for solid in self.solids():
                feet = pg.Rect(
                    int(self.x) + 2,
                    int(self.y) + c.PLAYER_H,
                    c.PLAYER_W - 4,
                    c.FEET_PROBE,
                )
                if feet.colliderect(solid):
                    self.y = solid.top - c.PLAYER_H
                    if self.vy > 0:
                        self.vy = 0
                    break

        if self.on_ground:
            self.coyote_until = now_ms + c.COYOTE_MS
        elif was_grounded and not self.on_ground and self.vy >= 0:
            # Walked off ledge — coyote already set while grounded
            pass

        # Buffered jump after landing
        self._try_consume_jump(now_ms)

        # Clamp to screen
        if self.x < 0:
            self.x = 0
        if self.x + c.PLAYER_W > c.SCREEN_W:
            self.x = c.SCREEN_W - c.PLAYER_W
        if self.y > c.SCREEN_H:
            self.soft_kill(now_ms)
            return

        # Spike kill
        pret = self.player_rect
        for spike in self.spikes:
            if spike.is_lethal() and pret.colliderect(spike.rect.inflate(-4, -2)):
                self.soft_kill(now_ms)
                return

        # Exit
        if pret.colliderect(self.layout.exit_rect):
            self.advance_level(now_ms)

    def _resolve_x(self) -> None:
        pret = self.player_rect
        for solid in self.solids():
            if pret.colliderect(solid):
                if self.vx > 0:
                    self.x = solid.left - c.PLAYER_W
                elif self.vx < 0:
                    self.x = solid.right
                pret = self.player_rect

    def _resolve_y(self, prev_bottom: float) -> None:
        """Resolve vertical hits using previous feet position (avoids canceling jumps)."""
        self.on_ground = False
        pret = self.player_rect
        for solid in self.solids():
            if not pret.colliderect(solid):
                continue
            # Landed on top: feet were at or above the surface before this step
            if prev_bottom <= solid.top + 1 and self.vy >= 0:
                self.y = solid.top - c.PLAYER_H
                self.vy = 0
                self.on_ground = True
            # Hit underside while rising
            elif self.vy < 0 and prev_bottom > solid.bottom:
                self.y = solid.bottom
                self.vy = 0
            # Fallback: push out by nearest vertical edge
            elif self.vy >= 0:
                self.y = solid.top - c.PLAYER_H
                self.vy = 0
                self.on_ground = True
            else:
                self.y = solid.bottom
                self.vy = 0
            pret = self.player_rect

    def draw(self, surf: pg.Surface, font: pg.font.Font, big: pg.font.Font) -> None:
        surf.fill(c.BG)
        for r in self.layout.floors:
            pg.draw.rect(surf, c.FLOOR, r)
        for r in self.layout.platforms:
            pg.draw.rect(surf, c.PLATFORM, r)
            pg.draw.rect(surf, (100, 120, 150), r, 2)

        # Exit door
        er = self.layout.exit_rect
        pg.draw.rect(surf, c.EXIT_C, er, border_radius=4)
        label = font.render("EXIT", True, c.BG)
        surf.blit(label, label.get_rect(center=er.center))

        for spike in self.spikes:
            spike.draw(surf)

        pg.draw.rect(surf, c.PLAYER, self.player_rect, border_radius=4)

        # HUD
        hud = font.render(
            f"Level {self.level_index + 1}/{c.MAX_LEVEL}   A/D move · Up arrow jump",
            True,
            c.HUD,
        )
        surf.blit(hud, (16, 12))
        hint = font.render("Yellow = warning. Red = death.", True, c.WARNING)
        surf.blit(hint, (16, 36))

        if self.message:
            msg = big.render(self.message, True, c.TEXT)
            surf.blit(msg, msg.get_rect(center=(c.SCREEN_W // 2, 80)))

        if self.won:
            overlay = pg.Surface((c.SCREEN_W, c.SCREEN_H), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            surf.blit(overlay, (0, 0))
            win = big.render("You survived the troll.", True, c.EXIT_C)
            sub = font.render("Close the window or press Esc to quit.", True, c.TEXT)
            surf.blit(win, win.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 - 20)))
            surf.blit(sub, sub.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 + 24)))
