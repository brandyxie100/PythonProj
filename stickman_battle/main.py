"""Stickman Battle — entry point and scene management.

Run:
    python main.py

Scenes:
    MenuScene     — title screen, difficulty picker, controls legend.
    GameScene     — the battle in a single room.
    GameOverScene — win / lose result with restart / menu options.

Controls (in-game):
    A / ← → move left        D / → → move right
    W / ↑  → jump             Z / J → attack
"""

from __future__ import annotations

import math
import random
import sys
from typing import Optional

import pygame

import config as c
from entities import Enemy, HitEffect, Platform, Player, Stickman, Tire


# ---------------------------------------------------------------------------
# Gradient background helper
# ---------------------------------------------------------------------------

def _draw_bg(surf: pygame.Surface) -> None:
    """Fill surf with a vertical gradient matching the reference screenshots.

    Args:
        surf: target surface.
    """
    for y in range(c.SCREEN_H):
        t = y / c.SCREEN_H
        r = int(c.BG_TOP[0] + (c.BG_BOT[0] - c.BG_TOP[0]) * t)
        g = int(c.BG_TOP[1] + (c.BG_BOT[1] - c.BG_TOP[1]) * t)
        b = int(c.BG_TOP[2] + (c.BG_BOT[2] - c.BG_TOP[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (c.SCREEN_W, y))


# ---------------------------------------------------------------------------
# Menu scene
# ---------------------------------------------------------------------------

class MenuScene:
    """Title screen with difficulty selection."""

    _BUTTONS = ["easy", "normal", "hard"]
    _BTN_LABELS = {"easy": "Easy", "normal": "Normal", "hard": "Hard"}
    _BTN_COLORS = {
        "easy":   (50, 200, 80),
        "normal": (200, 160, 30),
        "hard":   (210, 50, 50),
    }
    _BTN_HOVER = {
        "easy":   (80, 230, 110),
        "normal": (230, 190, 60),
        "hard":   (240, 80,  80),
    }

    def __init__(self) -> None:
        self._font_title  = pygame.font.SysFont("Arial", 62, bold=True)
        self._font_sub    = pygame.font.SysFont("Arial", 28)
        self._font_btn    = pygame.font.SysFont("Arial", 26, bold=True)
        self._font_ctrl   = pygame.font.SysFont("Arial", 18)
        self._selected: Optional[str] = None

        # Layout button rects
        btn_w, btn_h = 160, 50
        total_w = len(self._BUTTONS) * btn_w + (len(self._BUTTONS) - 1) * 24
        start_x = (c.SCREEN_W - total_w) // 2
        cy = 360
        self._btn_rects: dict[str, pygame.Rect] = {}
        for i, name in enumerate(self._BUTTONS):
            self._btn_rects[name] = pygame.Rect(
                start_x + i * (btn_w + 24), cy, btn_w, btn_h
            )

        # Demo stickman animation (purely decorative)
        self._walk_phase = 0.0

    def handle_event(self, event: pygame.event.Event) -> Optional["GameScene"]:
        """Process input; return next scene on difficulty selection.

        Args:
            event: pygame event.

        Returns:
            GameScene if a difficulty was chosen, else None.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            for name, rect in self._btn_rects.items():
                if rect.collidepoint(pos):
                    return GameScene(name)
        return None

    def update(self) -> None:
        self._walk_phase += 0.12

    def draw(self, surf: pygame.Surface) -> None:
        """Render the menu.

        Args:
            surf: target surface.
        """
        _draw_bg(surf)

        # Title
        title = self._font_title.render("STICKMAN BATTLE", True, c.WHITE)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 120)))

        # Sub-title
        sub = self._font_sub.render("Choose your difficulty:", True, (180, 210, 240))
        surf.blit(sub, sub.get_rect(center=(c.SCREEN_W // 2, 300)))

        # Difficulty buttons
        mouse_pos = pygame.mouse.get_pos()
        for name, rect in self._btn_rects.items():
            hovered = rect.collidepoint(mouse_pos)
            col = self._BTN_HOVER[name] if hovered else self._BTN_COLORS[name]
            pygame.draw.rect(surf, col, rect, border_radius=10)
            pygame.draw.rect(surf, c.WHITE, rect, 2, border_radius=10)
            lbl = self._font_btn.render(self._BTN_LABELS[name], True, c.WHITE)
            surf.blit(lbl, lbl.get_rect(center=rect.center))

        # Controls legend
        controls = [
            "A / ←  Move left       D / →  Move right",
            "W / ↑  Jump            Z / J  Attack",
        ]
        for i, line in enumerate(controls):
            txt = self._font_ctrl.render(line, True, (160, 190, 220))
            surf.blit(txt, txt.get_rect(center=(c.SCREEN_W // 2, 450 + i * 26)))

        # Decorative stickmen
        self._draw_demo_stickmen(surf)

    def _draw_demo_stickmen(self, surf: pygame.Surface) -> None:
        """Render three colourful stickmen walking across the bottom.

        Args:
            surf: target surface.
        """
        ph = self._walk_phase
        y_base = c.SCREEN_H - 30
        data = [
            (c.BLUE_COL,   130, "sword"),
            (c.RED_COL,    450, "hammer"),
            (c.YELLOW_COL, 770, "pickaxe"),
        ]
        for col, base_x, wpn in data:
            # Simple oscillation so they don't drift off screen
            cx = base_x + math.sin(ph * 0.4 + base_x * 0.01) * 30
            dummy = Stickman(cx, y_base, col, 100, wpn)
            dummy.walk_phase = ph + base_x * 0.02
            dummy.facing     = 1
            dummy.draw(surf)


# ---------------------------------------------------------------------------
# Game scene — the battle room
# ---------------------------------------------------------------------------

class GameScene:
    """Single-room battle arena.

    Level layout (pixel coords, screen is 900 × 600):
        - Floor at y = 555
        - Mid-left platform  220 × 18 @ (100, 410)
        - Mid-right platform 220 × 18 @ (580, 410)
        - Upper-centre platform 180 × 18 @ (360, 280)
        - Left-wall ledge   120 × 18 @ (20,  330)
        - Right-wall ledge  120 × 18 @ (760, 330)
    """

    def __init__(self, difficulty: str) -> None:
        """Args:
            difficulty: one of 'easy', 'normal', 'hard'.
        """
        self.difficulty = difficulty
        self._cfg = c.DIFFICULTIES[difficulty]
        self._font     = pygame.font.SysFont("Arial", 22, bold=True)
        self._font_big = pygame.font.SysFont("Arial", 36, bold=True)
        self._font_sm  = pygame.font.SysFont("Arial", 17)

        # ---- Build platforms ----
        floor_y = c.SCREEN_H - 20
        self._platforms: list[Platform] = [
            # floor
            Platform(0, floor_y, c.SCREEN_W, 20),
            # mid-left
            Platform(80,  410, 220, 18),
            # mid-right
            Platform(600, 410, 220, 18),
            # upper-centre
            Platform(355, 280, 190, 18),
            # left-wall ledge
            Platform(10,  330, 130, 18),
            # right-wall ledge
            Platform(760, 330, 130, 18),
        ]

        # ---- Player ----
        self._player = Player(
            x=c.SCREEN_W // 2,
            y=float(floor_y),
            health=self._cfg["player_health"],
            weapon_name="sword",
        )

        # ---- Enemies ----
        self._enemies: list[Enemy] = []
        self._spawn_enemies(self._cfg["enemy_count"])

        # ---- Tires ----
        self._tires: list[Tire] = []
        tire_xs = [160, 350, 560, 740]
        for tx in tire_xs:
            self._tires.append(Tire(tx, floor_y - c.TIRE_RADIUS))

        # ---- Effects ----
        self._effects: list[HitEffect] = []

        # ---- Result ----
        self._result: Optional[str] = None   # "win" | "lose"
        self._result_timer = 0                # frames before auto-transition
        self._total_enemies = self._cfg["enemy_count"]

    # ------------------------------------------------------------------
    # Enemy spawning
    # ------------------------------------------------------------------

    def _spawn_enemies(self, count: int) -> None:
        """Populate the enemy list.

        Args:
            count: number of enemies to create.
        """
        cfg   = self._cfg
        floor_y = c.SCREEN_H - 20
        # Evenly-spaced x positions near the edges, alternating sides
        xs = [80, c.SCREEN_W - 80, 200, c.SCREEN_W - 200, 350]
        wpns = cfg["enemy_weapons"]

        for i in range(count):
            wpn = wpns[i % len(wpns)]
            col = c.RED_COL if i % 2 == 0 else (210, 60, 160)  # red or magenta
            e = Enemy(
                x=float(xs[i % len(xs)]),
                y=float(floor_y),
                health=cfg["enemy_health"],
                speed=cfg["enemy_speed"],
                damage=cfg["enemy_damage"],
                attack_cd=cfg["enemy_attack_cd"],
                weapon_name=wpn,
                color=col,
            )
            # Alternate facing direction
            e.facing = 1 if i % 2 == 0 else -1
            self._enemies.append(e)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> Optional["GameOverScene"]:
        """Handle player input events.

        Args:
            event: pygame event.

        Returns:
            GameOverScene when battle ends, else None.
        """
        return None   # transition is handled in update()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self) -> Optional["GameOverScene"]:
        """Step all entities and check win / lose condition.

        Returns:
            GameOverScene when the battle is over, else None.
        """
        if self._result:
            self._result_timer -= 1
            if self._result_timer <= 0:
                return GameOverScene(self._result, self.difficulty)
            return None

        keys = pygame.key.get_pressed()

        # Player
        self._player.handle_input(keys)
        self._player.update(self._platforms)

        # Enemies
        for enemy in self._enemies:
            enemy.update(self._platforms, self._player)

        # Tires
        for tire in self._tires:
            tire.update(self._platforms)

        # Effects
        for fx in list(self._effects):
            fx.update()
            if not fx.alive():
                self._effects.remove(fx)

        # --- Collision: player attacks enemies ---
        dmg_mult = self._cfg["player_damage_mult"]
        phitbox  = self._player.weapon_hitbox()
        if phitbox:
            for enemy in self._enemies:
                if id(enemy) in self._player._hit_targets:
                    continue
                if enemy.alive and phitbox.colliderect(enemy.rect):
                    base_dmg = self._player.weapon["damage"] * dmg_mult
                    knockback = self._player.weapon["knockback"]
                    enemy.take_damage(base_dmg, source_x=self._player.x)
                    enemy.vx += self._player.facing * knockback
                    enemy.vy -= 2.5
                    self._player._hit_targets.add(id(enemy))
                    tip = self._player.weapon_tip()
                    self._effects.append(HitEffect(int(tip[0]), int(tip[1])))

        # --- Collision: enemies attack player ---
        for enemy in self._enemies:
            if not enemy.alive:
                continue
            enemy.check_hit_player(self._player)

        # --- Stickman–tire interaction ---
        for sm in [self._player] + self._enemies:
            if not sm.alive:
                continue
            for tire in self._tires:
                sr = sm.rect
                dist = math.hypot(sm.x - tire._cx, sm.y - c.STICK_H / 2 - tire._cy)
                if dist < c.TIRE_RADIUS + c.STICK_W / 2 + 4:
                    sm.push_tire(tire)

        # --- Remove dead enemies ---
        self._enemies = [e for e in self._enemies if e.alive]

        # --- Win / lose check ---
        if not self._player.alive:
            self._result = "lose"
            self._result_timer = 90
        elif len(self._enemies) == 0:
            self._result = "win"
            self._result_timer = 90

        return None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface) -> None:
        """Render the battle scene.

        Args:
            surf: target surface.
        """
        _draw_bg(surf)

        # Platforms
        for plat in self._platforms:
            surf.blit(plat.image, plat.rect)

        # Tires
        for tire in self._tires:
            surf.blit(tire.image, tire.rect)

        # Enemies
        for enemy in self._enemies:
            enemy.draw(surf)

        # Player
        self._player.draw(surf)

        # Hit effects
        for fx in self._effects:
            surf.blit(fx.image, fx.rect)

        # HUD
        self._draw_hud(surf)

        # Result overlay
        if self._result:
            self._draw_result_overlay(surf)

    def _draw_hud(self, surf: pygame.Surface) -> None:
        """Render game HUD: difficulty, enemies remaining.

        Args:
            surf: target surface.
        """
        diff_label = self.difficulty.capitalize()
        col_map = {"Easy": c.DIFFICULTIES["easy"], "Normal": c.DIFFICULTIES["normal"], "Hard": c.DIFFICULTIES["hard"]}
        diff_colors = {"Easy": (50, 200, 80), "Normal": (220, 180, 30), "Hard": (220, 60, 60)}
        d_col = diff_colors.get(diff_label, c.WHITE)

        # Difficulty badge (top-left)
        badge = self._font.render(f"  {diff_label}  ", True, c.WHITE)
        badge_rect = badge.get_rect(topleft=(10, 10))
        pygame.draw.rect(surf, d_col, badge_rect.inflate(6, 4), border_radius=6)
        surf.blit(badge, badge_rect)

        # Enemies remaining (top-right)
        remaining = len(self._enemies)
        txt = self._font.render(f"Enemies: {remaining} / {self._total_enemies}", True, c.WHITE)
        surf.blit(txt, txt.get_rect(topright=(c.SCREEN_W - 10, 10)))

        # Player weapon indicator (bottom-left)
        wpn_txt = self._font_sm.render(
            f"Weapon: {self._player.weapon_name.capitalize()}", True, (200, 220, 240)
        )
        surf.blit(wpn_txt, (10, c.SCREEN_H - 28))

        # Controls reminder (bottom-right, small)
        ctrl_txt = self._font_sm.render("A/D: Move  W: Jump  Z/J: Attack", True, (140, 170, 200))
        surf.blit(ctrl_txt, ctrl_txt.get_rect(bottomright=(c.SCREEN_W - 8, c.SCREEN_H - 8)))

    def _draw_result_overlay(self, surf: pygame.Surface) -> None:
        """Translucent overlay showing win / lose result.

        Args:
            surf: target surface.
        """
        overlay = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        surf.blit(overlay, (0, 0))

        if self._result == "win":
            label = "YOU WIN!"
            col   = (80, 240, 80)
        else:
            label = "YOU LOSE!"
            col   = (240, 80, 80)

        txt = self._font_big.render(label, True, col)
        surf.blit(txt, txt.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2)))


# ---------------------------------------------------------------------------
# Game-over scene
# ---------------------------------------------------------------------------

class GameOverScene:
    """Displays the battle result and offers restart / menu buttons."""

    _BTN_W, _BTN_H = 180, 50

    def __init__(self, result: str, difficulty: str) -> None:
        """Args:
            result: 'win' or 'lose'.
            difficulty: difficulty key used in the match.
        """
        self.result     = result
        self.difficulty = difficulty
        self._font_big  = pygame.font.SysFont("Arial", 60, bold=True)
        self._font_med  = pygame.font.SysFont("Arial", 28)
        self._font_btn  = pygame.font.SysFont("Arial", 24, bold=True)

        cx = c.SCREEN_W // 2
        self._btn_retry = pygame.Rect(cx - self._BTN_W - 16, 400, self._BTN_W, self._BTN_H)
        self._btn_menu  = pygame.Rect(cx + 16,                400, self._BTN_W, self._BTN_H)

    def handle_event(self, event: pygame.event.Event) -> Optional[object]:
        """Handle button clicks.

        Args:
            event: pygame event.

        Returns:
            GameScene on retry, MenuScene on back-to-menu, None otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self._btn_retry.collidepoint(pos):
                return GameScene(self.difficulty)
            if self._btn_menu.collidepoint(pos):
                return MenuScene()
        return None

    def update(self) -> None:
        pass

    def draw(self, surf: pygame.Surface) -> None:
        """Render game-over screen.

        Args:
            surf: target surface.
        """
        _draw_bg(surf)

        # Big result text
        if self.result == "win":
            label = "VICTORY!"
            col   = (80, 240, 80)
            sub   = "You defeated all enemies!"
        else:
            label = "DEFEATED!"
            col   = (240, 80, 80)
            sub   = "Better luck next time..."

        title = self._font_big.render(label, True, col)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 180)))

        sub_txt = self._font_med.render(sub, True, (200, 220, 240))
        surf.blit(sub_txt, sub_txt.get_rect(center=(c.SCREEN_W // 2, 260)))

        diff_txt = self._font_med.render(
            f"Difficulty: {self.difficulty.capitalize()}", True, c.WHITE
        )
        surf.blit(diff_txt, diff_txt.get_rect(center=(c.SCREEN_W // 2, 320)))

        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        for rect, label_str, base_col in [
            (self._btn_retry, "Play Again", (50, 130, 220)),
            (self._btn_menu,  "Main Menu",  (80, 80, 130)),
        ]:
            hov_col = tuple(min(255, v + 30) for v in base_col)
            col = hov_col if rect.collidepoint(mouse_pos) else base_col
            pygame.draw.rect(surf, col, rect, border_radius=10)
            pygame.draw.rect(surf, c.WHITE, rect, 2, border_radius=10)
            btn_txt = self._font_btn.render(label_str, True, c.WHITE)
            surf.blit(btn_txt, btn_txt.get_rect(center=rect.center))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Initialise pygame and run the main game loop."""
    pygame.init()
    pygame.display.set_caption(c.TITLE)
    screen = pygame.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    clock  = pygame.time.Clock()

    scene: object = MenuScene()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            result = scene.handle_event(event)   # type: ignore[attr-defined]
            if result is not None:
                scene = result

        # Update and possible scene transition
        next_scene = scene.update()               # type: ignore[attr-defined]
        if next_scene is not None:
            scene = next_scene

        scene.draw(screen)                        # type: ignore[attr-defined]
        pygame.display.flip()
        clock.tick(c.FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
