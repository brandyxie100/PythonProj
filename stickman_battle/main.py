"""Stickman Battle — entry point and scene management.

Run:
    python main.py

Scenes:
    MenuScene     — title screen, difficulty picker, controls legend.
    GameScene     — the battle in a single room.
    GameOverScene — win / lose result with restart / menu options.

Controls (in-game):
    A / ← → move left        D / → → move right
    W / ↑  → jump (press again mid-air for double jump)
    Z / J → attack (360° weapon spin)
    B     → throw grenade
"""

from __future__ import annotations

import math
import random
import sys
from typing import Optional

import pygame

import config as c
from entities import (
    AK47Pickup,
    Arrow,
    BowPickup,
    Enemy,
    Grenade,
    HitEffect,
    MuzzleFlash,
    Platform,
    Player,
    RifleBullet,
    ShellCasing,
    SpringBall,
    Stickman,
    Tire,
)


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
            "W / ↑  Jump (double-tap mid-air for extra height)",
            "Z / J  Melee spin / bow / AK-47 (hold to auto-fire)",
            "B      Throw grenade (6 per match)",
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

        # ---- Spring balls (fixed boost pads) ----
        self._springs: list[SpringBall] = [
            SpringBall(c.SCREEN_W // 2, floor_y - c.SPRING_BALL_RADIUS),
            SpringBall(190, 410 - c.SPRING_BALL_RADIUS),
            SpringBall(710, 410 - c.SPRING_BALL_RADIUS),
            SpringBall(450, 280 - c.SPRING_BALL_RADIUS),
        ]

        # ---- Effects ----
        self._effects: list[HitEffect] = []

        # ---- Bow pickup & projectiles ----
        self._bow_pickup: Optional[BowPickup] = None
        self._arrows: list[Arrow] = []
        self._grenades: list[Grenade] = []

        # ---- AK-47 timed spawn & rifle effects ----
        self._match_frames = 0
        self._ak47_spawned = False
        self._ak47_pickup: Optional[AK47Pickup] = None
        self._bullets: list[RifleBullet] = []
        self._muzzle_flashes: list[MuzzleFlash] = []
        self._shell_casings: list[ShellCasing] = []

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

    def _spawn_bow_pickup(self) -> None:
        """Spawn a shiny bow set at a random arena location."""
        floor_y = c.SCREEN_H - 20
        spots = [
            (random.randint(100, c.SCREEN_W - 100), floor_y),
            (random.randint(90, 280), 410),
            (random.randint(620, 810), 410),
            (random.randint(370, 530), 280),
            (random.randint(30, 130), 330),
            (random.randint(770, 870), 330),
        ]
        x, y = random.choice(spots)
        self._bow_pickup = BowPickup(float(x), float(y))

    def _spawn_ak47_pickup(self) -> None:
        """Spawn AK-47 at a random map location (30 s after match start)."""
        floor_y = c.SCREEN_H - 20
        spots = [
            (random.randint(100, c.SCREEN_W - 100), floor_y),
            (random.randint(90, 280), 410),
            (random.randint(620, 810), 410),
            (random.randint(370, 530), 280),
            (random.randint(30, 130), 330),
            (random.randint(770, 870), 330),
        ]
        x, y = random.choice(spots)
        self._ak47_pickup = AK47Pickup(float(x), float(y))

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
        self._match_frames += 1

        if not self._ak47_spawned and self._match_frames >= c.AK47_SPAWN_DELAY_F:
            self._spawn_ak47_pickup()
            self._ak47_spawned = True

        # Player
        self._player.handle_input(keys)
        self._player.update(self._platforms)

        # Bow shot (ranged attack)
        arrow = self._player.consume_shot()
        if arrow is not None:
            arrow.damage *= self._cfg["player_damage_mult"]
            self._arrows.append(arrow)

        # AK-47 automatic fire
        bullet, flash, casing = self._player.consume_rifle_shot()
        if bullet is not None:
            bullet.damage *= self._cfg["player_damage_mult"]
            self._bullets.append(bullet)
        if flash is not None:
            self._muzzle_flashes.append(flash)
        if casing is not None:
            self._shell_casings.append(casing)

        # Player grenade throw
        grenade = self._player.consume_grenade_throw()
        if grenade is not None:
            self._grenades.append(grenade)

        # Enemies
        for enemy in self._enemies:
            enemy.update(self._platforms, self._player)
            eg = enemy.maybe_throw_grenade(self._player, self._cfg)
            if eg is not None:
                self._grenades.append(eg)

        # Tires
        for tire in self._tires:
            tire.update(self._platforms)

        # Spring balls (pulse animation only — position is fixed)
        for spring in self._springs:
            spring.update()

        # Bow pickup countdown & collection
        if self._bow_pickup is not None:
            self._bow_pickup.update()
            if self._bow_pickup.try_collect(self._player):
                self._bow_pickup = None
            elif not self._bow_pickup.active:
                self._bow_pickup = None

        # AK-47 pickup
        if self._ak47_pickup is not None:
            self._ak47_pickup.update()
            if self._ak47_pickup.try_collect(self._player):
                self._ak47_pickup = None
            elif not self._ak47_pickup.active:
                self._ak47_pickup = None

        # Flying arrows
        for arrow in self._arrows:
            arrow.update()
            for enemy in self._enemies:
                if not enemy.alive:
                    continue
                if arrow.try_hit(enemy):
                    self._effects.append(HitEffect(int(arrow.x), int(arrow.y)))
                    break
        self._arrows = [a for a in self._arrows if a.alive]

        # Rifle bullets
        for bullet in self._bullets:
            bullet.update()
            for enemy in self._enemies:
                if not enemy.alive:
                    continue
                if bullet.try_hit(enemy):
                    self._effects.append(HitEffect(int(bullet.x), int(bullet.y)))
                    break
        self._bullets = [b for b in self._bullets if b.alive]

        # Muzzle flashes & shell casings (firing VFX)
        for flash in self._muzzle_flashes:
            flash.update()
        self._muzzle_flashes = [f for f in self._muzzle_flashes if f.alive]
        for shell in self._shell_casings:
            shell.update()
        self._shell_casings = [s for s in self._shell_casings if s.alive]

        # Flying grenades and explosions
        for grenade in self._grenades:
            grenade.update(self._platforms)
            if grenade.just_exploded:
                hits = grenade.apply_explosion([self._player] + self._enemies)
                self._effects.append(HitEffect(int(grenade.x), int(grenade.y)))
                # Add extra flashes when multiple targets are hit.
                for target in hits[1:]:
                    self._effects.append(HitEffect(int(target.x), int(target.y - target.TOTAL_H / 2)))
        self._grenades = [g for g in self._grenades if g.alive]

        # Effects
        for fx in list(self._effects):
            fx.update()
            if not fx.alive():
                self._effects.remove(fx)

        # --- Collision: player melee hits enemies (skip when using ranged) ---
        if not self._player.is_using_ranged():
            dmg_mult = self._cfg["player_damage_mult"]
            base_dmg = self._player.weapon["damage"] * dmg_mult
            knockback = self._player.weapon["knockback"]
            for _target, tip_x, tip_y in self._player.check_weapon_hits(
                self._enemies, base_dmg, knockback
            ):
                self._effects.append(HitEffect(int(tip_x), int(tip_y)))

        # --- Collision: enemies attack player ---
        for enemy in self._enemies:
            if not enemy.alive:
                continue
            if enemy.check_hit_player(self._player):
                tip = enemy.weapon_tip()
                self._effects.append(HitEffect(int(tip[0]), int(tip[1])))

        # --- Spring ball boosts ---
        for sm in [self._player] + self._enemies:
            if not sm.alive:
                continue
            for spring in self._springs:
                spring.try_boost(sm)

        # --- Stickman–tire interaction ---
        for sm in [self._player] + self._enemies:
            if not sm.alive:
                continue
            for tire in self._tires:
                sr = sm.rect
                dist = math.hypot(sm.x - tire._cx, sm.y - c.STICK_H / 2 - tire._cy)
                if dist < c.TIRE_RADIUS + c.STICK_W / 2 + 4:
                    sm.push_tire(tire)

        # --- Remove dead enemies & maybe spawn bow pickup ---
        killed = [e for e in self._enemies if not e.alive]
        if killed and random.random() < c.BOW_SPAWN_CHANCE:
            self._spawn_bow_pickup()
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

        # Spring balls (drawn before characters so feet appear on top)
        for spring in self._springs:
            spring.draw(surf)

        # Bow pickup (shiny, with countdown)
        if self._bow_pickup is not None and self._bow_pickup.active:
            self._bow_pickup.draw(surf)

        # AK-47 pickup
        if self._ak47_pickup is not None and self._ak47_pickup.active:
            self._ak47_pickup.draw(surf)

        # Arrows in flight
        for arrow in self._arrows:
            arrow.draw(surf)

        # Rifle bullets
        for bullet in self._bullets:
            bullet.draw(surf)

        # Shell casings (behind characters)
        for shell in self._shell_casings:
            shell.draw(surf)

        # Grenades in flight / explosion pulse
        for grenade in self._grenades:
            grenade.draw(surf)

        # Enemies
        for enemy in self._enemies:
            enemy.draw(surf)

        # Player
        self._player.draw(surf)

        # Muzzle flashes (on top of player)
        for flash in self._muzzle_flashes:
            flash.draw(surf)

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
        if self._player.is_using_ak47():
            wpn_txt = self._font_sm.render(
                f"AK-47 — Rounds: {self._player._rounds_left}",
                True, (140, 255, 160),
            )
        elif self._player.is_using_bow():
            wpn_txt = self._font_sm.render(
                f"Bow — Arrows: {self._player._arrows_left}",
                True, (255, 220, 120),
            )
        else:
            wpn_txt = self._font_sm.render(
                f"Weapon: {self._player.weapon_name.capitalize()}",
                True, (200, 220, 240),
            )
        surf.blit(wpn_txt, (10, c.SCREEN_H - 28))
        grenade_txt = self._font_sm.render(
            f"Grenades: {self._player.grenades_left}",
            True, (255, 190, 120),
        )
        surf.blit(grenade_txt, (10, c.SCREEN_H - 48))

        # Bow pickup hint
        if self._bow_pickup is not None and self._bow_pickup.active:
            hint = self._font_sm.render(
                f"Bow nearby! {self._bow_pickup.seconds_left}s",
                True, (255, 230, 100),
            )
            surf.blit(hint, hint.get_rect(midtop=(c.SCREEN_W // 2, 36)))

        # AK-47 spawn countdown / pickup hint
        if not self._ak47_spawned:
            secs = max(0, (c.AK47_SPAWN_DELAY_F - self._match_frames) // c.FPS)
            ak_hint = self._font_sm.render(
                f"AK-47 drops in {secs}s",
                True, (140, 255, 180),
            )
            surf.blit(ak_hint, ak_hint.get_rect(midtop=(c.SCREEN_W // 2, 58)))
        elif self._ak47_pickup is not None and self._ak47_pickup.active:
            ak_hint = self._font_sm.render(
                "AK-47 on the map! Grab it!",
                True, (140, 255, 180),
            )
            surf.blit(ak_hint, ak_hint.get_rect(midtop=(c.SCREEN_W // 2, 58)))

        # Controls reminder (bottom-right, small)
        ctrl_txt = self._font_sm.render(
            "A/D: Move  W: Jump  Z/J: Attack/Shoot  B: Grenade",
            True, (140, 170, 200),
        )
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
