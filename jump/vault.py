"""Hidden vault screen for the main-menu easter egg."""

from __future__ import annotations

import pygame

import config as c


class Vault:
    """A locked or unlocked secret room reached from the main menu."""

    def __init__(self, unlocked: bool, has_key: bool = False) -> None:
        self.unlocked = unlocked
        self.has_key = has_key
        self.request_menu = False
        self.request_path = False
        self.path_button = pygame.Rect(c.SCREEN_W // 2 - 120, 430, 240, 42)
        self.tap_count = 0
        self.exploded = False
        self.lock_rect = pygame.Rect(c.SCREEN_W // 2 - 82, 176, 164, 146)
        self._pulse = 0.0
        self._title = pygame.font.SysFont("Arial", 64, bold=True)
        self._body = pygame.font.SysFont("Arial", 24, bold=True)
        self._small = pygame.font.SysFont("Arial", 17)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Return to the main menu with Escape."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.request_menu = True
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.unlocked
            and not self.exploded
            and self.lock_rect.collidepoint(event.pos)
        ):
            self.tap_count += 1
            if self.tap_count >= 10:
                self.exploded = True
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.exploded
            and self.has_key
            and self.path_button.collidepoint(event.pos)
        ):
            self.request_path = True

    def update(self, dt: float) -> None:
        """Advance the vault animation."""
        self._pulse += dt

    def draw(self, surf: pygame.Surface) -> None:
        """Render the vault and its current lock state."""
        for y in range(c.SCREEN_H):
            t = y / c.SCREEN_H
            color = (
                int(8 + (24 - 8) * t),
                int(10 + (14 - 10) * t),
                int(24 + (45 - 24) * t),
            )
            pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))

        title = self._title.render("THE VAULT", True, c.GROUND_LINE)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 92)))

        lock_color = c.PROGRESS_FILL if self.unlocked else c.SPIKE
        self.lock_rect = pygame.Rect(c.SCREEN_W // 2 - 82, 176, 164, 146)
        lock_rect = self.lock_rect
        pygame.draw.rect(surf, lock_color, lock_rect, width=5, border_radius=12)
        shackle = pygame.Rect(c.SCREEN_W // 2 - 42, 132, 84, 92)
        pygame.draw.arc(surf, lock_color, shackle, 3.14, 6.28, 7)
        pygame.draw.circle(surf, lock_color, lock_rect.center, 12)
        pygame.draw.line(
            surf,
            lock_color,
            (lock_rect.centerx, lock_rect.centery),
            (lock_rect.centerx, lock_rect.centery + 26),
            6,
        )

        if self.exploded:
            state = "VAULT OPEN"
            detail = (
                "KEY ACQUIRED"
                if self.has_key
                else "BEAT THE FIRST LEVEL TO GET THE KEY"
            )
        else:
            state = "LOCK OPEN" if self.unlocked else "LOCKED"
            detail = (
                f"Tap the lock {10 - self.tap_count} more times"
                if self.unlocked
                else "The lock is still sealed."
            )
        state_text = self._body.render(state, True, lock_color)
        surf.blit(state_text, state_text.get_rect(center=(c.SCREEN_W // 2, 372)))
        detail_text = self._small.render(detail, True, c.UI_DIM)
        surf.blit(detail_text, detail_text.get_rect(center=(c.SCREEN_W // 2, 414)))
        hint = self._small.render("Press Esc to return", True, c.UI)
        surf.blit(hint, hint.get_rect(center=(c.SCREEN_W // 2, 480)))
        if self.exploded and self.has_key:
            pygame.draw.rect(surf, c.PROGRESS_FILL, self.path_button, border_radius=6)
            path_text = self._body.render("OPEN PATH", True, (12, 18, 32))
            surf.blit(path_text, path_text.get_rect(center=self.path_button.center))
