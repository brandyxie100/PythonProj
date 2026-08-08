"""Main Blumgi Merge scene — shop, merge board, 100-stage dungeon."""

from __future__ import annotations

from typing import Optional

import pygame

import config as c
from battle import Battle
from board import Board
from config import stage_spec
from fx import FXSystem
from slime import Slime


class Game:
    """Merge-battler campaign across 100 dungeon floors."""

    def __init__(self) -> None:
        self._title = pygame.font.SysFont("Arial", 52, bold=True)
        self._font = pygame.font.SysFont("Arial", 24, bold=True)
        self._small = pygame.font.SysFont("Arial", 18, bold=True)
        self._tiny = pygame.font.SysFont("Arial", 14)

        self.stage_no = 1
        self.gold = c.START_GOLD
        self.board = Board()
        self.fx = FXSystem()
        self.battle: Battle | None = None
        self.state = "title"  # title | prep | fight | clear | lose | win
        self.message = ""
        self.pulse = 0.0
        self.request_quit = False

        self.buy_rect = pygame.Rect(560, 130, 170, 52)
        self.fight_rect = pygame.Rect(750, 130, 170, 52)
        self._seed_start_slimes()

    def _seed_start_slimes(self) -> None:
        self.board.clear()
        for _ in range(2):
            self.board.try_buy(1)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == "prep":
                self.state = "title"
            else:
                self.request_quit = True
            return

        if self.state == "title":
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                self.state = "prep"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.state = "prep"
            return

        if self.state in ("clear", "lose", "win"):
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                self._advance_after_result()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._advance_after_result()
            return

        if self.state == "fight":
            return

        if self.state != "prep":
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buy_rect.collidepoint(event.pos):
                self._try_buy()
            elif self.fight_rect.collidepoint(event.pos):
                self._start_fight()
            else:
                self.board.start_drag(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self.board.move_drag(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            result = self.board.end_drag(event.pos)
            if result == "merge" and self.board.last_merge_at:
                x, y = self.board.last_merge_at
                # Find color of merged slime
                cell = self.board.hit_cell((int(x), int(y)))
                color = c.TIER_COLORS[0]
                if cell:
                    s = self.board.cells[cell[0]][cell[1]]
                    if s:
                        color = s.color
                self.fx.merge_burst(x, y, color)

    def _advance_after_result(self) -> None:
        if self.state == "win":
            self.stage_no = 1
            self.gold = c.START_GOLD
            self._seed_start_slimes()
            self.state = "title"
        elif self.state == "clear":
            self.stage_no += 1
            if self.stage_no > c.TOTAL_STAGES:
                self.state = "win"
            else:
                self.state = "prep"
        elif self.state == "lose":
            # Retry same floor, keep board + gold
            self.state = "prep"

    def _try_buy(self) -> None:
        if self.gold < c.SLIME_COST:
            self.message = "Not enough gold!"
            return
        ok, pos = self.board.try_buy(1)
        if not ok:
            self.message = "Board full — merge to make space!"
            return
        self.gold -= c.SLIME_COST
        if pos:
            self.fx.burst(pos[0], pos[1], c.TIER_COLORS[0], count=10)
        self.message = ""

    def _start_fight(self) -> None:
        army = self.board.army()
        if not army:
            self.message = "Buy some slimes first!"
            return
        # Copy army for battle animation state
        copies = [Slime(s.tier) for s in army]
        spec = stage_spec(self.stage_no)
        self.battle = Battle(stage=spec, army=copies, fx=self.fx)
        self.state = "fight"
        self.message = ""

    def update(self, dt: float) -> None:
        self.pulse += dt
        self.fx.update(dt)
        self.board.update(dt)

        if self.state == "fight" and self.battle is not None:
            for s in self.battle.army:
                s.update(dt)
            self.battle.update(dt)
            if self.battle.done:
                if self.battle.won:
                    self.gold += self.battle.reward
                    self.fx.coin_burst(c.SCREEN_W // 2, 280, self.battle.reward)
                    if self.stage_no >= c.TOTAL_STAGES:
                        self.state = "win"
                    else:
                        self.state = "clear"
                    self.message = f"Floor cleared! +{self.battle.reward} gold"
                else:
                    self.state = "lose"
                    self.message = "Your army fell — merge stronger and retry!"
                self.battle = None

    def draw(self, surf: pygame.Surface) -> None:
        self._draw_bg(surf)

        if self.state == "title":
            self._draw_title(surf)
            return

        if self.state == "fight" and self.battle is not None:
            self.battle.draw(surf)
            self.fx.draw(surf)
            return

        self._draw_hud(surf)
        self.board.draw(surf)
        self._draw_side_panel(surf)
        self.fx.draw(surf)

        if self.state in ("clear", "lose", "win"):
            self._banner(surf)

    def _draw_bg(self, surf: pygame.Surface) -> None:
        for y in range(c.SCREEN_H):
            t = y / c.SCREEN_H
            color = tuple(
                int(c.BG_TOP[i] + (c.BG_BOTTOM[i] - c.BG_TOP[i]) * t) for i in range(3)
            )
            pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))
        # Floating orbs decoration
        import math

        for i, (bx, by) in enumerate(((120, 40), (400, 60), (800, 45), (600, 70))):
            r = 10 + int(4 * abs(math.sin(self.pulse * 2 + i)))
            pygame.draw.circle(
                surf, c.TIER_COLORS[i % len(c.TIER_COLORS)], (bx, by), r
            )

    def _draw_title(self, surf: pygame.Surface) -> None:
        title = self._title.render("Blumgi Merge", True, (255, 120, 220))
        sub = self._font.render("Merge vivid slimes · Clear 100 dungeon floors", True, c.UI)
        tip = self._small.render("Click / Enter to start", True, c.GOLD)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 200)))
        surf.blit(sub, sub.get_rect(center=(c.SCREEN_W // 2, 270)))
        surf.blit(tip, tip.get_rect(center=(c.SCREEN_W // 2, 340)))
        # Preview tier rainbow
        from slime import slime_sprite

        for i in range(8):
            spr = slime_sprite(i + 1, 56)
            surf.blit(spr, (180 + i * 80, 400))

    def _draw_hud(self, surf: pygame.Surface) -> None:
        spec = stage_spec(self.stage_no)
        bar = pygame.Surface((c.SCREEN_W, 88), pygame.SRCALPHA)
        bar.fill((20, 10, 40, 180))
        surf.blit(bar, (0, 0))
        stage = self._font.render(
            f"Floor {self.stage_no}/{c.TOTAL_STAGES}: {spec.name}", True, c.UI
        )
        gold = self._font.render(f"Gold: {self.gold}", True, c.GOLD)
        dps = self._small.render(
            f"Army DPS {self.board.total_dps()}   HP {self.board.total_hp()}",
            True,
            c.UI_DIM,
        )
        surf.blit(stage, (20, 14))
        surf.blit(gold, (20, 48))
        surf.blit(dps, (280, 52))
        if self.message:
            msg = self._small.render(self.message, True, (255, 200, 120))
            surf.blit(msg, (520, 52))

    def _draw_side_panel(self, surf: pygame.Surface) -> None:
        # Buy button
        pygame.draw.rect(surf, c.BTN_BUY, self.buy_rect, border_radius=12)
        pygame.draw.rect(surf, c.UI, self.buy_rect, width=2, border_radius=12)
        buy = self._small.render(f"Buy Slime  ({c.SLIME_COST}g)", True, c.UI)
        surf.blit(buy, buy.get_rect(center=self.buy_rect.center))

        # Fight button
        pygame.draw.rect(surf, c.BTN_FIGHT, self.fight_rect, border_radius=12)
        pygame.draw.rect(surf, c.UI, self.fight_rect, width=2, border_radius=12)
        fight = self._small.render("FIGHT!", True, c.UI)
        surf.blit(fight, fight.get_rect(center=self.fight_rect.center))

        # Tips + tier legend
        tips = [
            "Drag matching slimes together to merge",
            "Higher tiers = more DPS & HP",
            "Boss every 10 floors",
        ]
        y = 210
        for line in tips:
            surf.blit(self._tiny.render(line, True, c.UI_DIM), (560, y))
            y += 22

        surf.blit(self._small.render("Tiers", True, c.UI), (560, 290))
        from slime import slime_sprite

        for i in range(min(5, c.MAX_TIER)):
            spr = slime_sprite(i + 1, 40)
            surf.blit(spr, (560 + i * 70, 320))
            name = self._tiny.render(c.TIER_NAMES[i][:7], True, c.TIER_COLORS[i])
            surf.blit(name, (560 + i * 70, 375))
        for i in range(5, c.MAX_TIER):
            spr = slime_sprite(i + 1, 40)
            surf.blit(spr, (560 + (i - 5) * 70, 410))
            name = self._tiny.render(c.TIER_NAMES[i][:7], True, c.TIER_COLORS[i])
            surf.blit(name, (560 + (i - 5) * 70, 465))

        hint = self._tiny.render("Esc — title", True, c.UI_DIM)
        surf.blit(hint, (560, 520))

    def _banner(self, surf: pygame.Surface) -> None:
        overlay = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((10, 5, 30, 160))
        surf.blit(overlay, (0, 0))
        if self.state == "clear":
            title = "FLOOR CLEAR!"
        elif self.state == "win":
            title = "YOU WIN! 100/100"
        else:
            title = "DEFEAT"
        t = self._title.render(title, True, c.GOLD if self.state != "lose" else (255, 100, 120))
        s = self._font.render(self.message or "Click / Enter to continue", True, c.UI)
        surf.blit(t, t.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 - 30)))
        surf.blit(s, s.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 + 40)))
