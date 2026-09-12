"""The ten-level vault path."""

from __future__ import annotations

import pygame

import config as c
from level import Obstacle, Orb, Portal


class Path:
    """Level-select screen and progress for the vault path."""

    def __init__(self, completed: set[int] | None = None) -> None:
        self.completed = set(completed or set())
        self.request_vault = False
        self.level_to_play: int | None = None
        self._title = pygame.font.SysFont("Arial", 52, bold=True)
        self._body = pygame.font.SysFont("Arial", 22, bold=True)
        self._small = pygame.font.SysFont("Arial", 16)
        self.level_rects = [
            pygame.Rect(100 + (i % 5) * 155, 170 + (i // 5) * 110, 120, 76)
            for i in range(10)
        ]

    @property
    def door_open(self) -> bool:
        return len(self.completed) == 10

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.request_vault = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.level_rects):
                if rect.collidepoint(event.pos) and index not in self.completed:
                    self.level_to_play = index
                    return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill((10, 15, 34))
        title = self._title.render("THE PATH", True, c.GROUND_LINE)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 70)))
        subtitle = self._small.render(
            f"WHITE ORBS: {len(self.completed)}/10  ·  Complete every level to open the door",
            True,
            c.UI_DIM,
        )
        surf.blit(subtitle, subtitle.get_rect(center=(c.SCREEN_W // 2, 112)))

        for index, rect in enumerate(self.level_rects):
            complete = index in self.completed
            color = c.PROGRESS_FILL if complete else c.MENU_BTN
            pygame.draw.rect(surf, color, rect, border_radius=8)
            pygame.draw.rect(surf, c.UI, rect, width=2, border_radius=8)
            label = "WHITE ORB" if complete else f"LEVEL {index + 1}"
            text = self._body.render(label, True, (12, 18, 32) if complete else c.UI)
            surf.blit(text, text.get_rect(center=rect.center))

        door_color = c.PROGRESS_FILL if self.door_open else c.UI_DIM
        door = pygame.Rect(c.SCREEN_W // 2 - 78, 410, 156, 82)
        pygame.draw.rect(surf, door_color, door, width=5, border_radius=8)
        pygame.draw.circle(surf, door_color, door.center, 9)
        status = "DOOR OPEN" if self.door_open else "DOOR LOCKED"
        status_text = self._body.render(status, True, door_color)
        surf.blit(status_text, status_text.get_rect(center=(c.SCREEN_W // 2, 512)))
        hint = self._small.render("Click a level  ·  Esc back to vault", True, c.UI_DIM)
        surf.blit(hint, hint.get_rect(center=(c.SCREEN_W // 2, 530)))


def build_path_level(level_index: int) -> tuple[list[Obstacle], list[Portal], list[Orb], float]:
    """Build one fair but increasingly difficult path level."""
    ground = c.GROUND_Y
    obstacles: list[Obstacle] = []
    difficulty = level_index + 1
    start = 520.0
    spacing = max(105.0, 170.0 - difficulty * 6.0)
    for i in range(5 + difficulty):
        x = start + i * spacing
        obstacles.append(Obstacle("spike", x, ground - 28.0, 28.0, 28.0))
        if i % 4 == 3:
            obstacles.append(Obstacle("spike", x + 38.0, ground - 28.0, 28.0, 28.0))
    if difficulty >= 4:
        obstacles.append(Obstacle("block", start + 5 * spacing, ground - 72.0, 72.0, 36.0))
    portals: list[Portal] = []
    if difficulty >= 7:
        portals.append(Portal(start + 2 * spacing, "ship"))
        portals.append(Portal(start + 5 * spacing, "cube"))
    orbs = [Orb("white", start + 3 * spacing, ground - 120.0)]
    return obstacles, portals, orbs, start + (7 + difficulty) * spacing
