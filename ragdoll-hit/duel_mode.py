"""Versus stage-clearing projectile-duel mode.

Two stick figures stand atop pillars and lob weapons along parabolic arcs.
Players earn coins by hitting enemies (limbs 1x, torso 2x, head 3x), spend
coins on weapons plus helmets/shields, and clear a stage only after meeting its
coin goal and defeating every opponent. Stages 16–30 add a taller second pillar
with an extra foe.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

import pygame

import config as c
from duel_fighter import DuelFighter, EmbeddedWeapon
from projectiles import Projectile, spawn_projectile
from weapon_draw import draw_panel_icon

Point = tuple[float, float]

_PILLAR_TOP_Y: float = 452.0
_HIGH_PILLAR_TOP_Y: float = 300.0  # taller second pillar in latter-half stages
_PILLAR_WIDTH: int = 104
_PLAYER_X: float = 320.0  # shifted right so the figure clears the weapon panel
_ENEMY_X: float = float(c.SCREEN_W) - 180.0
_HIGH_ENEMY_X: float = float(c.SCREEN_W) - 380.0
_PROJECTILE_FLOOR: float = float(c.SCREEN_H) + 30.0
_TOTAL_STAGES: int = c.DUEL_TOTAL_STAGES

# Left-side weapon-shop panel layout (starts below HUD meters).
_PANEL_X: int = 18
_PANEL_Y: int = 214
_PANEL_BTN_W: int = 176
_PANEL_BTN_H: int = 34
_PANEL_GAP: int = 8

# Right-side defense-shop panel layout (kept high so it clears the stickman).
_DEF_PANEL_X: int = c.SCREEN_W - 186
_DEF_PANEL_Y: int = 88
_DEF_BTN_W: int = 168
_DEF_BTN_H: int = 28

# Compact integrity (energy) bars.
_INTEGRITY_BAR_W: int = 128
_INTEGRITY_BAR_H: int = 10
_HUD_LEFT_X: int = 20

# Modal popup layout (stage intro + stage clear).
_POPUP_W: int = 480
_POPUP_H: int = 360
_CONTINUE_BTN_W: int = 210
_CONTINUE_BTN_H: int = 44


@dataclass(frozen=True, slots=True)
class DuelStageSpec:
    """Difficulty and coin goal for one duel stage."""

    number: int
    enemy_weapon: str
    fire_interval: float  # seconds between enemy throws
    aim_noise: float  # radians of elevation jitter (lower = more accurate)
    coin_goal: int  # coins that must be earned this stage to pass
    dual_enemies: bool  # latter half: second foe on a taller pillar


@dataclass(frozen=True, slots=True)
class StageClearPopup:
    """Overlay shown after meeting the coin goal and defeating the enemy."""

    cleared_stage: int
    stage_earned: int
    coin_goal: int
    wallet: int
    is_final: bool


@dataclass(frozen=True, slots=True)
class StageIntroPopup:
    """Overlay shown at the start of each stage with the coin requirement."""

    stage: int
    coin_goal: int
    dual_enemies: bool


@dataclass(slots=True)
class FloatingCoinPopup:
    """A +N coin label that rises and fades above the enemy's head."""

    amount: int
    x: float
    y: float
    age: float = 0.0
    lifetime: float = 1.05


def duel_stage(number: int) -> DuelStageSpec:
    """Build an escalating duel stage for the 30-stage campaign."""
    if number < 1 or number > _TOTAL_STAGES:
        raise ValueError(f"stage {number} out of range 1..{_TOTAL_STAGES}")
    weapons = c.THROW_WEAPON_ORDER
    return DuelStageSpec(
        number=number,
        enemy_weapon=weapons[(number - 1) % len(weapons)],
        fire_interval=c.duel_fire_interval(number),
        aim_noise=c.duel_aim_noise(number),
        coin_goal=c.duel_coin_goal(number),
        dual_enemies=number >= c.DUEL_DUAL_ENEMY_FROM,
    )


def _simulate_miss_distance(
    origin: Point,
    facing: int,
    elevation: float,
    power: float,
    speed_scale: float,
    target: Point,
) -> float:
    """Return the closest a trajectory passes to ``target`` (for AI aiming)."""
    speed = power * speed_scale
    x, y = origin
    vx = facing * math.cos(elevation) * speed
    vy = -math.sin(elevation) * speed
    dt = 1.0 / 120.0
    best = float("inf")
    for _ in range(720):
        vy += c.PROJECTILE_GRAVITY * dt
        x += vx * dt
        y += vy * dt
        best = min(best, math.hypot(x - target[0], y - target[1]))
        if y >= _PROJECTILE_FLOOR or x < -80 or x > c.SCREEN_W + 80:
            break
    return best


def _solve_aim(
    origin: Point,
    facing: int,
    target: Point,
    speed_scale: float,
) -> tuple[float, float]:
    """Search elevation/power pairs for the best firing solution."""
    best_elev = 0.7
    best_power = c.THROW_POWER_MAX
    best_dist = float("inf")
    for ei in range(20):
        elev = c.AIM_MIN_ELEV + (c.AIM_MAX_ELEV - c.AIM_MIN_ELEV) * ei / 19.0
        for pi in range(11):
            power = c.THROW_POWER_MIN + (
                c.THROW_POWER_MAX - c.THROW_POWER_MIN
            ) * pi / 10.0
            dist = _simulate_miss_distance(
                origin, facing, elev, power, speed_scale, target
            )
            if dist < best_dist:
                best_dist = dist
                best_elev = elev
                best_power = power
    return best_elev, best_power


class DuelAI:
    """Aims and fires the enemy fighter with stage-scaled accuracy."""

    def __init__(self, spec: DuelStageSpec) -> None:
        """Store the stage spec and stagger the first shot."""
        self._spec = spec
        self._fire_timer = 1.2

    def update(
        self,
        me: DuelFighter,
        target: DuelFighter,
        dt: float,
    ) -> Optional[Projectile]:
        """Aim toward the target and occasionally fire a projectile."""
        if me.dead or target.dead:
            return None

        stats = c.THROW_WEAPONS[me.weapon_key]
        # Aim toward the torso center so most hits land on the body mass.
        aim_point = target.neck
        aim_elev, power = _solve_aim(
            me.muzzle_point(), me.facing, aim_point, stats.speed_scale
        )
        # Smoothly track the computed elevation so the arm visibly follows aim.
        me.aim_elev += max(-0.05, min(0.05, aim_elev - me.aim_elev))

        self._fire_timer -= dt
        if self._fire_timer > 0.0 or not me.can_throw():
            return None

        self._fire_timer = self._spec.fire_interval
        noisy_elev = aim_elev + random.uniform(-self._spec.aim_noise, self._spec.aim_noise)
        me.aim_elev = max(c.AIM_MIN_ELEV, min(c.AIM_MAX_ELEV, noisy_elev))
        me.throw_cooldown = c.THROW_COOLDOWN
        me.start_throw_animation()
        return spawn_projectile(
            me.weapon_key, me.team, me.muzzle_point(), me.aim_elev, me.facing, power
        )


class VersusScene:
    """Stage-clearing duel with hit coins, a weapon shop, and coin goals."""

    def __init__(self) -> None:
        """Set up fonts, wallet, owned starter weapon, and stage 1."""
        self._font = pygame.font.SysFont("Arial", 22, bold=True)
        self._title = pygame.font.SysFont("Arial", 34, bold=True)
        self._small = pygame.font.SysFont("Arial", 17)
        self._tiny = pygame.font.SysFont("Arial", 14)
        self._stage_no = 1
        self._coins = 0  # spendable wallet
        self._stage_earned = 0  # coins earned toward the current stage goal
        self._owned_weapons: set[str] = {c.DUEL_STARTER_WEAPON}
        self._owned_helmets: set[str] = set()
        self._owned_shields: set[str] = set()
        self._result: Optional[str] = None
        self._space_prev = False
        self._prev_enemy_weapon = ""
        self._clear_popup: Optional[StageClearPopup] = None
        self._intro_popup: Optional[StageIntroPopup] = None
        self._coin_popups: list[FloatingCoinPopup] = []
        self._display_coins = 0.0  # smoothly counts up toward wallet
        self._display_earned = 0.0  # smoothly counts up toward stage goal progress
        self._need_more_banner = 0.0

        self._player = DuelFighter(
            team="player",
            x=_PLAYER_X,
            ground_y=_PILLAR_TOP_Y,
            facing=1,
            weapon_key=c.DUEL_STARTER_WEAPON,
        )
        self._projectiles: list[Projectile] = []
        self._enemies: list[DuelFighter] = []
        self._ais: list[DuelAI] = []
        self._load_stage(self._stage_no, show_intro=True)

    # -- stage lifecycle ----------------------------------------------------
    def _pick_enemy_weapon(self) -> str:
        """Choose a random weapon that differs from the last enemy's weapon."""
        options = [w for w in c.THROW_WEAPON_ORDER if w != self._prev_enemy_weapon]
        weapon = random.choice(options)
        self._prev_enemy_weapon = weapon
        return weapon

    def _assign_enemy_gear(self, fighter: DuelFighter, stage: int) -> None:
        """Give late-stage enemies helmets/shields for extra toughness."""
        if stage >= 22 and random.random() < 0.55:
            fighter.equip_helmet(random.choice(("leather_helm", "iron_helm")))
        elif stage >= 12 and random.random() < 0.45:
            fighter.equip_helmet("leather_helm")
        if stage >= 24 and random.random() < 0.5:
            fighter.equip_shield(random.choice(("wood_shield", "iron_shield")))
        elif stage >= 14 and random.random() < 0.4:
            fighter.equip_shield("wood_shield")

    def _spawn_enemies(self) -> None:
        """Spawn the stage's main foe (and a high-pillar foe when dual)."""
        spec = duel_stage(self._stage_no)
        self._enemies = []
        self._ais = []
        self._projectiles.clear()

        main = DuelFighter(
            team="enemy",
            x=_ENEMY_X,
            ground_y=_PILLAR_TOP_Y,
            facing=-1,
            weapon_key=self._pick_enemy_weapon(),
        )
        self._assign_enemy_gear(main, self._stage_no)
        self._enemies.append(main)
        self._ais.append(DuelAI(spec))

        if spec.dual_enemies:
            high = DuelFighter(
                team="enemy",
                x=_HIGH_ENEMY_X,
                ground_y=_HIGH_PILLAR_TOP_Y,
                facing=-1,
                weapon_key=self._pick_enemy_weapon(),
            )
            self._assign_enemy_gear(high, self._stage_no)
            self._enemies.append(high)
            # High foe fires a bit slower / noisier so both aren't perfect.
            high_spec = DuelStageSpec(
                number=spec.number,
                enemy_weapon=high.weapon_key,
                fire_interval=spec.fire_interval * 1.15,
                aim_noise=spec.aim_noise * 1.25,
                coin_goal=spec.coin_goal,
                dual_enemies=True,
            )
            self._ais.append(DuelAI(high_spec))

    @property
    def _enemy(self) -> DuelFighter:
        """Primary (lower-pillar) enemy — kept for older tests/helpers."""
        return self._enemies[0]

    def _living_enemies(self) -> list[DuelFighter]:
        """Enemies that are still fighting."""
        return [e for e in self._enemies if not e.dead]

    def _all_enemies_dead(self) -> bool:
        """True when every spawned foe has been defeated."""
        return bool(self._enemies) and all(e.dead for e in self._enemies)

    def _load_stage(self, number: int, *, show_intro: bool = True) -> None:
        """Start a stage: reset stage earnings, heal the player, spawn foes."""
        self._stage_no = number
        self._stage_earned = 0
        self._display_earned = 0.0
        self._coin_popups.clear()
        self._spawn_enemies()
        # Preserve equipped gear; refresh durability via reset_health.
        self._player.reset_health()
        if self._player.weapon_key not in self._owned_weapons:
            self._player.weapon_key = c.DUEL_STARTER_WEAPON
        self._clear_popup = None
        self._need_more_banner = 0.0
        self._space_prev = True  # ignore held Space from dismissing popups
        spec = duel_stage(number)
        if show_intro:
            self._intro_popup = StageIntroPopup(
                stage=number,
                coin_goal=spec.coin_goal,
                dual_enemies=spec.dual_enemies,
            )
        else:
            self._intro_popup = None

    def _award_hit_coins(self, segment_name: str, target: DuelFighter) -> int:
        """Add hit payout and spawn a floating +N above the struck foe."""
        amount = c.hit_coins_for_segment(segment_name)
        self._coins += amount
        self._stage_earned += amount
        head_x, head_y = target.head_center
        stack = len(self._coin_popups) * 10.0
        self._coin_popups.append(
            FloatingCoinPopup(
                amount=amount,
                x=head_x,
                y=head_y - c.HEAD_R - 8.0 - stack,
            )
        )
        return amount

    def _update_coin_popups(self, dt: float) -> None:
        """Advance floating labels and ease the HUD coin counters upward."""
        for popup in self._coin_popups:
            popup.age += dt
            popup.y -= 52.0 * dt  # rise above the head
        self._coin_popups = [p for p in self._coin_popups if p.age < p.lifetime]

        # Count the HUD numbers up (and snap down immediately after spending).
        coin_speed = 70.0 * dt
        if self._display_coins < self._coins:
            self._display_coins = min(float(self._coins), self._display_coins + coin_speed)
        else:
            self._display_coins = float(self._coins)

        earned_speed = 70.0 * dt
        if self._display_earned < self._stage_earned:
            self._display_earned = min(
                float(self._stage_earned), self._display_earned + earned_speed
            )
        else:
            self._display_earned = float(self._stage_earned)

    def _try_buy_weapon(self, key: str) -> bool:
        """Purchase ``key`` if locked and affordable; equip it when owned."""
        stats = c.THROW_WEAPONS[key]
        if key in self._owned_weapons:
            self._player.weapon_key = key
            self._player.weapon_swap_timer = c.DUEL_WEAPON_SWAP_TIME
            return True
        if self._coins < stats.price:
            return False
        self._coins -= stats.price
        self._owned_weapons.add(key)
        self._player.weapon_key = key
        self._player.weapon_swap_timer = c.DUEL_WEAPON_SWAP_TIME
        return True

    def _try_buy_helmet(self, key: str) -> bool:
        """Purchase or equip a helmet from the defense shop."""
        stats = c.HELMETS[key]
        if key in self._owned_helmets:
            self._player.equip_helmet(key)
            return True
        if self._coins < stats.price:
            return False
        self._coins -= stats.price
        self._owned_helmets.add(key)
        self._player.equip_helmet(key)
        return True

    def _try_buy_shield(self, key: str) -> bool:
        """Purchase or equip a shield from the defense shop."""
        stats = c.SHIELDS[key]
        if key in self._owned_shields:
            self._player.equip_shield(key)
            return True
        if self._coins < stats.price:
            return False
        self._coins -= stats.price
        self._owned_shields.add(key)
        self._player.equip_shield(key)
        return True

    def _cycle_owned_weapon(self) -> None:
        """Cycle only through weapons the player has unlocked."""
        owned = [k for k in c.THROW_WEAPON_ORDER if k in self._owned_weapons]
        if not owned:
            return
        if self._player.weapon_key not in owned:
            self._player.weapon_key = owned[0]
            return
        idx = owned.index(self._player.weapon_key)
        self._player.weapon_key = owned[(idx + 1) % len(owned)]
        self._player.weapon_swap_timer = c.DUEL_WEAPON_SWAP_TIME

    def _on_enemies_defeated(self) -> None:
        """Pass if the coin goal is met; otherwise respawn the stage foes."""
        goal = duel_stage(self._stage_no).coin_goal
        self._projectiles.clear()
        self._player.charging = False
        if self._stage_earned >= goal:
            self._clear_popup = StageClearPopup(
                cleared_stage=self._stage_no,
                stage_earned=self._stage_earned,
                coin_goal=goal,
                wallet=self._coins,
                is_final=self._stage_no >= _TOTAL_STAGES,
            )
            return
        self._spawn_enemies()
        self._need_more_banner = 2.4

    def _dismiss_intro_popup(self) -> None:
        """Close the stage-requirement window and begin combat."""
        self._intro_popup = None
        self._space_prev = True

    def _dismiss_stage_clear_popup(self) -> Optional[str]:
        """Advance to the next stage, or finish the run on the final stage."""
        popup = self._clear_popup
        if popup is None:
            return None
        if popup.is_final:
            self._result = "win"
            self._clear_popup = None
            return self._result
        self._load_stage(self._stage_no + 1, show_intro=True)
        return None

    @staticmethod
    def _popup_rect() -> pygame.Rect:
        """Centered modal panel for intro / clear overlays."""
        return pygame.Rect(
            (c.SCREEN_W - _POPUP_W) // 2,
            (c.SCREEN_H - _POPUP_H) // 2 - 10,
            _POPUP_W,
            _POPUP_H,
        )

    @staticmethod
    def _continue_button_rect() -> pygame.Rect:
        """Continue button inside a modal popup."""
        panel = VersusScene._popup_rect()
        return pygame.Rect(
            panel.centerx - _CONTINUE_BTN_W // 2,
            panel.bottom - 64,
            _CONTINUE_BTN_W,
            _CONTINUE_BTN_H,
        )

    @property
    def _modal_open(self) -> bool:
        """True while an intro or clear popup freezes combat."""
        return self._intro_popup is not None or self._clear_popup is not None

    # -- input --------------------------------------------------------------
    @staticmethod
    def _weapon_buttons() -> list[tuple[pygame.Rect, str]]:
        """Return clickable shop rects paired with their weapon key."""
        buttons: list[tuple[pygame.Rect, str]] = []
        for i, key in enumerate(c.THROW_WEAPON_ORDER):
            rect = pygame.Rect(
                _PANEL_X,
                _PANEL_Y + i * (_PANEL_BTN_H + _PANEL_GAP),
                _PANEL_BTN_W,
                _PANEL_BTN_H,
            )
            buttons.append((rect, key))
        return buttons

    @staticmethod
    def _defense_buttons() -> list[tuple[pygame.Rect, str, str]]:
        """Return defense-shop rects as (rect, kind, key)."""
        buttons: list[tuple[pygame.Rect, str, str]] = []
        row = 0
        for key in c.HELMET_ORDER:
            rect = pygame.Rect(
                _DEF_PANEL_X,
                _DEF_PANEL_Y + row * (_DEF_BTN_H + 4),
                _DEF_BTN_W,
                _DEF_BTN_H,
            )
            buttons.append((rect, "helmet", key))
            row += 1
        row += 1  # small gap between helmets and shields
        for key in c.SHIELD_ORDER:
            rect = pygame.Rect(
                _DEF_PANEL_X,
                _DEF_PANEL_Y + row * (_DEF_BTN_H + 4),
                _DEF_BTN_W,
                _DEF_BTN_H,
            )
            buttons.append((rect, "shield", key))
            row += 1
        return buttons

    @property
    def _defense_shop_unlocked(self) -> bool:
        """True once the campaign reaches the defense-shop unlock stage."""
        return self._stage_no >= c.DUEL_DEFENSE_SHOP_FROM

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle shop clicks and intro / clear popup dismissal."""
        if self._intro_popup is not None:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_SPACE,
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                self._dismiss_intro_popup()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._continue_button_rect().collidepoint(event.pos):
                    self._dismiss_intro_popup()
            return

        if self._clear_popup is not None:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_SPACE,
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                self._dismiss_stage_clear_popup()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._continue_button_rect().collidepoint(event.pos):
                    self._dismiss_stage_clear_popup()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self._cycle_owned_weapon()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, key in self._weapon_buttons():
                if rect.collidepoint(event.pos):
                    self._try_buy_weapon(key)
                    return
            if self._defense_shop_unlocked:
                for rect, kind, key in self._defense_buttons():
                    if rect.collidepoint(event.pos):
                        if kind == "helmet":
                            self._try_buy_helmet(key)
                        else:
                            self._try_buy_shield(key)
                        return

    def _handle_player_input(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        move_axis = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        self._player.apply_move_axis(move_axis, dt)

        aim_dir = int(keys[pygame.K_w] or keys[pygame.K_UP]) - int(
            keys[pygame.K_s] or keys[pygame.K_DOWN]
        )
        self._player.rotate_aim(aim_dir, dt)

        space = bool(keys[pygame.K_SPACE])
        if space and not self._space_prev:
            self._player.start_charge()
        if not space and self._space_prev:
            power = self._player.release_charge()
            if power is not None:
                self._projectiles.append(
                    spawn_projectile(
                        self._player.weapon_key,
                        "player",
                        self._player.muzzle_point(),
                        self._player.aim_elev,
                        self._player.facing,
                        power,
                    )
                )
        self._space_prev = space

    # -- update -------------------------------------------------------------
    def update(self, dt: float) -> Optional[str]:
        """Advance one frame; returns 'win'/'lose' when the run ends."""
        if self._result is not None:
            return self._result

        if self._need_more_banner > 0.0:
            self._need_more_banner = max(0.0, self._need_more_banner - dt)
        self._update_coin_popups(dt)

        # Freeze combat while a modal window is open.
        if self._modal_open:
            return None

        self._handle_player_input(dt)
        self._player.update(dt)
        for enemy, ai in zip(self._enemies, self._ais):
            enemy.update(dt)
            if enemy.dead:
                continue
            shot = ai.update(enemy, self._player, dt)
            if shot is not None:
                self._projectiles.append(shot)

        self._advance_projectiles(dt)

        if self._player.dead:
            self._result = "lose"
            return self._result

        if self._all_enemies_dead() and self._clear_popup is None:
            self._on_enemies_defeated()
            return None

        return None

    def _advance_projectiles(self, dt: float) -> None:
        for proj in self._projectiles:
            if proj.dead:
                continue
            prev_tip = proj.tip()
            proj.update(dt, _PROJECTILE_FLOOR)
            if proj.team == "player":
                hit_target, hit = self._first_enemy_hit(prev_tip, proj.tip())
            else:
                hit_target, hit = None, None
                if not self._player.dead:
                    hit = self._swept_hit(self._player, prev_tip, proj.tip())
                    if hit is not None:
                        hit_target = self._player
            if hit_target is None or hit is None:
                continue
            segment, point = hit
            hit_target.apply_hit(
                segment,
                proj.stats.damage,
                EmbeddedWeapon(proj.weapon_key, point[0], point[1], proj.angle),
            )
            if proj.team == "player":
                self._award_hit_coins(segment, hit_target)
                if not hit_target.dead:
                    hit_target.apply_safe_knockback()
            proj.dead = True
        self._projectiles = [p for p in self._projectiles if not p.dead]

    def _first_enemy_hit(
        self,
        start: Point,
        end: Point,
    ) -> tuple[Optional[DuelFighter], Optional[tuple[str, Point]]]:
        """Return the living enemy struck first along a projectile path."""
        span = math.hypot(end[0] - start[0], end[1] - start[1])
        steps = max(1, int(span / 5.0))
        best_t: float | None = None
        best: tuple[DuelFighter, tuple[str, Point]] | None = None
        for enemy in self._living_enemies():
            for i in range(steps + 1):
                t = i / steps
                point = (
                    start[0] + (end[0] - start[0]) * t,
                    start[1] + (end[1] - start[1]) * t,
                )
                segment = enemy.hit_test(point)
                if segment is None:
                    continue
                if best_t is None or t < best_t:
                    best_t = t
                    best = (enemy, (segment, point))
                break
        if best is None:
            return None, None
        return best[0], best[1]

    @staticmethod
    def _swept_hit(
        target: DuelFighter,
        start: Point,
        end: Point,
    ) -> Optional[tuple[str, Point]]:
        """Sample points from ``start`` to ``end`` and return the first body hit."""
        span = math.hypot(end[0] - start[0], end[1] - start[1])
        steps = max(1, int(span / 5.0))
        for i in range(steps + 1):
            t = i / steps
            point = (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t)
            segment = target.hit_test(point)
            if segment is not None:
                return segment, point
        return None

    # -- rendering ----------------------------------------------------------
    def draw(self, surf: pygame.Surface) -> None:
        """Render background, pillars, fighters, projectiles, and HUD."""
        self._draw_background(surf)
        self._draw_pillar(surf, _PLAYER_X, _PILLAR_TOP_Y)
        self._draw_pillar(surf, _ENEMY_X, _PILLAR_TOP_Y)
        if duel_stage(self._stage_no).dual_enemies or any(
            abs(e.pillar_top_y - _HIGH_PILLAR_TOP_Y) < 1.0 for e in self._enemies
        ):
            self._draw_pillar(surf, _HIGH_ENEMY_X, _HIGH_PILLAR_TOP_Y)

        self._player.draw(surf)
        for enemy in self._enemies:
            enemy.draw(surf)
        for proj in self._projectiles:
            proj.draw(surf)
        self._draw_coin_popups(surf)

        self._draw_hud(surf)
        if self._intro_popup is not None:
            self._draw_stage_intro_popup(surf, self._intro_popup)
        elif self._clear_popup is not None:
            self._draw_stage_clear_popup(surf, self._clear_popup)

    def _draw_background(self, surf: pygame.Surface) -> None:
        for y in range(c.SCREEN_H):
            t = y / c.SCREEN_H
            color = tuple(
                int(c.DUEL_BG_TOP[i] + (c.DUEL_BG_BOTTOM[i] - c.DUEL_BG_TOP[i]) * t)
                for i in range(3)
            )
            pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))

    def _draw_pillar(self, surf: pygame.Surface, x: float, top_y: float) -> None:
        left = int(x - _PILLAR_WIDTH / 2)
        pygame.draw.rect(
            surf,
            c.DUEL_PILLAR_COLOR,
            pygame.Rect(left, int(top_y), _PILLAR_WIDTH, c.SCREEN_H - int(top_y)),
        )
        pygame.draw.rect(
            surf,
            c.DUEL_PILLAR_TOP,
            pygame.Rect(left - 6, int(top_y) - 10, _PILLAR_WIDTH + 12, 14),
            border_radius=4,
        )

    def _draw_coin_popups(self, surf: pygame.Surface) -> None:
        """Draw rising +N labels anchored above the enemy's head."""
        for popup in self._coin_popups:
            t = popup.age / popup.lifetime
            # Pop in quickly, then fade out while rising.
            if t < 0.15:
                scale = 0.75 + (t / 0.15) * 0.45
                alpha = 255
            else:
                scale = 1.2 - (t - 0.15) * 0.25
                alpha = int(255 * (1.0 - (t - 0.15) / 0.85))
            alpha = max(0, min(255, alpha))
            label = self._font.render(f"+{popup.amount}", True, (255, 220, 50))
            # Soft dark outline so the gold number reads on the green sky.
            outline = self._font.render(f"+{popup.amount}", True, (40, 30, 10))
            w = max(1, int(label.get_width() * scale))
            h = max(1, int(label.get_height() * scale))
            scaled = pygame.transform.smoothscale(label, (w, h))
            scaled_outline = pygame.transform.smoothscale(outline, (w, h))
            scaled.set_alpha(alpha)
            scaled_outline.set_alpha(alpha)
            rect = scaled.get_rect(center=(int(popup.x), int(popup.y)))
            surf.blit(scaled_outline, rect.move(1, 1))
            surf.blit(scaled, rect)

    def _draw_hud(self, surf: pygame.Surface) -> None:
        """Draw left/right HUD with clear vertical spacing (no label clashes)."""
        goal = duel_stage(self._stage_no).coin_goal
        shown_coins = int(self._display_coins)
        shown_earned = int(self._display_earned)
        x = _HUD_LEFT_X

        stage_txt = self._font.render(
            f"STAGE {self._stage_no}/{_TOTAL_STAGES}", True, (30, 40, 30)
        )
        wallet_txt = self._font.render(f"COINS: {shown_coins}", True, (120, 80, 20))
        progress = min(1.0, shown_earned / max(1, goal))
        goal_txt = self._font.render(
            f"GOAL: {shown_earned}/{goal}",
            True,
            (28, 110, 50) if shown_earned >= goal else (30, 40, 30),
        )
        surf.blit(stage_txt, (x, 12))
        surf.blit(wallet_txt, (x, 36))
        surf.blit(goal_txt, (x, 60))

        # Goal progress (narrow bar under GOAL text).
        goal_bar = pygame.Rect(x, 86, 200, 8)
        pygame.draw.rect(surf, (40, 60, 40), goal_bar, border_radius=3)
        pygame.draw.rect(
            surf,
            (240, 180, 40),
            pygame.Rect(x, 86, int(200 * progress), 8),
            border_radius=3,
        )

        # Player integrity block: label above bar.
        self._draw_integrity(surf, x, 102, "YOU", self._player)

        # Enemy bars top-right (compact stack).
        ey = 14
        for idx, enemy in enumerate(self._enemies):
            label = "ENEMY" if len(self._enemies) == 1 else f"E{idx + 1}"
            self._draw_integrity(surf, c.SCREEN_W - 148, ey, label, enemy)
            ey += 30

        gear_bits: list[str] = []
        if self._player.helmet_key:
            gear_bits.append(c.HELMETS[self._player.helmet_key].name)
        if self._player.shield_key:
            gear_bits.append(c.SHIELDS[self._player.shield_key].name)
        gear_label = " + ".join(gear_bits) if gear_bits else "none"
        weapon_txt = self._small.render(
            f"Weapon: {c.THROW_WEAPONS[self._player.weapon_key].name}  |  Gear: {gear_label}",
            True,
            (30, 40, 30),
        )
        surf.blit(weapon_txt, (x, 132))

        # Power meter sits above the weapon shop with a clear gap.
        meter = pygame.Rect(x, 156, 200, 12)
        pygame.draw.rect(surf, (40, 60, 40), meter, border_radius=3)
        frac = (self._player.power - c.THROW_POWER_MIN) / (
            c.THROW_POWER_MAX - c.THROW_POWER_MIN
        )
        frac = max(0.0, min(1.0, frac))
        pygame.draw.rect(
            surf,
            (240, 180, 40),
            pygame.Rect(x, 156, int(200 * frac), 12),
            border_radius=3,
        )
        power_label = self._small.render("POWER (hold Space)", True, (30, 40, 30))
        surf.blit(power_label, (x + 210, 154))

        self._draw_weapon_panel(surf)
        if self._defense_shop_unlocked:
            self._draw_defense_panel(surf)

        if self._defense_shop_unlocked:
            controls = self._small.render(
                "A/D dodge  |  W/S aim  |  Space throw  |  Left: weapons  |  Right: helmets/shields"
                "  |  Don't fall off!",
                True,
                (32, 44, 32),
            )
        else:
            controls = self._small.render(
                "A/D dodge  |  W/S aim  |  Space throw  |  Left: weapons"
                f"  |  Defense shop unlocks at stage {c.DUEL_DEFENSE_SHOP_FROM}",
                True,
                (32, 44, 32),
            )
        surf.blit(controls, (x, c.SCREEN_H - 28))

        if self._need_more_banner > 0.0:
            remaining = max(0, goal - self._stage_earned)
            banner = self._font.render(
                f"Need {remaining} more coins — foes respawned!",
                True,
                (140, 40, 30),
            )
            surf.blit(banner, banner.get_rect(center=(c.SCREEN_W // 2, 42)))

    def _draw_stage_intro_popup(self, surf: pygame.Surface, popup: StageIntroPopup) -> None:
        """Show the coin requirement and how to earn / spend before combat."""
        dim = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        dim.fill((12, 18, 12, 160))
        surf.blit(dim, (0, 0))

        panel = self._popup_rect()
        pygame.draw.rect(surf, (236, 244, 228), panel, border_radius=14)
        pygame.draw.rect(surf, (42, 78, 46), panel, 3, border_radius=14)

        title = self._title.render(f"STAGE {popup.stage}", True, (28, 92, 40))
        surf.blit(title, title.get_rect(centerx=panel.centerx, y=panel.y + 18))

        goal = self._font.render(
            f"Earn {popup.coin_goal} coins to pass", True, (140, 90, 20)
        )
        surf.blit(goal, goal.get_rect(centerx=panel.centerx, y=panel.y + 68))

        lines = [
            f"Arms / legs  +{c.HIT_COINS_LIMB}  |  Body +{c.HIT_COINS_TORSO}  |  Head +{c.HIT_COINS_HEAD}",
            "Left shop: weapons",
            "Pass = coin goal met + all enemies defeated.",
        ]
        if popup.stage >= c.DUEL_DEFENSE_SHOP_FROM:
            lines.insert(
                2,
                "Right shop: helmets & shields (blunt head / body hits).",
            )
        else:
            lines.insert(
                2,
                f"Helmets & shields unlock from stage {c.DUEL_DEFENSE_SHOP_FROM}.",
            )
        if popup.dual_enemies:
            lines.insert(
                0,
                "DUAL FOES: a second enemy stands on a taller pillar!",
            )
        y = panel.y + 108
        for line in lines:
            text = self._small.render(line, True, (40, 55, 40))
            surf.blit(text, text.get_rect(centerx=panel.centerx, y=y))
            y += 28

        self._draw_continue_button(surf, "Start Stage")

    def _draw_stage_clear_popup(self, surf: pygame.Surface, popup: StageClearPopup) -> None:
        """Draw a modal window celebrating the stage win and showing scores."""
        dim = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        dim.fill((12, 18, 12, 150))
        surf.blit(dim, (0, 0))

        panel = self._popup_rect()
        pygame.draw.rect(surf, (236, 244, 228), panel, border_radius=14)
        pygame.draw.rect(surf, (42, 78, 46), panel, 3, border_radius=14)

        if popup.is_final:
            title = self._title.render("YOU WIN!", True, (28, 92, 40))
            subtitle = self._font.render(
                f"All {_TOTAL_STAGES} stages cleared", True, (50, 70, 50)
            )
            button_label = "Finish"
        else:
            title = self._title.render("STAGE CLEARED!", True, (28, 92, 40))
            subtitle = self._font.render(
                f"Stage {popup.cleared_stage} of {_TOTAL_STAGES}",
                True,
                (50, 70, 50),
            )
            button_label = "Next Stage"

        surf.blit(title, title.get_rect(centerx=panel.centerx, y=panel.y + 28))
        surf.blit(subtitle, subtitle.get_rect(centerx=panel.centerx, y=panel.y + 78))

        earned_txt = self._font.render(
            f"Earned {popup.stage_earned} / {popup.coin_goal} goal coins",
            True,
            (140, 90, 20),
        )
        wallet_txt = self._font.render(
            f"Wallet: {popup.wallet} coins", True, (40, 55, 40)
        )
        surf.blit(earned_txt, earned_txt.get_rect(centerx=panel.centerx, y=panel.y + 124))
        surf.blit(wallet_txt, wallet_txt.get_rect(centerx=panel.centerx, y=panel.y + 158))

        self._draw_continue_button(surf, button_label)

    def _draw_continue_button(self, surf: pygame.Surface, label: str) -> None:
        """Shared Continue / Start button for modal popups."""
        btn = self._continue_button_rect()
        hovered = btn.collidepoint(pygame.mouse.get_pos())
        fill = (92, 176, 110) if hovered else (64, 148, 86)
        pygame.draw.rect(surf, fill, btn, border_radius=8)
        pygame.draw.rect(surf, (28, 70, 40), btn, 2, border_radius=8)
        text = self._font.render(label, True, (248, 252, 246))
        surf.blit(text, text.get_rect(center=btn.center))
        hint = self._small.render(
            "Press Space / Enter or click to continue", True, (70, 90, 70)
        )
        panel = self._popup_rect()
        surf.blit(hint, hint.get_rect(centerx=panel.centerx, y=panel.bottom - 22))

    def _draw_weapon_panel(self, surf: pygame.Surface) -> None:
        """Draw the left-side weapon shop (buy locked / equip owned)."""
        title = self._small.render("WEAPON SHOP", True, (28, 40, 28))
        surf.blit(title, (_PANEL_X, _PANEL_Y - 22))
        mouse = pygame.mouse.get_pos()
        for rect, key in self._weapon_buttons():
            stats = c.THROW_WEAPONS[key]
            owned = key in self._owned_weapons
            selected = key == self._player.weapon_key
            hovered = rect.collidepoint(mouse)
            can_afford = self._coins >= stats.price

            if selected:
                fill = (250, 214, 96)
            elif owned and hovered:
                fill = (150, 196, 128)
            elif owned:
                fill = (56, 96, 62)
            elif can_afford and hovered:
                fill = (120, 160, 90)
            elif can_afford:
                fill = (70, 100, 72)
            else:
                fill = (48, 58, 50)

            pygame.draw.rect(surf, fill, rect, border_radius=7)
            pygame.draw.rect(surf, (30, 46, 32), rect, 2, border_radius=7)

            icon_center = (rect.x + 22, rect.centery)
            draw_panel_icon(surf, key, icon_center, size=24.0)

            text_color = (40, 34, 12) if selected else (238, 244, 236)
            if not owned and not can_afford:
                text_color = (170, 176, 168)
            name = self._small.render(stats.name, True, text_color)
            surf.blit(name, (rect.x + 42, rect.y + 2))

            if owned:
                detail = "OWNED" if not selected else "EQUIPPED"
                detail_color = (40, 34, 12) if selected else (200, 230, 200)
            else:
                detail = f"{stats.price}c  dmg {stats.damage:.2f}"
                detail_color = (255, 230, 120) if can_afford else (160, 160, 150)
            meta = self._tiny.render(detail, True, detail_color)
            surf.blit(meta, (rect.x + 42, rect.y + 17))

    def _draw_defense_panel(self, surf: pygame.Surface) -> None:
        """Draw the right-side helmet / shield shop."""
        title = self._small.render("DEFENSE SHOP", True, (28, 40, 28))
        surf.blit(title, (_DEF_PANEL_X, _DEF_PANEL_Y - 22))
        mouse = pygame.mouse.get_pos()
        for rect, kind, key in self._defense_buttons():
            stats = c.HELMETS[key] if kind == "helmet" else c.SHIELDS[key]
            owned = key in (
                self._owned_helmets if kind == "helmet" else self._owned_shields
            )
            selected = (
                key == self._player.helmet_key
                if kind == "helmet"
                else key == self._player.shield_key
            )
            hovered = rect.collidepoint(mouse)
            can_afford = self._coins >= stats.price

            if selected:
                fill = (250, 214, 96)
            elif owned and hovered:
                fill = (150, 196, 128)
            elif owned:
                fill = (56, 96, 62)
            elif can_afford and hovered:
                fill = (120, 160, 90)
            elif can_afford:
                fill = (70, 100, 72)
            else:
                fill = (48, 58, 50)

            pygame.draw.rect(surf, fill, rect, border_radius=7)
            pygame.draw.rect(surf, (30, 46, 32), rect, 2, border_radius=7)
            pygame.draw.circle(surf, stats.color, (rect.x + 18, rect.centery), 8)

            text_color = (40, 34, 12) if selected else (238, 244, 236)
            if not owned and not can_afford:
                text_color = (170, 176, 168)
            name = self._tiny.render(stats.name, True, text_color)
            surf.blit(name, (rect.x + 34, rect.y + 2))

            if owned:
                hp = (
                    self._player.helmet_hp
                    if kind == "helmet" and selected
                    else self._player.shield_hp
                    if kind == "shield" and selected
                    else stats.durability
                )
                detail = f"EQUIPPED {hp}/{stats.durability}" if selected else "OWNED"
                detail_color = (40, 34, 12) if selected else (200, 230, 200)
            else:
                detail = f"{stats.price}c  x{stats.damage_factor:.2f} dmg"
                detail_color = (255, 230, 120) if can_afford else (160, 160, 150)
            meta = self._tiny.render(detail, True, detail_color)
            surf.blit(meta, (rect.x + 34, rect.y + 14))

    def _draw_integrity(
        self,
        surf: pygame.Surface,
        x: int,
        y: int,
        label: str,
        fighter: DuelFighter,
    ) -> None:
        """Draw a compact integrity block: label on top, bar directly beneath.

        ``y`` is the top of the label so callers can stack blocks without overlap.
        """
        text = self._tiny.render(label, True, (30, 40, 30))
        surf.blit(text, (x, y))
        bar_y = y + 14
        ratio = max(0.0, 1.0 - fighter.body_red_ratio() / c.BODY_RED_DEATH_RATIO)
        bar = pygame.Rect(x, bar_y, _INTEGRITY_BAR_W, _INTEGRITY_BAR_H)
        pygame.draw.rect(surf, (40, 60, 40), bar, border_radius=3)
        pygame.draw.rect(
            surf,
            (70, 200, 90),
            pygame.Rect(x, bar_y, int(_INTEGRITY_BAR_W * ratio), _INTEGRITY_BAR_H),
            border_radius=3,
        )

    @property
    def score(self) -> int:
        """Spendable coin wallet (also used as the run score)."""
        return self._coins

    @property
    def stage_earned(self) -> int:
        """Coins earned toward the current stage goal."""
        return self._stage_earned

    @property
    def stage_count(self) -> int:
        """Total number of duel stages in a full clear."""
        return _TOTAL_STAGES
