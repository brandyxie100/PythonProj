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
    warning_ms: int = 700
    warning: bool = True

    def update(self, now_ms: int) -> bool:
        """Advance state. Return False when the spike should despawn."""
        age = now_ms - self.born_ms
        if self.warning and age >= self.warning_ms:
            self.warning = False
        if age >= self.warning_ms + c.SPIKE_LIFE_MS:
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
    """Ten rooms: easy → almost-impossible (still jumpable gaps)."""
    g = c.SCREEN_H - 48  # ground top
    ground = pg.Rect(0, g, c.SCREEN_W, 48)
    spawn_y = g - c.PLAYER_H

    def door(x: int, stand_top: int) -> pg.Rect:
        return pg.Rect(x, stand_top - 64, 40, 64)

    return [
        # 1 Warmup — flat walk to exit
        LevelLayout(
            floors=[ground],
            platforms=[],
            exit_rect=door(c.SCREEN_W - 70, g),
            spawn=(50, spawn_y),
        ),
        # 2 Stroll — one easy step
        LevelLayout(
            floors=[ground],
            platforms=[pg.Rect(280, 360, 180, 18)],
            exit_rect=door(c.SCREEN_W - 70, g),
            spawn=(50, spawn_y),
        ),
        # 3 Hop — two wide platforms
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(180, 360, 150, 18),
                pg.Rect(420, 300, 150, 18),
            ],
            exit_rect=door(c.SCREEN_W - 70, g),
            spawn=(50, spawn_y),
        ),
        # 4 Climb — exit on mid ledge
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(140, 360, 120, 18),
                pg.Rect(320, 300, 120, 18),
                pg.Rect(500, 250, 140, 18),
                pg.Rect(680, 250, 100, 18),
            ],
            exit_rect=door(c.SCREEN_W - 70, 250),
            spawn=(40, spawn_y),
        ),
        # 5 Zigzag — up then across
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(100, 380, 100, 18),
                pg.Rect(260, 320, 100, 18),
                pg.Rect(420, 260, 100, 18),
                pg.Rect(580, 210, 100, 18),
                pg.Rect(700, 280, 90, 18),
            ],
            exit_rect=door(c.SCREEN_W - 60, 280),
            spawn=(40, spawn_y),
        ),
        # 6 Narrow — thinner platforms
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(110, 370, 80, 18),
                pg.Rect(250, 310, 70, 18),
                pg.Rect(390, 255, 70, 18),
                pg.Rect(530, 200, 70, 18),
                pg.Rect(670, 255, 90, 18),
            ],
            exit_rect=door(c.SCREEN_W - 55, 255),
            spawn=(40, spawn_y),
        ),
        # 7 Gauntlet — longer path, mid heights
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(80, 390, 70, 18),
                pg.Rect(200, 340, 70, 18),
                pg.Rect(320, 290, 70, 18),
                pg.Rect(440, 240, 70, 18),
                pg.Rect(560, 190, 70, 18),
                pg.Rect(680, 240, 80, 18),
                pg.Rect(680, 340, 80, 18),
            ],
            exit_rect=door(c.SCREEN_W - 55, 340),
            spawn=(30, spawn_y),
        ),
        # 8 Pressure — tight staircase to high exit
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(90, 390, 65, 18),
                pg.Rect(200, 340, 60, 18),
                pg.Rect(310, 290, 60, 18),
                pg.Rect(420, 240, 60, 18),
                pg.Rect(530, 190, 60, 18),
                pg.Rect(640, 150, 70, 18),
                pg.Rect(720, 150, 70, 18),
            ],
            exit_rect=door(c.SCREEN_W - 50, 150),
            spawn=(30, spawn_y),
        ),
        # 9 Nightmare — sparse ledges (gaps still jumpable)
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(100, 380, 60, 18),
                pg.Rect(240, 320, 55, 18),
                pg.Rect(380, 260, 55, 18),
                pg.Rect(520, 200, 55, 18),
                pg.Rect(650, 160, 60, 18),
                pg.Rect(720, 250, 70, 18),
            ],
            exit_rect=door(c.SCREEN_W - 50, 250),
            spawn=(30, spawn_y),
        ),
        # 10 Almost Impossible — tall climb, fast spikes, still reachable
        LevelLayout(
            floors=[ground],
            platforms=[
                pg.Rect(70, 400, 55, 18),
                pg.Rect(170, 355, 50, 18),
                pg.Rect(270, 310, 50, 18),
                pg.Rect(370, 265, 50, 18),
                pg.Rect(470, 220, 50, 18),
                pg.Rect(570, 175, 50, 18),
                pg.Rect(670, 140, 55, 18),
                pg.Rect(730, 140, 60, 18),
                pg.Rect(730, 280, 60, 18),
            ],
            exit_rect=door(c.SCREEN_W - 45, 280),
            spawn=(25, spawn_y),
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
            self.message = "You survived all 10 levels."
            return
        self.level_index += 1
        name = c.LEVEL_NAMES[self.level_index]
        self.message = f"Level {self.level_index + 1}: {name}"
        self.message_until = now_ms + 1600
        self.reset_level(keep_message=True)

    def solids(self) -> list[pg.Rect]:
        return [*self.layout.floors, *self.layout.platforms]

    def _spawn_spike(self, now_ms: int) -> None:
        """Pick a random solid top edge and plant a spike."""
        surfaces = self.solids()
        surface = self.rng.choice(surfaces)
        warn = c.LEVEL_WARNING_MS[self.level_index]
        exit_r = self.layout.exit_rect
        for _ in range(12):
            w = 22
            left = self.rng.randint(surface.left, max(surface.left, surface.right - w))
            rect = pg.Rect(left, surface.top - 28, w, 28)
            if rect.colliderect(self.player_rect.inflate(40, 20)):
                continue
            if rect.colliderect(exit_r.inflate(30, 10)):
                continue
            self.spikes.append(
                Spike(rect=rect, born_ms=now_ms, warning_ms=warn, warning=True)
            )
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

        # Schedule spikes (burst grows on later levels)
        interval = c.LEVEL_SPAWN_MS[self.level_index]
        if self.next_spike_ms == 0:
            self.next_spike_ms = now_ms + interval // 2
        elif now_ms >= self.next_spike_ms:
            burst = c.LEVEL_SPIKE_BURST[self.level_index]
            for _ in range(burst):
                self._spawn_spike(now_ms)
            jitter = self.rng.randint(-250, 350)
            self.next_spike_ms = now_ms + max(550, interval + jitter)

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
        name = c.LEVEL_NAMES[self.level_index]
        hud = font.render(
            f"Level {self.level_index + 1}/{c.MAX_LEVEL}: {name}   A/D · ↑ jump",
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
            win = big.render("You survived all 10 levels.", True, c.EXIT_C)
            sub = font.render("Esc to quit. (Level 10 was only almost impossible.)", True, c.TEXT)
            surf.blit(win, win.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 - 20)))
            surf.blit(sub, sub.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 + 24)))
