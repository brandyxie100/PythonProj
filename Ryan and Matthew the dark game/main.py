"""A small original dark-fantasy block platformer."""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass

import pygame as pg

SCREEN_W = 960
SCREEN_H = 540
FPS = 60
TILE = 32
GRAVITY = 1800.0
MOVE_SPEED = 280.0
JUMP_SPEED = -670.0
BG = (10, 13, 27)
STONE = (43, 48, 69)
STONE_TOP = (80, 85, 115)
PURPLE = (172, 109, 255)
CYAN = (100, 242, 235)
WHITE = (230, 233, 255)


@dataclass(frozen=True)
class Stage:
    name: str
    width: int
    floor_spans: tuple[tuple[int, int], ...]
    ledges: tuple[tuple[int, int, int], ...]
    spikes: tuple[int, ...]
    shards: tuple[tuple[int, int], ...]
    exit_x: int


STAGES = (
    Stage(
        "Moonlit Ruins",
        56,
        ((0, 15), (18, 31), (34, 46), (49, 56)),
        ((5, 13, 4), (20, 13, 4), (27, 13, 3), (36, 13, 4), (43, 13, 3)),
        (10, 23, 39, 51),
        ((7, 12), (21, 12), (37, 11)),
        54,
    ),
    Stage(
        "The Hollow Keep",
        63,
        ((0, 13), (16, 27), (30, 41), (44, 54), (57, 63)),
        ((4, 13, 4), (11, 11, 4), (19, 13, 4), (25, 11, 4), (33, 13, 4), (39, 11, 4), (47, 13, 4), (53, 11, 4)),
        (8, 21, 35, 49, 59),
        ((12, 10), (26, 10), (40, 10), (54, 10)),
        61,
    ),
    Stage(
        "The Last Lantern",
        70,
        ((0, 12), (15, 25), (28, 38), (41, 52), (55, 70)),
        ((3, 13, 4), (9, 11, 4), (17, 13, 4), (23, 11, 4), (30, 13, 4), (36, 11, 4), (43, 13, 4), (49, 11, 4), (57, 13, 4), (63, 11, 4)),
        (7, 19, 32, 46, 60, 67),
        ((10, 10), (24, 10), (37, 10), (50, 10), (64, 10)),
        68,
    ),
)


@dataclass
class Level:
    stage: Stage
    solids: list[pg.Rect]
    spikes: list[pg.Rect]
    shards: list[pg.Rect]
    exit_rect: pg.Rect

    @property
    def world_width(self) -> int:
        return self.stage.width * TILE


def build_level(stage: Stage) -> Level:
    """Build collision shapes from a stage's tile coordinates."""
    solids = [
        pg.Rect(start * TILE, 16 * TILE, (end - start) * TILE, 2 * TILE)
        for start, end in stage.floor_spans
    ]
    solids.extend(
        pg.Rect(x * TILE, y * TILE, width * TILE, TILE)
        for x, y, width in stage.ledges
    )
    spikes = [
        pg.Rect(x * TILE + 2, 16 * TILE - 17, TILE - 4, 17)
        for x in stage.spikes
    ]
    shards = [
        pg.Rect(x * TILE + 10, y * TILE + 8, 12, 18)
        for x, y in stage.shards
    ]
    exit_rect = pg.Rect(stage.exit_x * TILE, 16 * TILE - 64, 28, 64)
    return Level(stage, solids, spikes, shards, exit_rect)


class DarkGame:
    def __init__(self) -> None:
        self.level_index = 0
        self.deaths = 0
        self.camera_x = 0
        self.message = ""
        self.message_until = 0
        self.won = False
        self._stars = [
            (random.randrange(SCREEN_W), random.randrange(SCREEN_H), random.choice((1, 1, 2)))
            for _ in range(90)
        ]
        self.load_stage()

    def load_stage(self) -> None:
        self.level = build_level(STAGES[self.level_index])
        self.spawn = pg.Vector2(2 * TILE, 16 * TILE - 30)
        self.player = pg.Rect(round(self.spawn.x), round(self.spawn.y), 22, 30)
        self.velocity = pg.Vector2()
        self.grounded = True
        self.collected: set[int] = set()
        self.camera_x = 0

    def restart(self) -> None:
        self.deaths += 1
        self.load_stage()
        self.message = "The shadows return you to the start."
        self.message_until = pg.time.get_ticks() + 1400

    def update(self, dt: float, keys: pg.key.ScancodeWrapper) -> None:
        if self.won:
            return
        if keys[pg.K_a] or keys[pg.K_LEFT]:
            self.velocity.x = -MOVE_SPEED
        elif keys[pg.K_d] or keys[pg.K_RIGHT]:
            self.velocity.x = MOVE_SPEED
        else:
            self.velocity.x = 0

        self.velocity.y = min(self.velocity.y + GRAVITY * dt, 950)
        self.player.x += round(self.velocity.x * dt)
        for solid in self.level.solids:
            if self.player.colliderect(solid):
                if self.velocity.x > 0:
                    self.player.right = solid.left
                elif self.velocity.x < 0:
                    self.player.left = solid.right

        self.player.y += round(self.velocity.y * dt)
        self.grounded = False
        for solid in self.level.solids:
            if self.player.colliderect(solid):
                if self.velocity.y > 0:
                    self.player.bottom = solid.top
                    self.grounded = True
                elif self.velocity.y < 0:
                    self.player.top = solid.bottom
                self.velocity.y = 0

        if self.player.top > SCREEN_H + TILE or any(
            self.player.colliderect(spike) for spike in self.level.spikes
        ):
            self.restart()
            return

        for index, shard in enumerate(self.level.shards):
            if index not in self.collected and self.player.colliderect(shard):
                self.collected.add(index)

        if self.player.colliderect(self.level.exit_rect):
            if len(self.collected) == len(self.level.shards):
                self.level_index += 1
                if self.level_index == len(STAGES):
                    self.won = True
                else:
                    self.load_stage()
                    self.message = f"{STAGES[self.level_index].name} — keep the lantern lit."
                    self.message_until = pg.time.get_ticks() + 1800
            else:
                self.message = "The gate needs every lost shard."
                self.message_until = pg.time.get_ticks() + 1200

        target = self.player.centerx - SCREEN_W // 2
        self.camera_x = max(0, min(target, self.level.world_width - SCREEN_W))

    def jump(self) -> None:
        if not self.won and self.grounded:
            self.velocity.y = JUMP_SPEED
            self.grounded = False

    def draw(self, screen: pg.Surface, font: pg.font.Font, title_font: pg.font.Font) -> None:
        screen.fill(BG)
        for x, y, radius in self._stars:
            twinkle = 120 + int(55 * math.sin(pg.time.get_ticks() / 700 + x))
            screen.set_at((x, y), (twinkle, twinkle, min(255, twinkle + 25)))

        # A dim moon and distant silhouettes give each level a night-sky horizon.
        pg.draw.circle(screen, (63, 67, 104), (780 - self.camera_x // 12, 112), 54)
        pg.draw.circle(screen, (135, 131, 175), (780 - self.camera_x // 12, 112), 44)
        for x in range(-self.camera_x // 3 % 190 - 190, SCREEN_W, 190):
            pg.draw.polygon(screen, (20, 23, 42), [(x, 405), (x + 38, 250), (x + 82, 405)])

        for solid in self.level.solids:
            visible = self._screen_rect(solid)
            if visible.right < 0 or visible.left > SCREEN_W:
                continue
            pg.draw.rect(screen, STONE, visible)
            pg.draw.line(screen, STONE_TOP, visible.topleft, visible.topright, 3)
            if visible.width > TILE:
                for seam_x in range(visible.left + TILE, visible.right, TILE):
                    pg.draw.line(screen, (31, 35, 53), (seam_x, visible.top + 5), (seam_x, visible.bottom), 2)

        for spike in self.level.spikes:
            rect = self._screen_rect(spike)
            pg.draw.polygon(
                screen,
                (196, 66, 104),
                [(rect.left, rect.bottom), (rect.centerx, rect.top), (rect.right, rect.bottom)],
            )
            pg.draw.line(screen, (255, 121, 160), (rect.left + 5, rect.bottom - 2), (rect.centerx, rect.top + 5), 2)

        for index, shard in enumerate(self.level.shards):
            if index in self.collected:
                continue
            rect = self._screen_rect(shard)
            pg.draw.circle(screen, (67, 125, 150), rect.center, 14)
            pg.draw.polygon(
                screen,
                CYAN,
                [(rect.centerx, rect.top), (rect.right, rect.centery), (rect.centerx, rect.bottom), (rect.left, rect.centery)],
            )

        gate = self._screen_rect(self.level.exit_rect)
        gate_color = PURPLE if len(self.collected) == len(self.level.shards) else (72, 63, 91)
        pg.draw.rect(screen, gate_color, gate, border_radius=14)
        pg.draw.rect(screen, (221, 193, 255), gate.inflate(-10, -10), 2, border_radius=10)
        pg.draw.circle(screen, BG, gate.center, 6)

        player = self._screen_rect(self.player)
        pg.draw.ellipse(screen, (75, 43, 122), player.inflate(18, 12))
        pg.draw.rect(screen, (66, 56, 103), player, border_radius=6)
        pg.draw.rect(screen, (137, 113, 191), (player.x + 3, player.y + 3, player.width - 6, 8), border_radius=3)
        pg.draw.rect(screen, CYAN, (player.x + 5, player.y + 11, 4, 3))
        pg.draw.rect(screen, CYAN, (player.x + 13, player.y + 11, 4, 3))

        stage_name = STAGES[self.level_index].name if not self.won else "The Lantern Bearer"
        hud = font.render(
            f"{stage_name}   |   Shards: {len(self.collected)}/{len(self.level.shards)}   |   Falls: {self.deaths}",
            True,
            WHITE,
        )
        screen.blit(hud, (18, 16))
        controls = font.render("A/D or arrows: move    Space/W/Up: jump    R: restart    Esc: quit", True, (163, 171, 202))
        screen.blit(controls, (18, SCREEN_H - 30))

        if self.message and pg.time.get_ticks() < self.message_until:
            banner = font.render(self.message, True, (255, 217, 153))
            screen.blit(banner, banner.get_rect(center=(SCREEN_W // 2, 72)))

        if self.won:
            shade = pg.Surface((SCREEN_W, SCREEN_H), pg.SRCALPHA)
            shade.fill((5, 7, 18, 205))
            screen.blit(shade, (0, 0))
            title = title_font.render("THE LANTERN LIVES", True, CYAN)
            subtitle = font.render("You carried the light through the dark.  Press Enter to play again.", True, WHITE)
            screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 24)))
            screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 28)))

    def _screen_rect(self, rect: pg.Rect) -> pg.Rect:
        return rect.move(-self.camera_x, 0)


def main() -> int:
    pg.init()
    pg.display.set_caption("The Lantern Below")
    screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pg.time.Clock()
    font = pg.font.SysFont("consolas", 18)
    title_font = pg.font.SysFont("consolas", 40, bold=True)
    game = DarkGame()
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000, 1 / 30)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key in (pg.K_SPACE, pg.K_w, pg.K_UP):
                    if game.won:
                        game = DarkGame()
                    else:
                        game.jump()
                elif event.key == pg.K_RETURN and game.won:
                    game = DarkGame()
                elif event.key == pg.K_r and not game.won:
                    game.load_stage()

        game.update(dt, pg.key.get_pressed())
        game.draw(screen, font, title_font)
        pg.display.flip()

    pg.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
