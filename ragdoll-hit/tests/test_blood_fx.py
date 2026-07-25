"""Tests for hit and death blood particle bursts."""

from __future__ import annotations

import pygame

import config as c
from blood_fx import BloodBurstSystem
from duel_mode import VersusScene
from projectiles import Projectile


def test_hit_burst_spawns_fewer_particles_than_death() -> None:
    fx = BloodBurstSystem()
    fx.spawn_hit((100.0, 200.0))
    hit_count = len(fx.particles)
    fx.clear()
    fx.spawn_death((100.0, 200.0))
    death_count = len(fx.particles)
    assert hit_count == c.BLOOD_HIT_COUNT
    assert death_count == c.BLOOD_DEATH_COUNT + c.BLOOD_DEATH_MIST_COUNT
    assert death_count > hit_count


def test_particles_expire_after_update() -> None:
    fx = BloodBurstSystem()
    fx.spawn_hit((50.0, 50.0))
    assert fx.particles
    for _ in range(120):
        fx.update(0.05)
    assert fx.particles == []


def test_death_particles_are_larger_on_average() -> None:
    fx = BloodBurstSystem()
    fx.spawn_hit((0.0, 0.0))
    hit_avg = sum(p.radius for p in fx.particles) / len(fx.particles)
    fx.clear()
    fx.spawn_death((0.0, 0.0))
    # Compare against heavy droplets only (exclude mist).
    heavy = [p for p in fx.particles if p.radius >= c.BLOOD_DEATH_RADIUS_MIN]
    death_avg = sum(p.radius for p in heavy) / len(heavy)
    assert death_avg > hit_avg


def test_projectile_hit_spawns_hit_blood() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    enemy = scene._enemy
    # Tip on mid-torso so the wound is non-lethal.
    tx, ty = enemy.x, enemy.neck[1] + 20.0
    half = c.THROW_WEAPONS["spear"].length * 0.5
    scene._projectiles = [
        Projectile("spear", "player", tx - half, ty, 200.0, 0.0, angle=0.0)
    ]
    before = len(scene._blood.particles)
    scene._advance_projectiles(0.016)
    assert not enemy.dead
    assert len(scene._blood.particles) == before + c.BLOOD_HIT_COUNT


def test_lethal_projectile_spawns_death_blood() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    enemy = scene._enemy
    hx, hy = enemy.head_center
    half = c.THROW_WEAPONS["spear"].length * 0.5
    scene._projectiles = [
        Projectile("spear", "player", hx - half, hy, 200.0, 0.0, angle=0.0)
    ]
    before = len(scene._blood.particles)
    scene._advance_projectiles(0.016)
    assert enemy.dead
    assert len(scene._blood.particles) == before + (
        c.BLOOD_DEATH_COUNT + c.BLOOD_DEATH_MIST_COUNT
    )


def test_blood_draw_does_not_raise() -> None:
    fx = BloodBurstSystem()
    fx.spawn_death((200.0, 300.0))
    surf = pygame.Surface((640, 360))
    fx.draw(surf)
    fx.update(0.016)
    fx.draw(surf)


def test_fall_death_triggers_blood_burst() -> None:
    scene = VersusScene()
    scene._dismiss_intro_popup()
    player = scene._player
    player.falling = True
    player.ground_y = c.SCREEN_H + 80.0
    before = len(scene._blood.particles)
    scene._update_fighter_with_death_fx(player, 0.016)
    assert player.dead
    assert len(scene._blood.particles) > before
