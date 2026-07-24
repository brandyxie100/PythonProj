"""Main game controller — state machine, combat loop, spawning."""

from __future__ import annotations

import math
import random
from enum import Enum, auto

import pygame as pg

import config as cfg
import sprites
from entities import Boss, Bullet, Enemy, Loadout, Player, PowerUp
from missions import MISSIONS, MissionSpec, WaveSpec
from ui import HUD, MenuView
from world import OceanWorld


class State(Enum):
    """Top-level game states."""

    TITLE = auto()
    BRIEFING = auto()
    HANGAR = auto()
    PLAY = auto()
    RESULT = auto()


class Game:
    """1942 campaign runner."""

    def __init__(self) -> None:
        """Initialize display and persistent campaign data."""
        pg.init()
        pg.display.set_caption(cfg.TITLE)
        self.screen = pg.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H))
        self.clock = pg.time.Clock()
        self.running = True

        self.state = State.TITLE
        self.menu = MenuView()
        self.hud = HUD()
        self.world = OceanWorld()

        self.high_score = 0
        self.score = 0
        self.spendable = 0  # score banked for hangar purchases
        self.mission_index = 0  # 0-based
        self.loadout = Loadout()
        self.hangar_cursor = 0

        self.player: Player | None = None
        self.bullets: list[Bullet] = []
        self.enemies: list[Enemy] = []
        self.powerups: list[PowerUp] = []
        self.particles: list[dict] = []
        self.boss: Boss | None = None

        self.mission_time = 0.0
        self.spawned_waves: set[int] = set()
        self.boss_spawned = False
        self.result_victory = False
        self.result_final = False
        self.banner = ""
        self.banner_timer = 0.0
        self.outro_timer = 0.0
        self.outro_kind: str | None = None  # "win" | "lose"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Main loop."""
        while self.running:
            dt = self.clock.tick(cfg.FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pg.display.flip()
        pg.quit()

    def _handle_events(self) -> None:
        """Global and state-specific input."""
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if self.state == State.PLAY:
                        self._fail_mission()
                    elif self.state == State.HANGAR:
                        self.state = State.BRIEFING
                    elif self.state == State.TITLE:
                        self.running = False
                    else:
                        self.state = State.TITLE
                elif event.key == pg.K_RETURN:
                    self._on_confirm()
                elif event.key == pg.K_h and self.state == State.BRIEFING:
                    self.state = State.HANGAR
                elif self.state == State.HANGAR:
                    if event.key in (pg.K_UP, pg.K_w):
                        self.hangar_cursor = (self.hangar_cursor - 1) % 5
                    elif event.key in (pg.K_DOWN, pg.K_s):
                        self.hangar_cursor = (self.hangar_cursor + 1) % 5
                elif self.state == State.PLAY and event.key == pg.K_b:
                    self._use_bomb()

    def _on_confirm(self) -> None:
        """ENTER handling by state."""
        if self.state == State.TITLE:
            self.mission_index = 0
            self.score = 0
            self.spendable = 0
            self.loadout = Loadout()
            self.state = State.BRIEFING
        elif self.state == State.BRIEFING:
            self._start_mission()
        elif self.state == State.HANGAR:
            self._buy_upgrade()
        elif self.state == State.RESULT:
            if self.result_victory and not self.result_final:
                self.mission_index += 1
                if self.mission_index >= cfg.TOTAL_MISSIONS:
                    self.state = State.TITLE
                else:
                    self.state = State.BRIEFING
            else:
                self.state = State.TITLE

    # ------------------------------------------------------------------
    # Mission flow
    # ------------------------------------------------------------------
    def _current_mission(self) -> MissionSpec:
        return MISSIONS[self.mission_index]

    def _start_mission(self) -> None:
        """Reset combat scene for the active mission."""
        m = self._current_mission()
        self.world = OceanWorld()
        self.world.set_speed(m.scroll_speed)
        self.player = Player(self.loadout)
        self.bullets.clear()
        self.enemies.clear()
        self.powerups.clear()
        self.particles.clear()
        self.boss = None
        self.mission_time = 0.0
        self.spawned_waves.clear()
        self.boss_spawned = False
        self.banner = m.title
        self.banner_timer = 2.2
        self.outro_timer = 0.0
        self.outro_kind = None
        self.state = State.PLAY

    def _spawn_bullet(self, bullet: Bullet) -> None:
        self.bullets.append(bullet)

    def _use_bomb(self) -> None:
        if self.player is None or not self.player.try_bomb():
            return
        radius = cfg.BOMB_CLEAR_RADIUS + self.loadout.bomb_level * 30
        cx, cy = self.player.x, self.player.y
        for enemy in self.enemies:
            if enemy.alive and math.hypot(enemy.x - cx, enemy.y - cy) <= radius:
                enemy.hurt(99)
                self._on_enemy_killed(enemy)
        if self.boss and self.boss.alive and math.hypot(self.boss.x - cx, self.boss.y - cy) <= radius:
            self.boss.hurt(12)
        self.bullets = [b for b in self.bullets if b.friendly]
        self.particles.extend(sprites.spawn_explosion_particles(cx, cy, 28))
        # Screen flash via particles ring
        for ang in range(0, 360, 15):
            rad = math.radians(ang)
            self.particles.append(
                {
                    "x": cx + math.cos(rad) * 20,
                    "y": cy + math.sin(rad) * 20,
                    "vx": math.cos(rad) * 200,
                    "vy": math.sin(rad) * 200,
                    "life": 0.45,
                    "max_life": 0.45,
                    "r": 3,
                    "color": cfg.UI_WHITE,
                }
            )

    def _buy_upgrade(self) -> None:
        """Purchase hangar upgrade at cursor."""
        attrs = ["fire_level", "spread_level", "speed_level", "shield_level", "bomb_level"]
        caps = [4, 3, 3, 3, 3]
        attr = attrs[self.hangar_cursor]
        level = getattr(self.loadout, attr)
        cap = caps[self.hangar_cursor]
        if level >= cap:
            return
        cost = cfg.UPGRADE_COST_BASE * (level + 1)
        if self.spendable < cost:
            return
        self.spendable -= cost
        setattr(self.loadout, attr, level + 1)

    def _fail_mission(self) -> None:
        self.result_victory = False
        self.result_final = False
        self.high_score = max(self.high_score, self.score)
        self.state = State.RESULT

    def _clear_mission(self) -> None:
        self.result_victory = True
        self.result_final = self.mission_index >= cfg.TOTAL_MISSIONS - 1
        # Bank a mission stipend for hangar upgrades (not full score reuse).
        self.spendable += 500 + self._current_mission().number * 80
        self.high_score = max(self.high_score, self.score)
        self.state = State.RESULT

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def _update(self, dt: float) -> None:
        if self.state != State.PLAY:
            return
        assert self.player is not None
        m = self._current_mission()
        self.mission_time += dt
        self.banner_timer = max(0.0, self.banner_timer - dt)
        self.world.update(dt)

        keys = pg.key.get_pressed()
        self.player.update(dt, keys, self._spawn_bullet)

        self._spawn_waves(m)
        self._update_entities(dt)
        self._resolve_collisions()
        self._update_particles(dt)
        self._check_mission_end(m)

        if not self.player.alive and self.outro_kind is None:
            self.outro_kind = "lose"
            self.outro_timer = 1.2
            self.particles.extend(
                sprites.spawn_explosion_particles(self.player.x, self.player.y, 24)
            )
        if self.outro_kind is not None:
            self.outro_timer -= dt
            if self.outro_timer <= 0:
                if self.outro_kind == "win":
                    self._clear_mission()
                else:
                    self._fail_mission()
                self.outro_kind = None

    def _spawn_waves(self, m: MissionSpec) -> None:
        for i, wave in enumerate(m.waves):
            if i in self.spawned_waves:
                continue
            if self.mission_time >= wave.delay:
                self.spawned_waves.add(i)
                self._emit_wave(wave)

        if (
            m.boss_name
            and not self.boss_spawned
            and self.mission_time >= m.clear_time
            and not any(e.alive for e in self.enemies)
        ):
            self.boss_spawned = True
            self.boss = Boss(m.number, m.boss_name)
            self.banner = m.boss_name
            self.banner_timer = 2.5

    def _emit_wave(self, wave: WaveSpec) -> None:
        positions = self._formation_positions(wave.count, wave.formation)
        for x, y in positions:
            self.enemies.append(
                Enemy(
                    kind=wave.kind,
                    x=x,
                    y=y,
                    hp=wave.hp,
                    score=wave.score,
                    vy=wave.vy,
                    fire_cd=wave.fire_cd,
                )
            )

    def _formation_positions(self, count: int, formation: str) -> list[tuple[float, float]]:
        cx = cfg.SCREEN_W * 0.5
        if formation == "line":
            return [(cx + (i - (count - 1) / 2) * 50, -30 - i * 8) for i in range(count)]
        if formation == "v":
            return [
                (cx + (i - (count - 1) / 2) * 42, -40 - abs(i - (count - 1) / 2) * 18)
                for i in range(count)
            ]
        if formation == "row":
            return [(60 + i * ((cfg.SCREEN_W - 120) / max(1, count - 1)), -50) for i in range(count)]
        # swarm
        return [
            (
                random.uniform(40, cfg.SCREEN_W - 40),
                -30 - random.uniform(0, 80),
            )
            for _ in range(count)
        ]

    def _update_entities(self, dt: float) -> None:
        assert self.player is not None
        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if b.alive]

        for e in self.enemies:
            e.update(dt, self.player, self._spawn_bullet)
        self.enemies = [e for e in self.enemies if e.alive]

        for p in self.powerups:
            p.update(dt)
        self.powerups = [p for p in self.powerups if p.alive]

        if self.boss and self.boss.alive:
            self.boss.update(dt, self.player, self._spawn_bullet)

    def _resolve_collisions(self) -> None:
        assert self.player is not None
        # Player bullets vs enemies / boss
        for bullet in self.bullets:
            if not bullet.alive or not bullet.friendly:
                continue
            br = bullet.hitbox()
            for enemy in self.enemies:
                if enemy.alive and br.colliderect(enemy.hitbox()):
                    bullet.alive = False
                    enemy.hurt(bullet.damage)
                    if not enemy.alive:
                        self._on_enemy_killed(enemy)
                    break
            if bullet.alive and self.boss and self.boss.alive and br.colliderect(self.boss.hitbox()):
                bullet.alive = False
                self.boss.hurt(bullet.damage)
                if not self.boss.alive:
                    self.score += self.boss.score
                    self.particles.extend(
                        sprites.spawn_explosion_particles(self.boss.x, self.boss.y, 40)
                    )
                    self.banner = "BOSS DESTROYED"
                    self.banner_timer = 2.0

        # Enemy bullets vs player
        pr = self.player.hitbox()
        for bullet in self.bullets:
            if bullet.alive and not bullet.friendly and pr.colliderect(bullet.hitbox()):
                bullet.alive = False
                self.player.damage(1)

        # Ramming
        for enemy in self.enemies:
            if enemy.alive and pr.colliderect(enemy.hitbox()):
                enemy.hurt(99)
                self._on_enemy_killed(enemy)
                self.player.damage(1)
        if self.boss and self.boss.alive and pr.colliderect(self.boss.hitbox()):
            self.player.damage(1)

        # Powerups
        for pup in self.powerups:
            if pup.alive and pr.colliderect(pup.hitbox()):
                pup.alive = False
                self._apply_powerup(pup.kind)

    def _on_enemy_killed(self, enemy: Enemy) -> None:
        self.score += enemy.score
        self.particles.extend(sprites.spawn_explosion_particles(enemy.x, enemy.y, 12))
        if random.random() < 0.18:
            kind = random.choices(
                ["power", "bomb", "shield", "score"],
                weights=[40, 20, 15, 25],
            )[0]
            self.powerups.append(PowerUp(enemy.x, enemy.y, kind))

    def _apply_powerup(self, kind: str) -> None:
        assert self.player is not None
        if kind == "power":
            # Temporary fire boost via lowering fire timer + small permanent nudge feel
            self.player.fire_timer = 0
            self.score += 50
            if self.loadout.fire_level < 4 and random.random() < 0.35:
                self.loadout.fire_level += 1
            elif self.loadout.spread_level < 3 and random.random() < 0.5:
                self.loadout.spread_level += 1
        elif kind == "bomb":
            self.player.bombs += 1
        elif kind == "shield":
            self.player.hp = min(self.player.hp + 1, self.loadout.max_hp() + 1)
        elif kind == "score":
            self.score += 500

    def _update_particles(self, dt: float) -> None:
        alive: list[dict] = []
        for p in self.particles:
            p["life"] -= dt
            if p["life"] <= 0:
                continue
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= 0.92
            p["vy"] *= 0.92
            alive.append(p)
        self.particles = alive

    def _check_mission_end(self, m: MissionSpec) -> None:
        """Start victory outro when waves (and boss) are cleared."""
        if self.outro_kind is not None:
            return
        if self.player is None or not self.player.alive:
            return
        waves_done = len(self.spawned_waves) >= len(m.waves)
        enemies_clear = not any(e.alive for e in self.enemies)
        if m.boss_name:
            boss_dead = self.boss_spawned and self.boss is not None and not self.boss.alive
            if boss_dead:
                self.outro_kind = "win"
                self.outro_timer = 1.6
        elif waves_done and enemies_clear:
            # Short grace after the last wave is gone.
            last_delay = m.waves[-1].delay if m.waves else 0.0
            if self.mission_time >= last_delay + 6.0:
                self.outro_kind = "win"
                self.outro_timer = 1.0

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def _draw(self) -> None:
        if self.state == State.TITLE:
            self.menu.draw_title(self.screen, self.high_score)
            return
        if self.state == State.BRIEFING:
            m = self._current_mission()
            self.menu.draw_briefing(self.screen, m.number, m.title, m.briefing, self.score)
            return
        if self.state == State.HANGAR:
            self.menu.draw_hangar(self.screen, self.loadout, self.spendable, self.hangar_cursor)
            return

        # PLAY or RESULT (result draws over last frame)
        self.world.draw(self.screen)
        for p in self.powerups:
            p.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)
        if self.boss:
            self.boss.draw(self.screen)
        for b in self.bullets:
            b.draw(self.screen)
        if self.player:
            self.player.draw(self.screen)
        for p in self.particles:
            pg.draw.circle(self.screen, p["color"], (int(p["x"]), int(p["y"])), max(1, int(p["r"])))

        if self.player and self.state == State.PLAY:
            m = self._current_mission()
            msg = self.banner if self.banner_timer > 0 else ""
            self.hud.draw(
                self.screen,
                mission=m.number,
                title=m.title,
                score=self.score,
                hp=self.player.hp,
                max_hp=self.loadout.max_hp(),
                bombs=self.player.bombs,
                loop_cd=self.player.loop_cd,
                loop_max=cfg.PLAYER_LOOP_COOLDOWN,
                message=msg,
            )

        if self.state == State.RESULT:
            self.menu.draw_result(
                self.screen,
                victory=self.result_victory,
                score=self.score,
                mission=self._current_mission().number,
                final=self.result_final,
            )
