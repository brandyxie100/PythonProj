"""Entry point for Spike Troll."""

from __future__ import annotations

import sys

import pygame as pg

import config as c
from game import Game


def main() -> int:
    """Run the troll platformer until quit."""
    pg.init()
    pg.display.set_caption(c.TITLE)
    screen = pg.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    clock = pg.time.Clock()
    font = pg.font.SysFont("consolas", 18)
    big = pg.font.SysFont("consolas", 28, bold=True)

    game = Game()
    running = True

    while running:
        dt = clock.tick(c.FPS) / 1000.0
        dt = min(dt, 1.0 / 30.0)
        now_ms = pg.time.get_ticks()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key in (pg.K_UP, pg.K_SPACE, pg.K_w):
                    game.request_jump(now_ms)
                elif event.key == pg.K_r and not game.won:
                    game.reset_level(keep_message=False)

        keys = pg.key.get_pressed()
        game.handle_input(keys)
        game.update(dt, now_ms)
        game.draw(screen, font, big)
        pg.display.flip()

    pg.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
