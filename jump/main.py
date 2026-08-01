"""Entry point for JUMP — Geometry Dash–style auto-runner."""

from __future__ import annotations

import sys

import pygame

import config as c
from game import Game
from menu import MainMenu


def main() -> int:
    """Run menu ↔ gameplay until the player quits."""
    pygame.init()
    pygame.display.set_caption(c.TITLE)
    screen = pygame.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    clock = pygame.time.Clock()

    menu = MainMenu()
    game: Game | None = None
    scene = "menu"

    running = True
    while running:
        dt = clock.tick(c.FPS) / 1000.0
        dt = min(dt, 1.0 / 30.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if scene == "menu":
                menu.handle_event(event)
            elif game is not None:
                game.handle_event(event)

        if scene == "menu":
            menu.update(dt)
            if menu.choice == "play":
                game = Game()
                scene = "game"
                menu.reset()
            elif menu.choice == "quit":
                running = False
            menu.draw(screen)
        elif game is not None:
            game.update(dt)
            if game.request_menu:
                scene = "menu"
                menu.reset()
                game = None
            else:
                game.draw(screen)

        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
