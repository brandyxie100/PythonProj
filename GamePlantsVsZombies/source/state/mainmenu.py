"""
Plants vs Zombies - Main Menu State
====================================
Title screen with Adventure and Cross mode options.
"""

__author__ = "marble_xu"

import pygame as pg

from .. import constants as c
from .. import tool


class Menu(tool.State):
    """Main menu state: Adventure + Cross mode buttons."""

    def __init__(self):
        tool.State.__init__(self)

    def startup(self, current_time, persist):
        self.next = c.LEVEL
        self.persist = persist
        self.game_info = persist

        self.setupBackground()
        self.setupOption()
        self.setupCrossOption()

    def setupBackground(self):
        frame_rect = [80, 0, 800, 600]
        self.bg_image = tool.get_image(tool.GFX[c.MAIN_MENU_IMAGE], *frame_rect)
        self.bg_rect = self.bg_image.get_rect()
        self.bg_rect.x = 0
        self.bg_rect.y = 0

    def setupOption(self):
        self.option_frames = []
        frame_names = [c.OPTION_ADVENTURE + '_0', c.OPTION_ADVENTURE + '_1']
        frame_rect = [0, 0, 165, 77]

        for name in frame_names:
            self.option_frames.append(
                tool.get_image(tool.GFX[name], *frame_rect, c.BLACK, 1.7)
            )

        self.option_frame_index = 0
        self.option_image = self.option_frames[self.option_frame_index]
        self.option_rect = self.option_image.get_rect()
        self.option_rect.x = 435
        self.option_rect.y = 75

        self.option_start = 0
        self.option_timer = 0
        self.option_clicked = False
        self.pending_mode = c.MODE_ADVENTURE

    def setupCrossOption(self):
        """Cross-Breeds button: custom DNA-helix art under Adventure."""
        btn = tool.GFX.get(c.CROSS_BUTTON)
        if isinstance(btn, pg.Surface):
            self.cross_image = btn
        else:
            from ..component.cross_ui import build_cross_button

            self.cross_image = build_cross_button()
        self.cross_rect = self.cross_image.get_rect()
        self.cross_rect.x = 430
        self.cross_rect.y = 210
        self.cross_hit = self.cross_rect.inflate(8, 8)
        self.cross_clicked = False
        self.cross_start = 0
        self.cross_flash = False

    def checkOptionClick(self, mouse_pos):
        x, y = mouse_pos
        if (
            x >= self.option_rect.x
            and x <= self.option_rect.right
            and y >= self.option_rect.y
            and y <= self.option_rect.bottom
        ):
            self.option_clicked = True
            self.pending_mode = c.MODE_ADVENTURE
            self.option_timer = self.option_start = self.current_time
            return True
        return False

    def checkCrossClick(self, mouse_pos):
        if self.cross_hit.collidepoint(mouse_pos):
            self.cross_clicked = True
            self.cross_flash = True
            self.pending_mode = c.MODE_CROSS
            self.cross_start = self.current_time
            return True
        return False

    def _start_mode(self) -> None:
        self.game_info[c.GAME_MODE] = self.pending_mode
        self.game_info[c.LEVEL_NUM] = c.START_LEVEL_NUM
        self.done = True

    def update(self, surface, current_time, mouse_pos, mouse_click):
        self.current_time = self.game_info[c.CURRENT_TIME] = current_time

        if not self.option_clicked and not self.cross_clicked:
            if mouse_pos:
                if not self.checkOptionClick(mouse_pos):
                    self.checkCrossClick(mouse_pos)
        elif self.option_clicked:
            if (self.current_time - self.option_timer) > 200:
                self.option_frame_index += 1
                if self.option_frame_index >= 2:
                    self.option_frame_index = 0
                self.option_timer = self.current_time
                self.option_image = self.option_frames[self.option_frame_index]
            if (self.current_time - self.option_start) > 1300:
                self._start_mode()
        elif self.cross_clicked:
            if (self.current_time - self.cross_start) > 600:
                self._start_mode()

        surface.blit(self.bg_image, self.bg_rect)
        surface.blit(self.option_image, self.option_rect)
        img = self.cross_image
        if self.cross_flash:
            glow = pg.Surface(img.get_size(), pg.SRCALPHA)
            glow.fill((255, 255, 180, 60))
            tmp = img.copy()
            tmp.blit(glow, (0, 0), special_flags=pg.BLEND_RGBA_ADD)
            surface.blit(tmp, self.cross_rect)
        else:
            surface.blit(img, self.cross_rect)
