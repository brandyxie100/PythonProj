"""Tests for multi-part weapon rendering."""

from __future__ import annotations

import pygame

import config as c
from weapon_draw import draw_panel_icon, draw_projectile_weapon, draw_weapon


def test_draw_weapon_all_keys_without_error() -> None:
    surf = pygame.Surface((200, 120))
    grip = (20.0, 60.0)
    tip = (160.0, 50.0)
    keys = set(c.THROW_WEAPONS) | {"arrow"}
    for key in keys:
        draw_weapon(surf, key, grip, tip, scale=1.0)


def test_draw_projectile_bow_becomes_arrow() -> None:
    surf = pygame.Surface((200, 120))
    # Should not raise; bow flight form uses the arrow drawer.
    draw_projectile_weapon(surf, "bow", (10.0, 60.0), (180.0, 40.0))


def test_draw_panel_icon_for_throw_weapons() -> None:
    surf = pygame.Surface((80, 40))
    for key in c.THROW_WEAPON_ORDER:
        draw_panel_icon(surf, key, (40.0, 20.0), size=22.0)
