"""Entry point for Versus Projectile Duel Mode."""

from __future__ import annotations

import sys
from typing import Optional

import pygame

import config as c
from duel_mode import VersusScene


def _draw_gradient(surf: pygame.Surface) -> None:
    """Draw the duel-style vertical background gradient."""
    for y in range(c.SCREEN_H):
        t = y / c.SCREEN_H
        color = tuple(
            int(c.DUEL_BG_TOP[i] + (c.DUEL_BG_BOTTOM[i] - c.DUEL_BG_TOP[i]) * t)
            for i in range(3)
        )
        pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))


class MenuScene:
    """Title screen focused solely on Versus Projectile Duel Mode."""

    def __init__(self) -> None:
        """Create fonts and the single Play button."""
        self._title_font = pygame.font.SysFont("Arial", 54, bold=True)
        self._subtitle_font = pygame.font.SysFont("Arial", 26, bold=True)
        self._btn_font = pygame.font.SysFont("Arial", 28, bold=True)
        self._hint_font = pygame.font.SysFont("Arial", 19)
        self._play_rect = pygame.Rect(c.SCREEN_W // 2 - 200, 320, 400, 64)
        self._choice: Optional[str] = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Start the duel on click or Space / Enter."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._play_rect.collidepoint(event.pos):
                self._choice = "play"
        elif event.type == pygame.KEYDOWN and event.key in (
            pygame.K_SPACE,
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            self._choice = "play"

    def update(self) -> Optional[str]:
        """Return and clear the pending menu choice."""
        choice = self._choice
        self._choice = None
        return choice

    def draw(self, surf: pygame.Surface) -> None:
        """Render the duel-focused title screen."""
        _draw_gradient(surf)
        title = self._title_font.render("RAGDOLL-HIT", True, (24, 40, 24))
        subtitle = self._subtitle_font.render(
            "Versus Projectile Duel", True, (40, 70, 40)
        )
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 140)))
        surf.blit(subtitle, subtitle.get_rect(center=(c.SCREEN_W // 2, 210)))

        mouse = pygame.mouse.get_pos()
        fill = (86, 190, 120) if self._play_rect.collidepoint(mouse) else (64, 158, 96)
        pygame.draw.rect(surf, fill, self._play_rect, border_radius=12)
        pygame.draw.rect(surf, (28, 70, 40), self._play_rect, 3, border_radius=12)
        play = self._btn_font.render("Play (7 Stages)", True, c.WHITE)
        surf.blit(play, play.get_rect(center=self._play_rect.center))

        hints = (
            "Hit foes for coins: limbs +5 · body +10 · head +15",
            "Buy stronger weapons in the shop, meet the coin goal, then finish the enemy",
            "A/D dodge  |  W/S aim  |  Hold Space to throw  |  Don't fall off the pillar",
        )
        for idx, line in enumerate(hints):
            hint = self._hint_font.render(line, True, (36, 56, 36))
            surf.blit(hint, hint.get_rect(center=(c.SCREEN_W // 2, 430 + idx * 32)))


class GameOverScene:
    """Win/lose screen after a duel run."""

    def __init__(self, won: bool, coins: int) -> None:
        """Store the run result and build buttons."""
        self.won = won
        self.coins = coins
        self._title_font = pygame.font.SysFont("Arial", 52, bold=True)
        self._btn_font = pygame.font.SysFont("Arial", 28, bold=True)
        self._choice: Optional[str] = None
        self._again = pygame.Rect(c.SCREEN_W // 2 - 170, 340, 340, 58)
        self._menu = pygame.Rect(c.SCREEN_W // 2 - 170, 415, 340, 58)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle Play Again / Back to Menu clicks."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._again.collidepoint(event.pos):
                self._choice = "again"
            elif self._menu.collidepoint(event.pos):
                self._choice = "menu"

    def update(self) -> Optional[str]:
        """Return and clear the pending game-over choice."""
        choice = self._choice
        self._choice = None
        return choice

    def draw(self, surf: pygame.Surface) -> None:
        """Render the result caption, coin total, and buttons."""
        _draw_gradient(surf)
        caption = "DUEL CLEARED!" if self.won else "YOU WERE DEFEATED"
        title = self._title_font.render(caption, True, (24, 40, 24))
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 180)))

        coin_text = self._btn_font.render(
            f"Coins: {self.coins}", True, (120, 80, 20)
        )
        surf.blit(coin_text, coin_text.get_rect(center=(c.SCREEN_W // 2, 260)))

        mouse = pygame.mouse.get_pos()
        for rect, label in ((self._again, "Play Again"), (self._menu, "Back to Menu")):
            color = (86, 190, 120) if rect.collidepoint(mouse) else (64, 158, 96)
            pygame.draw.rect(surf, color, rect, border_radius=11)
            pygame.draw.rect(surf, (28, 70, 40), rect, 2, border_radius=11)
            text = self._btn_font.render(label, True, c.WHITE)
            surf.blit(text, text.get_rect(center=rect.center))


def main() -> None:
    """Run the Versus Projectile Duel game loop."""
    pygame.init()
    screen = pygame.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    pygame.display.set_caption(c.TITLE)
    clock = pygame.time.Clock()

    scene: object = MenuScene()
    running = True
    while running:
        dt = clock.tick(c.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif hasattr(scene, "handle_event"):
                scene.handle_event(event)

        if isinstance(scene, MenuScene):
            if scene.update() == "play":
                scene = VersusScene()
        elif isinstance(scene, VersusScene):
            result = scene.update(dt)
            if result == "win":
                scene = GameOverScene(True, scene.score)
            elif result == "lose":
                scene = GameOverScene(False, scene.score)
        elif isinstance(scene, GameOverScene):
            choice = scene.update()
            if choice == "again":
                scene = VersusScene()
            elif choice == "menu":
                scene = MenuScene()

        screen.fill((0, 0, 0))
        scene.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
