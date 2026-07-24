"""Tank 1990 game loop — stages, spawning, combat, classic side panel."""

from __future__ import annotations

import random
from enum import Enum, auto

import pygame as pg

import config as cfg
from entities import DIR_DOWN, Bullet, Explosion, PowerUp, Tank
from mapdata import enemy_queue, get_stage
from tiles import StageMap


class State(Enum):
    TITLE = auto()
    STAGE_INTRO = auto()
    PLAY = auto()
    GAME_OVER = auto()
    STAGE_CLEAR = auto()
    WIN = auto()


class Game:
    """Battle City–style campaign."""

    def __init__(self) -> None:
        pg.init()
        pg.display.set_caption(cfg.TITLE)
        self.screen = pg.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H))
        self.clock = pg.time.Clock()
        self.running = True
        self.font = pg.font.SysFont("consolas", 18, bold=True)
        self.big = pg.font.SysFont("consolas", 36, bold=True)

        self.state = State.TITLE
        self.stage_num = 1
        self.lives = cfg.PLAYER_LIVES
        self.score = 0
        self.high_score = 0
        self.intro_timer = 0.0
        self.result_timer = 0.0

        self.stage: StageMap | None = None
        self.player: Tank | None = None
        self.enemies: list[Tank] = []
        self.bullets: list[Bullet] = []
        self.powerups: list[PowerUp] = []
        self.explosions: list[Explosion] = []
        self.spawn_queue: list[str] = []
        self.spawn_timer = 0.0
        self.spawn_slot = 0
        self.remaining_to_spawn = 0
        self.killed = 0
        self.freeze_timer = 0.0
        self.player_spawn_cd = 0.0

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(cfg.FPS) / 1000.0
            self._events()
            self._update(dt)
            self._draw()
            pg.display.flip()
        pg.quit()

    # ------------------------------------------------------------------
    def _events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if self.state == State.PLAY:
                        self.state = State.TITLE
                    else:
                        self.running = False
                elif event.key == pg.K_RETURN:
                    if self.state == State.TITLE:
                        self._new_game()
                    elif self.state in (State.GAME_OVER, State.WIN):
                        self.state = State.TITLE
                    elif self.state == State.STAGE_CLEAR:
                        self._advance_stage()

    def _advance_stage(self) -> None:
        """Go to the next stage or campaign victory."""
        self.stage_num += 1
        if self.stage_num > cfg.TOTAL_STAGES:
            self.state = State.WIN
            self.high_score = max(self.high_score, self.score)
        else:
            self._start_stage()

    def _new_game(self) -> None:
        self.stage_num = 1
        self.lives = cfg.PLAYER_LIVES
        self.score = 0
        self._start_stage()

    def _start_stage(self) -> None:
        self.stage = StageMap(get_stage(self.stage_num))
        self.enemies.clear()
        self.bullets.clear()
        self.powerups.clear()
        self.explosions.clear()
        self.spawn_queue = enemy_queue(self.stage_num)
        self.remaining_to_spawn = len(self.spawn_queue)
        self.spawn_timer = 0.5
        self.spawn_slot = 0
        self.killed = 0
        self.freeze_timer = 0.0
        self.player_spawn_cd = 0.0
        self._respawn_armed = False
        self.player = None
        self._spawn_player()
        self.state = State.STAGE_INTRO
        self.intro_timer = 1.6

    def _spawn_player(self) -> None:
        # Classic P1 spawn: left of base
        self.player = Tank(8 * cfg.TILE, 24 * cfg.TILE, friendly=True, kind="player")
        self.player.direction = 0  # UP
        self.player.invuln = cfg.SPAWN_INVULN

    def _spawn_bullet(self, bullet: Bullet) -> None:
        # Limit one friendly bullet on screen unless upgraded (level >= 2 => 2)
        if bullet.friendly:
            cap = 2 if self.player and self.player.level >= 2 else 1
            current = sum(1 for b in self.bullets if b.friendly and b.alive)
            if current >= cap:
                return
        self.bullets.append(bullet)

    # ------------------------------------------------------------------
    def _update(self, dt: float) -> None:
        if self.state == State.STAGE_INTRO:
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.state = State.PLAY
            return
        if self.state == State.STAGE_CLEAR:
            self.result_timer -= dt
            if self.result_timer <= 0:
                self._advance_stage()
            return
        if self.state != State.PLAY or self.stage is None:
            return

        self.stage.update(dt)
        self.freeze_timer = max(0.0, self.freeze_timer - dt)
        self.player_spawn_cd = max(0.0, self.player_spawn_cd - dt)

        tanks: list[Tank] = []
        if self.player and self.player.alive:
            tanks.append(self.player)
        tanks.extend(e for e in self.enemies if e.alive)

        keys = pg.key.get_pressed()
        if self.player and self.player.alive:
            self.player.update_player(dt, keys, self.stage, tanks, self._spawn_bullet)
        elif self.player_spawn_cd <= 0 and self.lives > 0 and self.player and not self.player.alive:
            pass  # wait handled below

        for enemy in self.enemies:
            enemy.update_enemy(
                dt,
                self.stage,
                tanks,
                self.player,
                self._spawn_bullet,
                frozen=self.freeze_timer > 0,
            )

        self._spawn_enemies(dt)
        self._update_bullets(dt)
        self._resolve_hits()
        self._update_powerups(dt)
        self._update_explosions(dt)
        self._respawn_player_if_needed()
        self._check_base()
        self._check_stage_clear()

    def _respawn_player_if_needed(self) -> None:
        """After a death, wait briefly then respawn or end the game."""
        if self.player is None or self.player.alive:
            self._respawn_armed = False
            return
        if self.lives <= 0:
            self.high_score = max(self.high_score, self.score)
            self.state = State.GAME_OVER
            return
        if not getattr(self, "_respawn_armed", False):
            self.player_spawn_cd = 1.0
            self._respawn_armed = True
            return
        if self.player_spawn_cd <= 0:
            self._spawn_player()
            self._respawn_armed = False

    def _spawn_enemies(self, dt: float) -> None:
        assert self.stage is not None
        alive = sum(1 for e in self.enemies if e.alive)
        if self.remaining_to_spawn <= 0 or alive >= cfg.MAX_ENEMIES_ON_FIELD:
            return
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return
        self.spawn_timer = cfg.SPAWN_INTERVAL
        slots = [(0, 0), (12 * cfg.TILE, 0), (24 * cfg.TILE, 0)]
        x, y = slots[self.spawn_slot % 3]
        self.spawn_slot += 1
        # Don't spawn on top of another tank
        rect = pg.Rect(int(x), int(y), cfg.TANK_SIZE, cfg.TANK_SIZE)
        for t in ([self.player] if self.player else []) + self.enemies:
            if t and t.alive and rect.colliderect(t.hitbox()):
                self.spawn_timer = 0.4
                return
        kind = self.spawn_queue[len(self.spawn_queue) - self.remaining_to_spawn]
        self.remaining_to_spawn -= 1
        enemy = Tank(x, y, friendly=False, kind=kind)
        enemy.direction = DIR_DOWN
        # Flashing red bonus tank drops a power-up
        if random.random() < 0.22:
            enemy.bonus = True
            enemy.color = cfg.ENEMY_RED
        self.enemies.append(enemy)

    def _update_bullets(self, dt: float) -> None:
        assert self.stage is not None
        for b in self.bullets:
            b.update(dt, self.stage)
        self.bullets = [b for b in self.bullets if b.alive]

    def _resolve_hits(self) -> None:
        # Bullet vs bullet (cancel)
        for i, a in enumerate(self.bullets):
            if not a.alive:
                continue
            for b in self.bullets[i + 1 :]:
                if not b.alive or a.friendly == b.friendly:
                    continue
                if a.hitbox().colliderect(b.hitbox()):
                    a.alive = b.alive = False

        # Bullets vs tanks
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            targets = []
            if bullet.friendly:
                targets = [e for e in self.enemies if e.alive]
            elif self.player and self.player.alive:
                targets = [self.player]
            for tank in targets:
                if bullet.hitbox().colliderect(tank.hitbox()):
                    bullet.alive = False
                    if tank.hurt():
                        self.explosions.append(
                            Explosion(
                                tank.x + cfg.TANK_SIZE / 2,
                                tank.y + cfg.TANK_SIZE / 2,
                                big=True,
                            )
                        )
                        if not tank.friendly:
                            self.killed += 1
                            self.score += {"basic": 100, "fast": 200, "power": 300, "armor": 400}.get(
                                tank.kind, 100
                            )
                            if tank.bonus:
                                self._drop_powerup(tank.x, tank.y)
                        else:
                            self.lives -= 1
                    break

    def _drop_powerup(self, x: float, y: float) -> None:
        kind = random.choice(PowerUp.KINDS)
        # Keep inside map
        x = max(0, min(cfg.MAP_W * cfg.TILE - cfg.TANK_SIZE, x))
        y = max(0, min(cfg.MAP_H * cfg.TILE - cfg.TANK_SIZE, y))
        self.powerups = [p for p in self.powerups if p.alive]  # only one classic style
        self.powerups.append(PowerUp(x, y, kind))

    def _update_powerups(self, dt: float) -> None:
        assert self.stage is not None
        for p in self.powerups:
            p.update(dt)
            if self.player and self.player.alive and p.alive and p.hitbox().colliderect(self.player.hitbox()):
                p.alive = False
                self._apply_powerup(p.kind)
        self.powerups = [p for p in self.powerups if p.alive]

    def _apply_powerup(self, kind: str) -> None:
        assert self.player is not None and self.stage is not None
        self.score += 500
        if kind == "helmet":
            self.player.shield = cfg.SHIELD_TIME
        elif kind == "clock":
            self.freeze_timer = cfg.FREEZE_TIME
        elif kind == "shovel":
            self.stage.fortify_base()
        elif kind == "star":
            self.player.apply_star()
        elif kind == "grenade":
            for e in self.enemies:
                if e.alive:
                    e.alive = False
                    self.killed += 1
                    self.score += 100
                    self.explosions.append(
                        Explosion(e.x + cfg.TANK_SIZE / 2, e.y + cfg.TANK_SIZE / 2, big=True)
                    )
        elif kind == "tank":
            self.lives += 1

    def _update_explosions(self, dt: float) -> None:
        for e in self.explosions:
            e.update(dt)
        self.explosions = [e for e in self.explosions if e.alive]

    def _check_base(self) -> None:
        assert self.stage is not None
        if not self.stage.base_alive:
            self.high_score = max(self.high_score, self.score)
            self.explosions.append(Explosion(13 * cfg.TILE, 25 * cfg.TILE, big=True))
            self.state = State.GAME_OVER

    def _check_stage_clear(self) -> None:
        if self.remaining_to_spawn <= 0 and not any(e.alive for e in self.enemies):
            self.state = State.STAGE_CLEAR
            self.result_timer = 2.5
            self.high_score = max(self.high_score, self.score)

    # ------------------------------------------------------------------
    def _draw(self) -> None:
        self.screen.fill(cfg.BLACK)
        if self.state == State.TITLE:
            self._draw_title()
            return
        if self.state == State.WIN:
            self._draw_center("YOU WIN!", f"SCORE {self.score}", "ENTER — TITLE")
            return
        if self.state == State.GAME_OVER:
            if self.stage:
                self._draw_playfield()
            self._draw_center("GAME OVER", f"SCORE {self.score}", "ENTER — TITLE")
            return

        self._draw_playfield()
        self._draw_panel()
        if self.state == State.STAGE_INTRO:
            overlay = pg.Surface((cfg.PLAY_W, cfg.PLAY_H), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            text = self.big.render(f"STAGE {self.stage_num}", True, cfg.UI_WHITE)
            self.screen.blit(text, text.get_rect(center=(cfg.PLAY_W // 2, cfg.PLAY_H // 2)))
        elif self.state == State.STAGE_CLEAR:
            text = self.big.render("STAGE CLEAR", True, cfg.UI_YELLOW)
            self.screen.blit(text, text.get_rect(center=(cfg.PLAY_W // 2, cfg.PLAY_H // 2)))
            hint = self.font.render("ENTER — NEXT", True, cfg.UI_WHITE)
            self.screen.blit(hint, hint.get_rect(center=(cfg.PLAY_W // 2, cfg.PLAY_H // 2 + 40)))

    def _draw_playfield(self) -> None:
        assert self.stage is not None
        field = self.screen.subsurface(pg.Rect(0, 0, cfg.PLAY_W, cfg.PLAY_H))
        self.stage.draw(field)
        for b in self.bullets:
            b.draw(field)
        for e in self.enemies:
            e.draw(field)
        if self.player:
            self.player.draw(field)
        for p in self.powerups:
            p.draw(field)
        self.stage.draw_eagle(field)
        self.stage.draw_grass_overlay(field)
        for ex in self.explosions:
            ex.draw(field)

    def _draw_panel(self) -> None:
        panel = pg.Rect(cfg.PLAY_W, 0, cfg.PANEL_W, cfg.SCREEN_H)
        pg.draw.rect(self.screen, cfg.PANEL_BG, panel)
        # Enemy icons remaining (including not yet spawned)
        left = self.remaining_to_spawn + sum(1 for e in self.enemies if e.alive)
        x0 = cfg.PLAY_W + 20
        y0 = 24
        for i in range(left):
            col = i % 2
            row = i // 2
            self._draw_enemy_icon(x0 + col * 28, y0 + row * 20)
        # IP / lives / stage
        y = cfg.SCREEN_H - 140
        self.screen.blit(self.font.render("IP", True, cfg.BLACK), (cfg.PLAY_W + 16, y))
        self._draw_player_icon(cfg.PLAY_W + 20, y + 28)
        self.screen.blit(
            self.font.render(str(max(0, self.lives)), True, cfg.BLACK),
            (cfg.PLAY_W + 50, y + 32),
        )
        self.screen.blit(self.font.render("FLAG", True, cfg.BLACK), (cfg.PLAY_W + 16, y + 70))
        flag = self.font.render(str(self.stage_num), True, cfg.BLACK)
        self.screen.blit(flag, (cfg.PLAY_W + 40, y + 95))

    def _draw_enemy_icon(self, x: int, y: int) -> None:
        pg.draw.rect(self.screen, cfg.BLACK, pg.Rect(x, y, 14, 14))
        pg.draw.rect(self.screen, cfg.ENEMY_DK, pg.Rect(x + 2, y + 2, 10, 10))

    def _draw_player_icon(self, x: int, y: int) -> None:
        pg.draw.rect(self.screen, cfg.PLAYER_DK, pg.Rect(x, y, 18, 18))
        pg.draw.rect(self.screen, cfg.PLAYER_YELLOW, pg.Rect(x + 3, y + 3, 12, 12))

    def _draw_title(self) -> None:
        self.screen.fill(cfg.BLACK)
        title = self.big.render("TANK 1990", True, cfg.UI_YELLOW)
        sub = self.font.render("BATTLE CITY LEGEND", True, cfg.UI_WHITE)
        tip = self.font.render("ENTER — START    ESC — QUIT", True, cfg.GRAY)
        ctrl = self.font.render("ARROWS/WASD MOVE   SPACE FIRE", True, cfg.GRAY)
        hs = self.font.render(f"HI-SCORE  {self.high_score:06d}", True, cfg.UI_ORANGE)
        self.screen.blit(title, title.get_rect(center=(cfg.SCREEN_W // 2, 200)))
        self.screen.blit(sub, sub.get_rect(center=(cfg.SCREEN_W // 2, 250)))
        self.screen.blit(hs, hs.get_rect(center=(cfg.SCREEN_W // 2, 320)))
        self.screen.blit(ctrl, ctrl.get_rect(center=(cfg.SCREEN_W // 2, 420)))
        self.screen.blit(tip, tip.get_rect(center=(cfg.SCREEN_W // 2, 460)))
        # Decorative tanks
        demo = Tank(6 * cfg.TILE, 10 * cfg.TILE, friendly=True)
        demo.invuln = 0
        demo.draw(self.screen)
        foe = Tank(16 * cfg.TILE, 10 * cfg.TILE, friendly=False, kind="armor")
        foe.invuln = 0
        foe.direction = DIR_DOWN
        foe.draw(self.screen)

    def _draw_center(self, title: str, line2: str, line3: str) -> None:
        overlay = pg.Surface((cfg.SCREEN_W, cfg.SCREEN_H), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        t = self.big.render(title, True, cfg.UI_ORANGE if "OVER" in title else cfg.UI_YELLOW)
        self.screen.blit(t, t.get_rect(center=(cfg.SCREEN_W // 2, cfg.SCREEN_H // 2 - 40)))
        a = self.font.render(line2, True, cfg.UI_WHITE)
        self.screen.blit(a, a.get_rect(center=(cfg.SCREEN_W // 2, cfg.SCREEN_H // 2 + 10)))
        b = self.font.render(line3, True, cfg.GRAY)
        self.screen.blit(b, b.get_rect(center=(cfg.SCREEN_W // 2, cfg.SCREEN_H // 2 + 50)))
