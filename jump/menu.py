"""Title / main menu for JUMP."""

from __future__ import annotations

from typing import Optional

import pygame

import config as c


class MainMenu:
    """Landing screen with Play and Quit actions."""

    def __init__(self) -> None:
        """Build fonts and button rects."""
        self._title = pygame.font.SysFont("Arial", 72, bold=True)
        self._sub = pygame.font.SysFont("Arial", 22)
        self._btn = pygame.font.SysFont("Arial", 28, bold=True)
        self._tiny = pygame.font.SysFont("Arial", 15)
        self.play_rect = pygame.Rect(c.SCREEN_W // 2 - 140, 268, 280, 58)
        self.quit_rect = pygame.Rect(c.SCREEN_W // 2 - 140, 342, 280, 58)
        self._choice: Optional[str] = None
        self._pulse = 0.0

    @property
    def choice(self) -> Optional[str]:
        """``'play'``, ``'quit'``, or ``None`` until the player picks."""
        return self._choice

    def reset(self) -> None:
        """Clear the pending choice when returning from a run."""
        self._choice = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Click / keyboard shortcuts for Play and Quit."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._choice = "play"
            elif event.key == pygame.K_ESCAPE:
                self._choice = "quit"
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.play_rect.collidepoint(event.pos):
                self._choice = "play"
            elif self.quit_rect.collidepoint(event.pos):
                self._choice = "quit"

    def update(self, dt: float) -> None:
        """Advance menu animation time."""
        self._pulse += dt

    def draw(self, surf: pygame.Surface) -> None:
        """Render the neon title card."""
        for y in range(c.SCREEN_H):
            t = y / c.SCREEN_H
            color = tuple(
                int(c.BG_TOP[i] + (c.BG_BOTTOM[i] - c.BG_TOP[i]) * t) for i in range(3)
            )
            pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))

        for x in range(0, c.SCREEN_W, 48):
            pygame.draw.line(surf, (28, 34, 70), (x, 0), (x, c.SCREEN_H))
        for y in range(0, c.SCREEN_H, 48):
            pygame.draw.line(surf, (28, 34, 70), (0, y), (c.SCREEN_W, y))

        title = self._title.render("JUMP", True, c.GROUND_LINE)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 88)))

        sub = self._sub.render("Cube · Ship · Ball · UFO", True, c.UI_DIM)
        surf.blit(sub, sub.get_rect(center=(c.SCREEN_W // 2, 145)))

        # Portal color legend
        legend = [
            ("CUBE", c.PORTAL_CUBE),
            ("SHIP", c.PORTAL_SHIP),
            ("BALL", c.PORTAL_BALL),
            ("UFO", c.PORTAL_UFO),
        ]
        base_x = c.SCREEN_W // 2 - 210
        for i, (name, color) in enumerate(legend):
            x = base_x + i * 110
            pygame.draw.circle(surf, color, (x + 20, 190), 12, 3)
            text = self._tiny.render(name, True, color)
            surf.blit(text, (x + 38, 182))

        # Ship tip callout
        tip = self._tiny.render(
            "Purple portal = SHIP  ·  Hold Space to fly up, release to go down",
            True,
            c.PORTAL_SHIP,
        )
        surf.blit(tip, tip.get_rect(center=(c.SCREEN_W // 2, 230)))

        mouse = pygame.mouse.get_pos()
        self._draw_button(
            surf, self.play_rect, "PLAY", self.play_rect.collidepoint(mouse)
        )
        self._draw_button(
            surf, self.quit_rect, "QUIT", self.quit_rect.collidepoint(mouse)
        )

        hints = [
            "Green portal: Cube — jump 2 blocks",
            "Purple portal: Ship — hold up / release down",
            "Orange portal: Ball — invert gravity  ·  Yellow: UFO — mid-air jump",
        ]
        for i, line in enumerate(hints):
            text = self._tiny.render(line, True, c.UI_DIM)
            surf.blit(text, text.get_rect(center=(c.SCREEN_W // 2, 430 + i * 20)))

    def _draw_button(
        self, surf: pygame.Surface, rect: pygame.Rect, label: str, hover: bool
    ) -> None:
        color = c.MENU_BTN_HOVER if hover else c.MENU_BTN
        pygame.draw.rect(surf, color, rect, border_radius=10)
        pygame.draw.rect(surf, c.UI, rect, width=2, border_radius=10)
        text = self._btn.render(label, True, c.UI)
        surf.blit(text, text.get_rect(center=rect.center))
