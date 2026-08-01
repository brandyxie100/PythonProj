"""Entry point for JUMP — Geometry Dash–style auto-runner."""

from __future__ import annotations

import sys

import pygame

import config as c
from game import Game


def main() -> int:
    """Run the game until the window is closed."""
    pygame.init()
    pygame.display.set_caption(c.TITLE)
    screen = pygame.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    clock = pygame.time.Clock()
    game = Game()

    running = True
    while running:
        dt = clock.tick(c.FPS) / 1000.0
        # Cap huge frame spikes (alt-tab) so physics stay stable.
        dt = min(dt, 1.0 / 30.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                game.handle_event(event)

        game.update(dt)
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
