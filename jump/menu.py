"""Title / main menu for JUMP."""

from __future__ import annotations

from typing import Optional

import pygame

import config as c
from level import LEVELS


class MainMenu:
    """Landing screen with Play and Quit actions."""

    def __init__(self) -> None:
        """Build fonts and button rects."""
        self._title = pygame.font.SysFont("Arial", 72, bold=True)
        self._sub = pygame.font.SysFont("Arial", 22)
        self._btn = pygame.font.SysFont("Arial", 28, bold=True)
        self._tiny = pygame.font.SysFont("Arial", 15)
        self.modes_rect = pygame.Rect(c.SCREEN_W // 2 - 140, 212, 280, 58)
        self.levels_rect = pygame.Rect(c.SCREEN_W // 2 - 140, 292, 280, 58)
        self.play_rect = pygame.Rect(c.SCREEN_W // 2 - 140, 372, 280, 58)
        self.quit_rect = pygame.Rect(c.SCREEN_W // 2 - 140, 452, 280, 58)
        self._choice: Optional[str] = None
        self._pulse = 0.0
        self._show_modes = False
        self._show_levels = False
        self._mode_labels = ["CUBE", "SHIP", "BALL", "UFO", "WAVE"]
        self._selected_mode = 0
        self._level_labels = ["RANDOM"] + [name for name, _ in LEVELS]
        self._selected_level = 0
        self._mode_rects = self._build_mode_rects()
        self._level_rects = self._build_level_rects()

    @property
    def choice(self) -> Optional[str]:
        """``'play'``, ``'quit'``, or ``None`` until the player picks."""
        return self._choice

    def reset(self) -> None:
        """Clear the pending choice when returning from a run."""
        self._choice = None

    @property
    def selected_level_index(self) -> Optional[int]:
        """Return None for random or the selected level index."""
        return None if self._selected_level == 0 else self._selected_level - 1

    @property
    def selected_mode(self) -> str:
        """Return the selected starting gamemode."""
        return self._mode_labels[self._selected_mode].lower()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Click / keyboard shortcuts for menu navigation."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self._show_levels or self._show_modes:
                    self._show_levels = False
                    self._show_modes = False
                else:
                    self._choice = "play"
            elif event.key == pygame.K_ESCAPE:
                if self._show_levels or self._show_modes:
                    self._show_levels = False
                    self._show_modes = False
                else:
                    self._choice = "quit"
            elif event.key in (pygame.K_UP, pygame.K_w):
                if self._show_levels:
                    self._selected_level = max(0, self._selected_level - 1)
                elif self._show_modes:
                    self._selected_mode = max(0, self._selected_mode - 1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                if self._show_levels:
                    self._selected_level = min(len(self._level_labels) - 1, self._selected_level + 1)
                elif self._show_modes:
                    self._selected_mode = min(len(self._mode_labels) - 1, self._selected_mode + 1)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.play_rect.collidepoint(event.pos):
                self._choice = "play"
            elif self.quit_rect.collidepoint(event.pos):
                self._choice = "quit"
            elif self.modes_rect.collidepoint(event.pos):
                self._show_modes = not self._show_modes
                if self._show_modes:
                    self._show_levels = False
            elif self.levels_rect.collidepoint(event.pos):
                self._show_levels = not self._show_levels
                if self._show_levels:
                    self._show_modes = False
            elif self._show_levels:
                for idx, rect in enumerate(self._level_rects):
                    if rect.collidepoint(event.pos):
                        self._selected_level = idx
                        self._show_levels = False
                        break
            elif self._show_modes:
                for idx, rect in enumerate(self._mode_rects):
                    if rect.collidepoint(event.pos):
                        self._selected_mode = idx
                        self._show_modes = False
                        break

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
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 78)))

        mouse = pygame.mouse.get_pos()
        self._draw_button(
            surf, self.modes_rect, "MODES", self.modes_rect.collidepoint(mouse)
        )
        self._draw_button(
            surf, self.levels_rect, "LEVELS", self.levels_rect.collidepoint(mouse)
        )

        if self._show_modes:
            for idx, label in enumerate(self._mode_labels):
                rect = self._mode_rects[idx]
                active = idx == self._selected_mode
                btn_color = c.MENU_BTN_HOVER if active else c.MENU_BTN
                pygame.draw.rect(surf, btn_color, rect, border_radius=10)
                pygame.draw.rect(surf, c.UI, rect, width=2, border_radius=10)
                text = self._btn.render(label, True, c.UI)
                surf.blit(text, text.get_rect(center=rect.center))

        if self._show_levels:
            for idx, label in enumerate(self._level_labels):
                rect = self._level_rects[idx]
                active = idx == self._selected_level
                btn_color = c.MENU_BTN_HOVER if active else c.MENU_BTN
                pygame.draw.rect(surf, btn_color, rect, border_radius=10)
                pygame.draw.rect(surf, c.UI, rect, width=2, border_radius=10)
                text = self._btn.render(label, True, c.UI)
                surf.blit(text, text.get_rect(center=rect.center))

        self._draw_button(
            surf, self.play_rect, "PLAY", self.play_rect.collidepoint(mouse)
        )
        self._draw_button(
            surf, self.quit_rect, "QUIT", self.quit_rect.collidepoint(mouse)
        )

    def _build_mode_rects(self) -> list[pygame.Rect]:
        rects: list[pygame.Rect] = []
        width = 260
        x = c.SCREEN_W // 2 - width // 2
        y = 100
        spacing = 44
        for i in range(len(self._mode_labels)):
            rects.append(pygame.Rect(x, y + i * spacing, width, 38))
        return rects

    def _build_level_rects(self) -> list[pygame.Rect]:
        rects: list[pygame.Rect] = []
        width = 300
        x = c.SCREEN_W // 2 - width // 2
        y = 180
        spacing = 44
        for i in range(len(self._level_labels)):
            rects.append(pygame.Rect(x, y + i * spacing, width, 38))
        return rects

    def _draw_button(
        self, surf: pygame.Surface, rect: pygame.Rect, label: str, hover: bool
    ) -> None:
        color = c.MENU_BTN_HOVER if hover else c.MENU_BTN
        pygame.draw.rect(surf, color, rect, border_radius=10)
        pygame.draw.rect(surf, c.UI, rect, width=2, border_radius=10)
        text = self._btn.render(label, True, c.UI)
        surf.blit(text, text.get_rect(center=rect.center))
