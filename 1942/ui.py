"""HUD, menus, and hangar upgrade screen."""

from __future__ import annotations

import pygame as pg

import config as cfg
from entities import Loadout


def _font(size: int, bold: bool = False) -> pg.font.Font:
    return pg.font.SysFont("consolas", size, bold=bold)


class HUD:
    """In-mission heads-up display."""

    def draw(
        self,
        surface: pg.Surface,
        *,
        mission: int,
        title: str,
        score: int,
        hp: int,
        max_hp: int,
        bombs: int,
        loop_cd: float,
        loop_max: float,
        message: str = "",
    ) -> None:
        """Paint score, lives, bombs, and loop cooldown."""
        f = _font(18, True)
        small = _font(14)
        surface.blit(f.render(f"SCORE {score:06d}", True, cfg.UI_WHITE), (10, 8))
        surface.blit(small.render(f"M{mission:02d}  {title}", True, cfg.UI_DIM), (10, 28))

        # HP as plane icons
        for i in range(max_hp):
            color = cfg.PLAYER_BLUE if i < hp else (60, 70, 80)
            pg.draw.polygon(
                surface,
                color,
                [
                    (cfg.SCREEN_W - 18 - i * 18, 22),
                    (cfg.SCREEN_W - 10 - i * 18, 10),
                    (cfg.SCREEN_W - 2 - i * 18, 22),
                ],
            )
        surface.blit(small.render(f"BOMBS {bombs}", True, cfg.UI_GOLD), (cfg.SCREEN_W - 90, 30))

        # Loop cooldown bar
        bar_w = 60
        x0 = cfg.SCREEN_W - 70
        y0 = 48
        pg.draw.rect(surface, (40, 40, 50), pg.Rect(x0, y0, bar_w, 5))
        ready = 1.0 if loop_cd <= 0 else max(0.0, 1.0 - loop_cd / loop_max)
        pg.draw.rect(surface, (120, 200, 255), pg.Rect(x0, y0, int(bar_w * ready), 5))
        surface.blit(small.render("LOOP", True, cfg.UI_DIM), (x0, y0 + 6))

        if message:
            msg = f.render(message, True, cfg.UI_GOLD)
            surface.blit(msg, msg.get_rect(center=(cfg.SCREEN_W // 2, 70)))


class MenuView:
    """Title / briefing / hangar / game-over screens."""

    def draw_title(self, surface: pg.Surface, high_score: int) -> None:
        """Main title screen."""
        surface.fill(cfg.OCEAN_DEEP)
        title = _font(48, True).render("1942", True, cfg.UI_GOLD)
        sub = _font(20).render("MIDWAY ATOLL", True, cfg.UI_WHITE)
        blurb = _font(14).render("Pacific Theater — Intercept the raid", True, cfg.UI_DIM)
        prompt = _font(16).render("ENTER — Briefing    ESC — Quit", True, cfg.UI_WHITE)
        hs = _font(14).render(f"High Score  {high_score:06d}", True, cfg.UI_GOLD)
        surface.blit(title, title.get_rect(center=(cfg.SCREEN_W // 2, 200)))
        surface.blit(sub, sub.get_rect(center=(cfg.SCREEN_W // 2, 255)))
        surface.blit(blurb, blurb.get_rect(center=(cfg.SCREEN_W // 2, 295)))
        surface.blit(hs, hs.get_rect(center=(cfg.SCREEN_W // 2, 360)))
        surface.blit(prompt, prompt.get_rect(center=(cfg.SCREEN_W // 2, 520)))
        controls = _font(13).render(
            "WASD/Arrows move  SPACE fire  SHIFT loop  B bomb",
            True,
            cfg.UI_DIM,
        )
        surface.blit(controls, controls.get_rect(center=(cfg.SCREEN_W // 2, 560)))

    def draw_briefing(
        self,
        surface: pg.Surface,
        mission: int,
        title: str,
        briefing: str,
        score: int,
    ) -> None:
        """Pre-mission briefing card."""
        surface.fill((12, 40, 70))
        pg.draw.rect(surface, cfg.OCEAN_MID, pg.Rect(30, 120, cfg.SCREEN_W - 60, 360), border_radius=8)
        head = _font(22, True).render(f"MISSION {mission:02d}", True, cfg.UI_GOLD)
        ttl = _font(26, True).render(title, True, cfg.UI_WHITE)
        surface.blit(head, head.get_rect(center=(cfg.SCREEN_W // 2, 160)))
        surface.blit(ttl, ttl.get_rect(center=(cfg.SCREEN_W // 2, 200)))
        # Word-wrap briefing
        words = briefing.split()
        lines: list[str] = []
        cur = ""
        for w in words:
            test = f"{cur} {w}".strip()
            if _font(16).size(test)[0] > cfg.SCREEN_W - 100:
                lines.append(cur)
                cur = w
            else:
                cur = test
        if cur:
            lines.append(cur)
        y = 250
        for line in lines:
            img = _font(16).render(line, True, cfg.UI_DIM)
            surface.blit(img, img.get_rect(center=(cfg.SCREEN_W // 2, y)))
            y += 24
        score_img = _font(14).render(f"Campaign score  {score:06d}", True, cfg.UI_GOLD)
        surface.blit(score_img, score_img.get_rect(center=(cfg.SCREEN_W // 2, 400)))
        prompt = _font(16).render("ENTER — Launch    H — Hangar", True, cfg.UI_WHITE)
        surface.blit(prompt, prompt.get_rect(center=(cfg.SCREEN_W // 2, 440)))

    def draw_hangar(
        self,
        surface: pg.Surface,
        loadout: Loadout,
        score: int,
        cursor: int,
    ) -> None:
        """Upgrade shop between missions."""
        surface.fill((20, 28, 40))
        head = _font(26, True).render("HANGAR UPGRADES", True, cfg.UI_GOLD)
        surface.blit(head, head.get_rect(center=(cfg.SCREEN_W // 2, 50)))
        bank = _font(16).render(f"Banked score (spend): {score}", True, cfg.UI_WHITE)
        surface.blit(bank, bank.get_rect(center=(cfg.SCREEN_W // 2, 90)))

        items = [
            ("Firepower", loadout.fire_level, 4, "Faster / denser forward guns"),
            ("Spread Shot", loadout.spread_level, 3, "Wing guns & angled volleys"),
            ("Engine", loadout.speed_level, 3, "Higher airspeed"),
            ("Armor Plate", loadout.shield_level, 3, "Extra hit points"),
            ("Bomb Bay", loadout.bomb_level, 3, "More bombs at sortie start"),
        ]
        y = 140
        for i, (name, level, cap, desc) in enumerate(items):
            selected = i == cursor
            cost = cfg.UPGRADE_COST_BASE * (level + 1)
            color = cfg.UI_GOLD if selected else cfg.UI_WHITE
            prefix = ">" if selected else " "
            line = _font(18, selected).render(
                f"{prefix} {name}  Lv{level}/{cap}  ({cost} pts)",
                True,
                color,
            )
            surface.blit(line, (50, y))
            surface.blit(_font(13).render(desc, True, cfg.UI_DIM), (70, y + 22))
            y += 55

        hint = _font(14).render(
            "UP/DOWN select   ENTER buy   ESC back",
            True,
            cfg.UI_DIM,
        )
        surface.blit(hint, hint.get_rect(center=(cfg.SCREEN_W // 2, 680)))

    def draw_result(
        self,
        surface: pg.Surface,
        *,
        victory: bool,
        score: int,
        mission: int,
        final: bool = False,
    ) -> None:
        """Mission clear or game over."""
        overlay = pg.Surface((cfg.SCREEN_W, cfg.SCREEN_H), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        if final:
            text = "MIDWAY SECURED"
            sub = "All 20 missions complete"
        elif victory:
            text = "MISSION CLEAR"
            sub = f"Proceeding to sortie {mission + 1:02d}" if mission < cfg.TOTAL_MISSIONS else ""
        else:
            text = "SHOT DOWN"
            sub = "The carriers needed you"
        img = _font(36, True).render(text, True, cfg.UI_GOLD if victory else cfg.UI_RED)
        surface.blit(img, img.get_rect(center=(cfg.SCREEN_W // 2, 280)))
        s = _font(18).render(f"Score  {score:06d}", True, cfg.UI_WHITE)
        surface.blit(s, s.get_rect(center=(cfg.SCREEN_W // 2, 340)))
        if sub:
            surface.blit(
                _font(14).render(sub, True, cfg.UI_DIM),
                _font(14).render(sub, True, cfg.UI_DIM).get_rect(center=(cfg.SCREEN_W // 2, 380)),
            )
        prompt = "ENTER — Continue" if victory and not final else "ENTER — Title"
        surface.blit(
            _font(16).render(prompt, True, cfg.UI_WHITE),
            _font(16).render(prompt, True, cfg.UI_WHITE).get_rect(center=(cfg.SCREEN_W // 2, 450)),
        )
