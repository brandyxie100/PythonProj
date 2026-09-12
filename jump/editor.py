"""Interactive level editor for JUMP."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import pygame

import config as c
from level import (
    Gamemode,
    Obstacle,
    Orb,
    OrbKind,
    Portal,
    draw_obstacle,
    draw_orb,
    draw_portal,
)

LEVEL_FILE = Path(__file__).with_name("custom_level.json")
GRID_SIZE = 18.0
TOOLBAR_TOP = c.SCREEN_H - 78


class Editor:
    """Grid-snapped editor for building a custom JUMP course."""

    def __init__(self) -> None:
        self._font = pygame.font.SysFont("Arial", 20, bold=True)
        self._small = pygame.font.SysFont("Arial", 15)
        self.obstacles: list[Obstacle] = []
        self.portals: list[Portal] = []
        self.orbs: list[Orb] = []
        self.finish_x = 2400.0
        self.camera_x = 0.0
        self.tool = "spike"
        self.portal_mode: Gamemode = "ship"
        self.orb_kind: OrbKind = "yellow"
        self.request_menu = False
        self.request_play = False
        self.request_secret = False
        self._secret_input = ""
        self.double_jump_enabled = True
        self._pulse = 0.0
        self._status = "New level"
        self._status_timer = 4.0

        self.tool_rects = {
            "spike": pygame.Rect(14, TOOLBAR_TOP + 12, 78, 34),
            "block": pygame.Rect(98, TOOLBAR_TOP + 12, 78, 34),
            "portal": pygame.Rect(182, TOOLBAR_TOP + 12, 86, 34),
            "orb": pygame.Rect(274, TOOLBAR_TOP + 12, 66, 34),
            "erase": pygame.Rect(346, TOOLBAR_TOP + 12, 76, 34),
        }
        self.scroll_left_rect = pygame.Rect(680, TOOLBAR_TOP + 12, 56, 34)
        self.scroll_right_rect = pygame.Rect(742, TOOLBAR_TOP + 12, 56, 34)
        self.double_jump_rect = pygame.Rect(490, TOOLBAR_TOP + 12, 174, 34)
        self.save_rect = pygame.Rect(424, TOOLBAR_TOP + 12, 58, 34)
        self.unsave_rect = pygame.Rect(424, TOOLBAR_TOP + 48, 76, 24)
        self.play_rect = pygame.Rect(820, TOOLBAR_TOP + 12, 126, 34)
        if LEVEL_FILE.exists():
            self.load()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle tools, placement, scrolling, and file commands."""
        if event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key).lower()
            if key_name in ("e", "s", "a"):
                self._secret_input = (self._secret_input + key_name)[-3:]
                if self._secret_input == "esa":
                    self.request_secret = True
                    self.request_play = True
                    return
            if event.key == pygame.K_ESCAPE:
                self.request_menu = True
            elif event.key == pygame.K_1:
                self.tool = "spike"
            elif event.key == pygame.K_2:
                self.tool = "block"
            elif event.key == pygame.K_3:
                self.tool = "portal"
            elif event.key == pygame.K_4:
                self.tool = "orb"
            elif event.key == pygame.K_5:
                self.tool = "erase"
            elif event.key == pygame.K_p:
                modes: tuple[Gamemode, ...] = ("cube", "ship", "ball", "ufo", "speed")
                self.portal_mode = modes[(modes.index(self.portal_mode) + 1) % len(modes)]
            elif event.key == pygame.K_o:
                kinds: tuple[OrbKind, ...] = ("yellow", "pink", "blue", "black")
                self.orb_kind = kinds[(kinds.index(self.orb_kind) + 1) % len(kinds)]
            elif event.key == pygame.K_LEFT:
                self.camera_x = max(0.0, self.camera_x - c.CUBE_SIZE * 4)
            elif event.key == pygame.K_RIGHT:
                self.camera_x += c.CUBE_SIZE * 4
            elif event.key == pygame.K_HOME:
                self.camera_x = 0.0
            elif event.key == pygame.K_END:
                self.camera_x = max(0.0, self.finish_x - c.SCREEN_W + 40)
            elif event.key == pygame.K_s:
                self.save()
            elif event.key == pygame.K_l:
                self.load()
            elif event.key == pygame.K_n:
                self.clear()
            return

        if event.type == pygame.MOUSEWHEEL:
            self.camera_x = max(0.0, self.camera_x - event.y * c.CUBE_SIZE * 2)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.unsave_rect.collidepoint(event.pos):
                    self.unsave()
                    return
                if self.save_rect.collidepoint(event.pos):
                    self.save()
                    return
                if self.double_jump_rect.collidepoint(event.pos):
                    self.double_jump_enabled = not self.double_jump_enabled
                    self._status = (
                        "Double jump enabled"
                        if self.double_jump_enabled
                        else "Double jump disabled"
                    )
                    self._status_timer = 2.0
                    return
                if self.scroll_left_rect.collidepoint(event.pos):
                    self.camera_x = max(0.0, self.camera_x - c.CUBE_SIZE * 8)
                    return
                if self.scroll_right_rect.collidepoint(event.pos):
                    self.camera_x += c.CUBE_SIZE * 8
                    return
                if self.play_rect.collidepoint(event.pos):
                    self.request_play = True
                    return
                for tool, rect in self.tool_rects.items():
                    if rect.collidepoint(event.pos):
                        self.tool = tool
                        return
                if event.pos[1] < TOOLBAR_TOP:
                    self.place(event.pos)
            elif event.button == 3 and event.pos[1] < TOOLBAR_TOP:
                self.tool = "erase"
                self.erase(event.pos)

    def level_data(self) -> tuple[list[Obstacle], list[Portal], list[Orb], float]:
        """Return a clean copy of the current layout for a gameplay run."""
        obstacles = [Obstacle(item.kind, item.x, item.y, item.w, item.h) for item in self.obstacles]
        portals = [Portal(item.x, item.mode) for item in self.portals]
        orbs = [Orb(item.kind, item.x, item.y) for item in self.orbs]
        return obstacles, portals, orbs, self.finish_x

    def update(self, dt: float) -> None:
        """Advance editor animation and status timeout."""
        self._pulse += dt
        self._status_timer = max(0.0, self._status_timer - dt)

    def place(self, position: tuple[int, int]) -> None:
        """Place the active item at a snapped screen position."""
        screen_x, screen_y = position
        world_x = self._snap(screen_x + self.camera_x)
        world_y = self._snap(screen_y)
        if self.tool == "spike":
            if world_y >= (c.CEILING_Y + c.GROUND_Y) / 2:
                world_y = c.GROUND_Y - 28.0
            else:
                world_y = c.CEILING_Y
            self.obstacles.append(Obstacle("spike", world_x, world_y, 28.0, 28.0))
        elif self.tool == "block":
            self.obstacles.append(
                Obstacle("block", world_x, max(c.CEILING_Y, world_y), c.CUBE_SIZE, c.CUBE_SIZE)
            )
        elif self.tool == "portal":
            self.portals.append(Portal(world_x, self.portal_mode))
        elif self.tool == "orb":
            self.orbs.append(Orb(self.orb_kind, world_x, max(c.CEILING_Y + 20, world_y)))
        elif self.tool == "erase":
            self.erase(position)
            return
        self._status = f"Added {self.tool}"
        self._status_timer = 2.0
        self.finish_x = max(self.finish_x, world_x + 300.0)

    def erase(self, position: tuple[int, int]) -> None:
        """Remove the nearest item within one grid cell of the cursor."""
        world_x = position[0] + self.camera_x
        world_y = position[1]
        candidates: list[tuple[float, str, object]] = []
        for obstacle in self.obstacles:
            rect = obstacle.screen_rect(self.camera_x)
            candidates.append((self._distance_to_rect(position, rect), "obstacle", obstacle))
        for portal in self.portals:
            distance = abs(portal.x - world_x)
            candidates.append((float(distance), "portal", portal))
        for orb in self.orbs:
            distance = ((orb.x - world_x) ** 2 + (orb.y - world_y) ** 2) ** 0.5
            candidates.append((float(distance), "orb", orb))
        if not candidates:
            return
        distance, kind, item = min(candidates, key=lambda candidate: candidate[0])
        if distance > GRID_SIZE * 2.0:
            return
        if kind == "obstacle":
            self.obstacles.remove(item)  # type: ignore[arg-type]
        elif kind == "portal":
            self.portals.remove(item)  # type: ignore[arg-type]
        else:
            self.orbs.remove(item)  # type: ignore[arg-type]
        self._status = "Item removed"
        self._status_timer = 2.0

    def save(self) -> None:
        """Write the current layout to the project's custom level file."""
        data = {
            "finish_x": self.finish_x,
            "double_jump_enabled": self.double_jump_enabled,
            "obstacles": [asdict(obstacle) for obstacle in self.obstacles],
            "portals": [asdict(portal) for portal in self.portals],
            "orbs": [asdict(orb) for orb in self.orbs],
        }
        try:
            LEVEL_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        except OSError as error:
            self._status = f"Save failed: {error.strerror or 'write error'}"
            self._status_timer = 4.0
            return
        self._status = f"Saved {LEVEL_FILE.name}"
        self._status_timer = 3.0

    def unsave(self) -> None:
        """Remove the saved level while keeping the current editor layout."""
        try:
            LEVEL_FILE.unlink(missing_ok=True)
        except OSError as error:
            self._status = f"Unsave failed: {error.strerror or 'delete error'}"
            self._status_timer = 4.0
            return
        self._status = "Saved progress removed"
        self._status_timer = 3.0

    def load(self) -> None:
        """Load a saved layout, leaving the current layout intact on bad data."""
        if not LEVEL_FILE.exists():
            self._status = "No saved level"
            self._status_timer = 3.0
            return
        try:
            data = json.loads(LEVEL_FILE.read_text(encoding="utf-8"))
            obstacles = [Obstacle(**item) for item in data["obstacles"]]
            portals = [Portal(**item) for item in data["portals"]]
            orbs = [Orb(**item) for item in data["orbs"]]
            finish_x = float(data["finish_x"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            self._status = "Could not load level"
            self._status_timer = 3.0
            return
        self.obstacles, self.portals, self.orbs, self.finish_x = (
            obstacles,
            portals,
            orbs,
            finish_x,
        )
        self.double_jump_enabled = bool(data.get("double_jump_enabled", True))
        self.camera_x = 0.0
        self._status = f"Loaded {LEVEL_FILE.name}"
        self._status_timer = 3.0

    def clear(self) -> None:
        """Start a fresh empty level."""
        self.obstacles.clear()
        self.portals.clear()
        self.orbs.clear()
        self.finish_x = 2400.0
        self.camera_x = 0.0
        self._status = "Cleared level"
        self._status_timer = 2.0

    def draw(self, surf: pygame.Surface) -> None:
        """Render the editing canvas, grid, objects, and controls."""
        self._draw_background(surf)
        self._draw_grid(surf)
        pygame.draw.line(surf, c.GROUND_LINE, (0, int(c.GROUND_Y)), (c.SCREEN_W, int(c.GROUND_Y)), 3)
        pygame.draw.line(surf, c.CEILING_LINE, (0, int(c.CEILING_Y)), (c.SCREEN_W, int(c.CEILING_Y)), 2)
        for portal in self.portals:
            draw_portal(surf, portal, self.camera_x, self._pulse)
        for orb in self.orbs:
            draw_orb(surf, orb, self.camera_x, self._pulse)
        for obstacle in self.obstacles:
            draw_obstacle(surf, obstacle, self.camera_x)
        self._draw_cursor(surf)
        self._draw_toolbar(surf)

    def _draw_background(self, surf: pygame.Surface) -> None:
        for y in range(TOOLBAR_TOP):
            t = y / max(1, TOOLBAR_TOP)
            color = tuple(
                int(c.BG_TOP[i] + (c.BG_BOTTOM[i] - c.BG_TOP[i]) * t) for i in range(3)
            )
            pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))

    def _draw_grid(self, surf: pygame.Surface) -> None:
        first_x = -int(self.camera_x % GRID_SIZE)
        for x in range(first_x, c.SCREEN_W, int(GRID_SIZE)):
            pygame.draw.line(surf, (45, 94, 112), (x, 0), (x, TOOLBAR_TOP), 1)
        for y in range(0, TOOLBAR_TOP, int(GRID_SIZE)):
            pygame.draw.line(surf, (45, 94, 112), (0, y), (c.SCREEN_W, y), 1)

    def _draw_cursor(self, surf: pygame.Surface) -> None:
        position = pygame.mouse.get_pos()
        if position[1] >= TOOLBAR_TOP:
            return
        x = int(self._snap(position[0] + self.camera_x) - self.camera_x)
        y = int(self._snap(position[1]))
        color = c.UI if self.tool != "erase" else c.SPIKE
        pygame.draw.rect(surf, color, pygame.Rect(x, y, int(GRID_SIZE), int(GRID_SIZE)), 2)

    def _draw_toolbar(self, surf: pygame.Surface) -> None:
        pygame.draw.rect(surf, (15, 20, 38), (0, TOOLBAR_TOP, c.SCREEN_W, c.SCREEN_H - TOOLBAR_TOP))
        labels = {"spike": "1 SPIKE", "block": "2 BLOCK", "portal": "3 PORTAL", "orb": "4 ORB", "erase": "5 ERASE"}
        for tool, rect in self.tool_rects.items():
            color = c.MENU_BTN_HOVER if tool == self.tool else c.MENU_BTN
            pygame.draw.rect(surf, color, rect, border_radius=5)
            pygame.draw.rect(surf, c.UI, rect, width=1, border_radius=5)
            text = self._small.render(labels[tool], True, c.UI)
            surf.blit(text, text.get_rect(center=rect.center))

        info = f"Portal: {self.portal_mode.upper()}  Orb: {self.orb_kind.upper()}"
        if self._status_timer > 0:
            info = self._status
        text = self._small.render(info, True, c.UI_DIM)
        surf.blit(text, (440, TOOLBAR_TOP + 50))
        help_text = "Click place  Right-click erase  P/O variants  S/L save/load  N new  Esc menu"
        help_surface = self._small.render(help_text, True, c.UI_DIM)
        surf.blit(help_surface, (14, TOOLBAR_TOP + 48))
        pygame.draw.rect(surf, (100, 70, 80), self.unsave_rect, border_radius=5)
        pygame.draw.rect(surf, c.UI, self.unsave_rect, width=1, border_radius=5)
        unsave_text = self._small.render("UNSAVE", True, c.UI)
        surf.blit(unsave_text, unsave_text.get_rect(center=self.unsave_rect.center))
        for rect, label in (
            (self.scroll_left_rect, "<"),
            (self.scroll_right_rect, ">"),
        ):
            pygame.draw.rect(surf, c.MENU_BTN, rect, border_radius=5)
            pygame.draw.rect(surf, c.UI, rect, width=1, border_radius=5)
            text = self._font.render(label, True, c.UI)
            surf.blit(text, text.get_rect(center=rect.center))
        pygame.draw.rect(surf, c.MENU_BTN, self.save_rect, border_radius=5)
        pygame.draw.rect(surf, c.UI, self.save_rect, width=1, border_radius=5)
        save_text = self._small.render("SAVE", True, c.UI)
        surf.blit(save_text, save_text.get_rect(center=self.save_rect.center))
        toggle_color = c.MENU_BTN_HOVER if self.double_jump_enabled else (100, 70, 80)
        pygame.draw.rect(surf, toggle_color, self.double_jump_rect, border_radius=5)
        pygame.draw.rect(surf, c.UI, self.double_jump_rect, width=1, border_radius=5)
        toggle_label = "DOUBLE JUMP: ON" if self.double_jump_enabled else "DOUBLE JUMP: OFF"
        toggle_text = self._small.render(toggle_label, True, c.UI)
        surf.blit(toggle_text, toggle_text.get_rect(center=self.double_jump_rect.center))
        pygame.draw.rect(surf, c.PROGRESS_FILL, self.play_rect, border_radius=5)
        pygame.draw.rect(surf, c.UI, self.play_rect, width=1, border_radius=5)
        play_text = self._font.render("PLAY", True, (15, 20, 38))
        surf.blit(play_text, play_text.get_rect(center=self.play_rect.center))

    @staticmethod
    def _snap(value: float) -> float:
        return round(value / GRID_SIZE) * GRID_SIZE

    @staticmethod
    def _distance_to_rect(position: tuple[int, int], rect: pygame.Rect) -> float:
        dx = max(rect.left - position[0], 0, position[0] - rect.right)
        dy = max(rect.top - position[1], 0, position[1] - rect.bottom)
        return float((dx * dx + dy * dy) ** 0.5)
