"""Portable saved-chapter library and chapter browser."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pygame

import config as c
from level import Obstacle, Orb, Portal

CHAPTERS_DIR = Path(__file__).with_name("chapters")


def level_to_dict(
    level_data: tuple[list[Obstacle], list[Portal], list[Orb], float],
    *,
    double_jump_enabled: bool = True,
    infinite_test_enabled: bool = False,
) -> dict[str, Any]:
    """Convert a playable layout into a portable JSON document."""
    obstacles, portals, orbs, finish_x = level_data
    return {
        "finish_x": finish_x,
        "double_jump_enabled": double_jump_enabled,
        "infinite_test_enabled": infinite_test_enabled,
        "obstacles": [asdict(item) for item in obstacles],
        "portals": [asdict(item) for item in portals],
        "orbs": [asdict(item) for item in orbs],
    }


def dict_to_level(data: dict[str, Any]) -> tuple[list[Obstacle], list[Portal], list[Orb], float]:
    """Read a chapter JSON document into gameplay objects."""
    obstacles = [Obstacle(**item) for item in data["obstacles"]]
    portals = [Portal(**item) for item in data["portals"]]
    orbs = [Orb(**item) for item in data["orbs"]]
    return obstacles, portals, orbs, float(data["finish_x"])


def save_chapter(level_data: tuple[list[Obstacle], list[Portal], list[Orb], float], *, double_jump_enabled: bool, infinite_test_enabled: bool) -> Path:
    """Save a new numbered chapter and return its file path."""
    CHAPTERS_DIR.mkdir(exist_ok=True)
    existing = sorted(CHAPTERS_DIR.glob("chapter_*.json"))
    number = 1
    used = {int(path.stem.removeprefix("chapter_")) for path in existing if path.stem.removeprefix("chapter_").isdigit()}
    while number in used:
        number += 1
    target = CHAPTERS_DIR / f"chapter_{number:03d}.json"
    target.write_text(
        json.dumps(
            level_to_dict(
                level_data,
                double_jump_enabled=double_jump_enabled,
                infinite_test_enabled=infinite_test_enabled,
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return target


def load_chapters() -> list[tuple[Path, dict[str, Any]]]:
    """Load valid chapters, skipping malformed files."""
    CHAPTERS_DIR.mkdir(exist_ok=True)
    chapters: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(CHAPTERS_DIR.glob("chapter_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            dict_to_level(data)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        chapters.append((path, data))
    return chapters


class ChapterBrowser:
    """Menu screen where players choose a shared saved chapter."""

    def __init__(self) -> None:
        self.chapters = load_chapters()
        self.level_data: tuple[list[Obstacle], list[Portal], list[Orb], float] | None = None
        self.double_jump_enabled = True
        self.infinite_test_enabled = False
        self.request_menu = False
        self._title = pygame.font.SysFont("Arial", 48, bold=True)
        self._body = pygame.font.SysFont("Arial", 22, bold=True)
        self._small = pygame.font.SysFont("Arial", 16)
        self.chapter_rects = [
            pygame.Rect(120 + (index % 4) * 190, 160 + (index // 4) * 90, 150, 62)
            for index in range(len(self.chapters))
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.request_menu = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.chapter_rects):
                if rect.collidepoint(event.pos):
                    _, data = self.chapters[index]
                    self.level_data = dict_to_level(data)
                    self.double_jump_enabled = bool(data.get("double_jump_enabled", True))
                    self.infinite_test_enabled = bool(data.get("infinite_test_enabled", False))
                    return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill((10, 15, 34))
        title = self._title.render("COMMUNITY CHAPTERS", True, c.GROUND_LINE)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 72)))
        subtitle = self._small.render(
            "Saved chapters in jump/chapters  ·  Esc back", True, c.UI_DIM
        )
        surf.blit(subtitle, subtitle.get_rect(center=(c.SCREEN_W // 2, 112)))
        if not self.chapters:
            empty = self._body.render("No chapters saved yet", True, c.UI_DIM)
            surf.blit(empty, empty.get_rect(center=(c.SCREEN_W // 2, 280)))
        for index, (path, _) in enumerate(self.chapters):
            rect = self.chapter_rects[index]
            pygame.draw.rect(surf, c.MENU_BTN, rect, border_radius=7)
            pygame.draw.rect(surf, c.UI, rect, width=2, border_radius=7)
            label = self._body.render(path.stem.replace("_", " ").upper(), True, c.UI)
            surf.blit(label, label.get_rect(center=rect.center))
        hint = self._small.render("Click a chapter to play it", True, c.UI_DIM)
        surf.blit(hint, hint.get_rect(center=(c.SCREEN_W // 2, 500)))
