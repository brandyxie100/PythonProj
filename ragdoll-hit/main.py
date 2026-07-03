"""Ragdoll Hit — entry point and scene management.

Run:
    python main.py

Milestone 1: single-player stage with pymunk ragdoll combat.
"""

from __future__ import annotations

import sys
from typing import Optional

import pygame
import pymunk

import config as c
from ai_controller import AIController
from coords import pymunk_to_pygame
from physics_world import PhysicsWorld
from ragdoll import Ragdoll
from terrain import Terrain
from weapon import Weapon


def _draw_bg(surf: pygame.Surface) -> None:
    """Vertical gradient background."""
    for y in range(c.SCREEN_H):
        t = y / c.SCREEN_H
        colour = tuple(
            int(c.BG_TOP[i] + (c.BG_BOT[i] - c.BG_TOP[i]) * t) for i in range(3)
        )
        pygame.draw.line(surf, colour, (0, y), (c.SCREEN_W, y))


def _draw_health_bar(
    surf: pygame.Surface,
    x: int,
    y: int,
    width: int,
    ratio: float,
    fill: tuple[int, int, int],
    label: str,
    font: pygame.font.Font,
) -> None:
    """Draw a labelled health bar."""
    pygame.draw.rect(surf, c.HEALTH_BG, (x, y, width, 14), border_radius=4)
    pygame.draw.rect(surf, fill, (x, y, int(width * ratio), 14), border_radius=4)
    text = font.render(label, True, c.UI_TEXT)
    surf.blit(text, (x, y - 18))


class MenuScene:
    """Title screen with mode entry points."""

    def __init__(self) -> None:
        self._title_font = pygame.font.SysFont("Arial", 58, bold=True)
        self._btn_font = pygame.font.SysFont("Arial", 28, bold=True)
        self._hint_font = pygame.font.SysFont("Arial", 18)
        self._start_rect = pygame.Rect(c.SCREEN_W // 2 - 140, 300, 280, 56)
        self._versus_rect = pygame.Rect(c.SCREEN_W // 2 - 140, 380, 280, 56)
        self._choice: Optional[str] = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle clicks on menu buttons."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._start_rect.collidepoint(event.pos):
                self._choice = "stage"
            elif self._versus_rect.collidepoint(event.pos):
                self._choice = "versus"

    def update(self) -> Optional[str]:
        """Return selected mode when player chooses."""
        choice = self._choice
        self._choice = None
        return choice

    def draw(self, surf: pygame.Surface) -> None:
        """Render menu UI."""
        _draw_bg(surf)
        title = self._title_font.render("RAGDOLL HIT", True, c.UI_TEXT)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 120)))

        mouse = pygame.mouse.get_pos()
        for rect, label, enabled in (
            (self._start_rect, "1 PLAYER", True),
            (self._versus_rect, "2 PLAYERS (Soon)", False),
        ):
            colour = (70, 140, 90) if enabled else (70, 70, 75)
            if enabled and rect.collidepoint(mouse):
                colour = (90, 170, 110)
            pygame.draw.rect(surf, colour, rect, border_radius=10)
            text = self._btn_font.render(label, True, c.UI_TEXT)
            surf.blit(text, text.get_rect(center=rect.center))

        hints = [
            "A / D move   W jump   Space / J swing staff",
            "Physics ragdoll combat — Milestone 1",
        ]
        for i, line in enumerate(hints):
            surf.blit(
                self._hint_font.render(line, True, (180, 180, 190)),
                (c.SCREEN_W // 2 - 200, 470 + i * 24),
            )


class StageScene:
    """Single-player stage: player ragdoll vs AI."""

    def __init__(self) -> None:
        self._world = PhysicsWorld()
        self._terrain = Terrain(self._world.space)
        self._player: Optional[Ragdoll] = None
        self._enemy: Optional[Ragdoll] = None
        self._player_weapon: Optional[Weapon] = None
        self._enemy_weapon: Optional[Weapon] = None
        self._ai = AIController()
        self._font = pygame.font.SysFont("Arial", 20, bold=True)
        self._result: Optional[str] = None
        self._spawn_fighters()

    def _spawn_fighters(self) -> None:
        """Create player, enemy, and weapons."""
        self._world.clear_registries()
        self._player = Ragdoll(
            self._world.space,
            *c.PLAYER_SPAWN,
            team="player",
            colour=c.PLAYER_COL,
            facing=1,
        )
        self._enemy = Ragdoll(
            self._world.space,
            *c.ENEMY_SPAWN,
            team="enemy",
            colour=c.ENEMY_COL,
            facing=-1,
        )
        self._player_weapon = Weapon(self._world.space, self._player)
        self._enemy_weapon = Weapon(self._world.space, self._enemy)
        self._ai.reset()

    def handle_event(self, event: pygame.event.Event) -> None:
        """No pause menu in Milestone 1."""
        return

    def _read_player_input(self) -> tuple[int, bool, bool]:
        """Read keyboard controls for the player."""
        keys = pygame.key.get_pressed()
        move = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        jump = keys[pygame.K_w] or keys[pygame.K_UP]
        attack = keys[pygame.K_SPACE] or keys[pygame.K_j]
        return move, jump, attack

    def update(self) -> Optional[str]:
        """Simulate one frame; return win/lose when resolved."""
        if self._result is not None:
            return self._result
        if self._player is None or self._enemy is None:
            return None

        move, jump, attack = self._read_player_input()
        self._player.apply_control(move, jump)
        if attack:
            self._player_weapon.begin_swing()

        distance = self._player.position.get_distance(self._enemy.position)
        ai_move, ai_jump, ai_attack = self._ai.update(
            self._enemy.position.x,
            self._player.position.x,
            distance,
        )
        self._enemy.apply_control(ai_move, ai_jump)
        if ai_attack:
            self._enemy_weapon.begin_swing()

        self._player_weapon.update()
        self._enemy_weapon.update()
        self._player.update()
        self._enemy.update()

        self._world.step()
        for victim, damage, impulse, part in self._world.drain_hits():
            victim.take_hit(part, damage, impulse)

        if not self._enemy.is_alive:
            return "win"
        if not self._player.is_alive:
            return "lose"
        return None

    def draw(self, surf: pygame.Surface) -> None:
        """Render stage."""
        _draw_bg(surf)
        self._terrain.draw(surf)
        if self._player:
            self._player.draw(surf)
        if self._enemy:
            self._enemy.draw(surf)
        if self._player_weapon:
            self._player_weapon.draw(surf)
        if self._enemy_weapon:
            self._enemy_weapon.draw(surf)

        if self._player and self._enemy:
            _draw_health_bar(
                surf,
                40,
                24,
                180,
                self._player.health / c.MAX_HEALTH,
                c.HEALTH_PLAYER,
                "YOU",
                self._font,
            )
            _draw_health_bar(
                surf,
                c.SCREEN_W - 220,
                24,
                180,
                self._enemy.health / c.MAX_HEALTH,
                c.HEALTH_ENEMY,
                "ENEMY",
                self._font,
            )

        level = self._font.render("LEVEL 1", True, c.UI_TEXT)
        surf.blit(level, level.get_rect(midtop=(c.SCREEN_W // 2, 20)))


class GameOverScene:
    """Win/lose screen with restart options."""

    def __init__(self, won: bool) -> None:
        self.won = won
        self._title_font = pygame.font.SysFont("Arial", 52, bold=True)
        self._btn_font = pygame.font.SysFont("Arial", 24, bold=True)
        self._again_rect = pygame.Rect(c.SCREEN_W // 2 - 130, 320, 260, 50)
        self._menu_rect = pygame.Rect(c.SCREEN_W // 2 - 130, 390, 260, 50)
        self._choice: Optional[str] = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle button clicks."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._again_rect.collidepoint(event.pos):
                self._choice = "again"
            elif self._menu_rect.collidepoint(event.pos):
                self._choice = "menu"

    def update(self) -> Optional[str]:
        """Return navigation choice."""
        choice = self._choice
        self._choice = None
        return choice

    def draw(self, surf: pygame.Surface) -> None:
        """Render game over UI."""
        _draw_bg(surf)
        overlay = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))

        title_text = "YOU WIN!" if self.won else "YOU LOSE"
        title = self._title_font.render(title_text, True, c.UI_TEXT)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 200)))

        mouse = pygame.mouse.get_pos()
        for rect, label in ((self._again_rect, "Play Again"), (self._menu_rect, "Main Menu")):
            colour = (70, 130, 180)
            if rect.collidepoint(mouse):
                colour = (100, 160, 210)
            pygame.draw.rect(surf, colour, rect, border_radius=10)
            text = self._btn_font.render(label, True, c.UI_TEXT)
            surf.blit(text, text.get_rect(center=rect.center))


def main() -> None:
    """Run the pygame main loop."""
    pygame.init()
    screen = pygame.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    pygame.display.set_caption(c.TITLE)
    clock = pygame.time.Clock()

    scene: object = MenuScene()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif hasattr(scene, "handle_event"):
                scene.handle_event(event)

        if isinstance(scene, MenuScene):
            choice = scene.update()
            if choice == "stage":
                scene = StageScene()
        elif isinstance(scene, StageScene):
            result = scene.update()
            if result in ("win", "lose"):
                scene = GameOverScene(result == "win")
        elif isinstance(scene, GameOverScene):
            choice = scene.update()
            if choice == "again":
                scene = StageScene()
            elif choice == "menu":
                scene = MenuScene()

        screen.fill((0, 0, 0))
        scene.draw(screen)
        pygame.display.flip()
        clock.tick(c.FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
