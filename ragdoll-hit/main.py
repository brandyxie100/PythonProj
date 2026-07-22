"""Entry point for stickman battle stage mode."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional

import pygame

import config as c
from ai_controller import EnemyAI
from duel_mode import VersusScene
from physics_world import weapon_hit
from stickman import Stickman
from terrain import EnemySpawn, LevelConfig, level_config
from weapon import Weapon


def _draw_gradient(surf: pygame.Surface) -> None:
    """Draw vertical background gradient."""
    for y in range(c.SCREEN_H):
        t = y / c.SCREEN_H
        color = tuple(
            int(c.BG_TOP[i] + (c.BG_BOTTOM[i] - c.BG_TOP[i]) * t) for i in range(3)
        )
        pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))


@dataclass(slots=True)
class KeyEdges:
    """One-frame key edge tracker for press actions."""

    attack_prev: bool = False
    jump_prev: bool = False
    cycle_prev: bool = False


class MenuScene:
    """Main menu."""

    def __init__(self) -> None:
        self._title_font = pygame.font.SysFont("Arial", 58, bold=True)
        self._btn_font = pygame.font.SysFont("Arial", 28, bold=True)
        self._hint_font = pygame.font.SysFont("Arial", 20)
        self._start_rect = pygame.Rect(c.SCREEN_W // 2 - 200, 300, 400, 60)
        self._duel_rect = pygame.Rect(c.SCREEN_W // 2 - 200, 374, 400, 60)
        self._choice: Optional[str] = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._start_rect.collidepoint(event.pos):
                self._choice = "start"
            elif self._duel_rect.collidepoint(event.pos):
                self._choice = "duel"

    def update(self) -> Optional[str]:
        choice = self._choice
        self._choice = None
        return choice

    def draw(self, surf: pygame.Surface) -> None:
        _draw_gradient(surf)
        title = self._title_font.render("RAGDOLL-HIT", True, c.UI_TEXT)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 150)))

        mouse = pygame.mouse.get_pos()
        buttons = (
            (self._start_rect, "Melee Stage Mode (Levels 1 -> 6)", (76, 126, 204), (98, 150, 235)),
            (self._duel_rect, "Versus Projectile Duel (7 Stages)", (64, 158, 96), (86, 190, 120)),
        )
        for rect, label, base, hover in buttons:
            color = hover if rect.collidepoint(mouse) else base
            pygame.draw.rect(surf, color, rect, border_radius=12)
            text = self._btn_font.render(label, True, c.WHITE)
            surf.blit(text, text.get_rect(center=rect.center))

        hints = (
            "Melee: A/D move, W double-jump, J/L arm, Space 180deg attack, E weapon",
            "Duel: W/S aim, hold Space to charge & release to throw, E cycle weapon",
            "Duel win: hit the head or turn >80% of the enemy body red",
        )
        for idx, line in enumerate(hints):
            hint = self._hint_font.render(line, True, c.UI_FAINT)
            surf.blit(hint, hint.get_rect(center=(c.SCREEN_W // 2, 470 + idx * 30)))


class StageScene:
    """Single-player stage progression across six levels."""

    def __init__(self) -> None:
        self._font = pygame.font.SysFont("Arial", 22, bold=True)
        self._small_font = pygame.font.SysFont("Arial", 17)
        self._level_no = 1
        self._coins = 0
        self._player_weapon_key = "spear"
        self._player: Stickman | None = None
        self._enemies: list[Stickman] = []
        self._enemy_ai: dict[int, EnemyAI] = {}
        self._level_data: LevelConfig | None = None
        self._transition_timer = 0.0
        self._banner = ""
        self._result: Optional[str] = None
        self._edges = KeyEdges()
        self._next_sid = 1
        self._load_level(self._level_no)

    def _alloc_sid(self) -> int:
        sid = self._next_sid
        self._next_sid += 1
        return sid

    def _create_enemy(self, spawn: EnemySpawn, pos: tuple[float, float]) -> Stickman:
        enemy = Stickman(
            sid=self._alloc_sid(),
            team="enemy",
            x=pos[0],
            y=pos[1],
            color=spawn.color,
            weapon=Weapon(spawn.weapon_name),
            max_health=c.BASE_ENEMY_HEALTH * spawn.health_multiplier,
            move_scale=spawn.speed_multiplier,
            attack_scale=0.95 + 0.3 * spawn.aggressiveness,
            facing=-1,
        )
        self._enemy_ai[enemy.sid] = EnemyAI(aggressiveness=spawn.aggressiveness)
        return enemy

    def _load_level(self, number: int) -> None:
        self._level_data = level_config(number)
        if self._player is None:
            self._player = Stickman(
                sid=self._alloc_sid(),
                team="player",
                x=self._level_data.player_spawn[0],
                y=self._level_data.player_spawn[1],
                color=c.PLAYER_BLUE,
                weapon=Weapon(self._player_weapon_key),
                max_health=c.PLAYER_MAX_HEALTH,
                move_scale=1.0,
                attack_scale=1.0,
                facing=1,
            )
        else:
            self._player.x, self._player.y = self._level_data.player_spawn
            self._player.vx = 0.0
            self._player.vy = 0.0
            self._player.health = self._player.max_health
            self._player.weapon = Weapon(self._player_weapon_key)
            self._player.grounded = False
            self._player.jumps_used = 0
        self._enemy_ai.clear()
        self._enemies = [
            self._create_enemy(spec, pos) for spec, pos in self._level_data.enemy_spawns
        ]
        self._banner = f"LEVEL {number}"
        self._transition_timer = 1.35

    def _handle_player_input(self, dt: float) -> None:
        if self._player is None:
            return
        keys = pygame.key.get_pressed()
        move_axis = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        self._player.apply_move_axis(move_axis, dt)

        arm_dir = int(keys[pygame.K_l]) - int(keys[pygame.K_j])
        off_arm_dir = int(keys[pygame.K_o]) - int(keys[pygame.K_u])
        leg_dir = int(keys[pygame.K_m]) - int(keys[pygame.K_n])
        self._player.rotate_primary_arm(arm_dir, dt)
        self._player.rotate_off_arm(off_arm_dir, dt)
        self._player.rotate_legs(leg_dir, dt)

        jump_pressed = bool(keys[pygame.K_w] or keys[pygame.K_UP])
        if jump_pressed and not self._edges.jump_prev:
            self._player.try_jump()
        self._edges.jump_prev = jump_pressed

        attack_pressed = bool(keys[pygame.K_SPACE] or keys[pygame.K_k])
        if attack_pressed and not self._edges.attack_prev:
            self._player.try_attack()
        self._edges.attack_prev = attack_pressed

        cycle_pressed = bool(keys[pygame.K_e])
        if cycle_pressed and not self._edges.cycle_prev:
            self._player.cycle_weapon()
            self._player_weapon_key = self._player.weapon.weapon_key
        self._edges.cycle_prev = cycle_pressed

    def _update_enemies(self, dt: float) -> None:
        if self._player is None or self._level_data is None:
            return
        for enemy in self._enemies:
            if not enemy.alive:
                continue
            ai = self._enemy_ai[enemy.sid]
            move, jump, attack, arm_dir, leg_dir = ai.update(
                enemy,
                self._player,
                self._level_data.arena,
                dt,
            )
            enemy.apply_move_axis(move, dt)
            enemy.rotate_primary_arm(arm_dir, dt)
            enemy.rotate_legs(leg_dir, dt * 0.6)
            if jump:
                enemy.try_jump()
            if attack:
                enemy.try_attack()

    def _resolve_combat(self) -> None:
        if self._player is None:
            return
        all_fighters = [self._player] + self._enemies
        for attacker in all_fighters:
            if not attacker.alive:
                continue
            for victim in all_fighters:
                if victim.sid == attacker.sid or not victim.alive:
                    continue
                if victim.team == attacker.team:
                    continue
                hit = weapon_hit(attacker, victim)
                if hit is None:
                    continue
                victim.take_damage(
                    hit.damage,
                    hit.knockback_x,
                    hit.knockback_y,
                )

    def update(self, dt: float) -> Optional[str]:
        if self._result is not None:
            return self._result
        if self._level_data is None or self._player is None:
            return None

        self._handle_player_input(dt)
        self._update_enemies(dt)

        # Resolve hits before physics so knockback moves fighters this frame.
        self._resolve_combat()

        self._player.update(self._level_data.arena, dt)
        for enemy in self._enemies:
            enemy.update(self._level_data.arena, dt)

        if self._player.health <= 0.0:
            self._result = "lose"
            return self._result

        self._enemies = [enemy for enemy in self._enemies if enemy.alive]
        if not self._enemies:
            self._coins += self._level_data.reward_coins
            if self._level_no >= 6:
                self._result = "win"
                return self._result
            self._level_no += 1
            self._load_level(self._level_no)

        if self._transition_timer > 0.0:
            self._transition_timer = max(0.0, self._transition_timer - dt)
        return None

    def draw(self, surf: pygame.Surface) -> None:
        if self._level_data is None or self._player is None:
            return
        _draw_gradient(surf)
        self._level_data.arena.draw(surf)

        self._player.draw(surf, is_player=True)
        for enemy in self._enemies:
            enemy.draw(surf)

        # HUD
        level_txt = self._font.render(f"LEVEL {self._level_no}/6", True, c.UI_TEXT)
        coins_txt = self._font.render(f"COINS: {self._coins}", True, c.ENEMY_YELLOW)
        hp_ratio = max(0.0, self._player.health / self._player.max_health)
        hp_w = 260
        pygame.draw.rect(surf, (42, 44, 54), pygame.Rect(20, 20, hp_w, 20), border_radius=5)
        pygame.draw.rect(
            surf,
            (60, 205, 120),
            pygame.Rect(20, 20, int(hp_w * hp_ratio), 20),
            border_radius=5,
        )
        hp_txt = self._small_font.render(
            f"HP {int(self._player.health)}/{int(self._player.max_health)}",
            True,
            c.UI_TEXT,
        )
        weapon_txt = self._small_font.render(
            f"Weapon: {self._player.weapon.stats.name}",
            True,
            c.UI_TEXT,
        )
        surf.blit(level_txt, (20, 52))
        surf.blit(coins_txt, (20, 78))
        surf.blit(hp_txt, (292, 18))
        surf.blit(weapon_txt, (292, 44))

        controls = self._small_font.render(
            "A/D move | W double jump | J/L arm | U/O off-arm | N/M legs | Space attack | E cycle weapon",
            True,
            c.UI_FAINT,
        )
        surf.blit(controls, (20, c.SCREEN_H - 28))

        if self._transition_timer > 0.0 and self._banner:
            alpha = max(0.0, min(1.0, self._transition_timer / 1.35))
            overlay = pygame.Surface((420, 88), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(160 * alpha)))
            surf.blit(overlay, (c.SCREEN_W // 2 - 210, 52))
            banner = self._font.render(self._banner, True, c.WHITE)
            surf.blit(banner, banner.get_rect(center=(c.SCREEN_W // 2, 96)))

    @property
    def coins(self) -> int:
        return self._coins


class GameOverScene:
    """Win/lose scene after stage mode run."""

    def __init__(self, won: bool, coins: int) -> None:
        self.won = won
        self.coins = coins
        self._title_font = pygame.font.SysFont("Arial", 56, bold=True)
        self._btn_font = pygame.font.SysFont("Arial", 28, bold=True)
        self._choice: Optional[str] = None
        self._again = pygame.Rect(c.SCREEN_W // 2 - 170, 340, 340, 58)
        self._menu = pygame.Rect(c.SCREEN_W // 2 - 170, 415, 340, 58)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._again.collidepoint(event.pos):
                self._choice = "again"
            elif self._menu.collidepoint(event.pos):
                self._choice = "menu"

    def update(self) -> Optional[str]:
        choice = self._choice
        self._choice = None
        return choice

    def draw(self, surf: pygame.Surface) -> None:
        _draw_gradient(surf)
        caption = "STAGE CLEARED!" if self.won else "YOU WERE DEFEATED"
        title = self._title_font.render(caption, True, c.UI_TEXT)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 200)))

        coin_text = self._btn_font.render(f"Gold Coins: {self.coins}", True, c.ENEMY_YELLOW)
        surf.blit(coin_text, coin_text.get_rect(center=(c.SCREEN_W // 2, 270)))

        mouse = pygame.mouse.get_pos()
        for rect, label in ((self._again, "Play Again"), (self._menu, "Back to Menu")):
            color = (86, 122, 186)
            if rect.collidepoint(mouse):
                color = (106, 145, 214)
            pygame.draw.rect(surf, color, rect, border_radius=11)
            text = self._btn_font.render(label, True, c.WHITE)
            surf.blit(text, text.get_rect(center=rect.center))


def main() -> None:
    """Run the game loop."""
    pygame.init()
    screen = pygame.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    pygame.display.set_caption(c.TITLE)
    clock = pygame.time.Clock()

    scene: object = MenuScene()
    last_mode = "start"
    running = True
    while running:
        dt = clock.tick(c.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif hasattr(scene, "handle_event"):
                scene.handle_event(event)

        if isinstance(scene, MenuScene):
            choice = scene.update()
            if choice == "start":
                last_mode = "start"
                scene = StageScene()
            elif choice == "duel":
                last_mode = "duel"
                scene = VersusScene()
        elif isinstance(scene, StageScene):
            result = scene.update(dt)
            if result == "win":
                scene = GameOverScene(True, scene.coins)
            elif result == "lose":
                scene = GameOverScene(False, scene.coins)
        elif isinstance(scene, VersusScene):
            result = scene.update(dt)
            if result == "win":
                scene = GameOverScene(True, scene.score)
            elif result == "lose":
                scene = GameOverScene(False, scene.score)
        elif isinstance(scene, GameOverScene):
            choice = scene.update()
            if choice == "again":
                scene = VersusScene() if last_mode == "duel" else StageScene()
            elif choice == "menu":
                scene = MenuScene()

        screen.fill((0, 0, 0))
        scene.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
