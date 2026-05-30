"""
Ship Shooter Game - Main Entry Point
=====================================
A top-down shooter where the player moves left/right, shoots bullets,
and avoids descending enemies. Health decreases on enemy collision.

Controls:
    - LEFT/RIGHT arrows: Move player.
    - SPACE: Shoot bullet.

Run from project root: python FlyCode/ship/start.py
Or from ship dir: python start.py
"""

from __future__ import annotations

import math
import os

import pygame

from component.bullet import Bullet
from component.enemy import Enemy
from component.player import Player
from config import res as _res


# ---------------------------------------------------------------------------
# Constants (extract magic numbers per project rules)
# ---------------------------------------------------------------------------
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 600
NUMBER_OF_ENEMIES: int = 100

COLLISION_RADIUS: int = 40
BULLET_OFFSCREEN_THRESHOLD: int = -40
PLAYER_X_MIN: int = -45
PLAYER_X_MAX: int = 645
ENEMY_RESET_Y_THRESHOLD: int = 600
PLAYER_DAMAGE_PER_HIT: int = 10
AUTO_SHOOT_INTERVAL_MS: int = 120  # milliseconds between automatic shots (lower = faster fire)
MIN_AUTO_SHOOT_MS: int = 50
MAX_AUTO_SHOOT_MS: int = 1000
AUTO_SHOOT_STEP_MS: int = 50
RAPID_FIRE_KEY = pygame.K_LSHIFT
RAPID_FIRE_DURATION_MS: int = 2000  # how long rapid-fire lasts when activated (ms)
RAPID_FIRE_COOLDOWN_MS: int = 3000  # cooldown after rapid-fire ends (ms)

# ---------------------------------------------------------------------------
# Pygame setup
# ---------------------------------------------------------------------------
pygame.init()
bg: pygame.Surface = pygame.image.load(_res("bg3.jpg"))
screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
font = pygame.font.Font(None, 24)

# Background music (optional; skip if file missing)
_music_path = _res("background-music.mp3")
if os.path.exists(_music_path):
    pygame.mixer.music.load(_music_path)
    pygame.mixer.music.play(-1)

player: Player = Player()
enemys: list[Enemy] = [Enemy() for _ in range(NUMBER_OF_ENEMIES)]
bullets: list[Bullet] = []


def is_collision(
    x1: float, y1: float, x2: float, y2: float, radius: int = COLLISION_RADIUS
) -> bool:
    """Check if two points are within collision radius.

    Args:
        x1: First point X.
        y1: First point Y.
        x2: Second point X.
        y2: Second point Y.
        radius: Collision radius in pixels.

    Returns:
        True if distance < radius.
    """
    return math.dist((x1, y1), (x2, y2)) < radius


def show_enemies() -> None:
    """Draw and update all enemies; handle collision with player."""
    for e in enemys:
        screen.blit(e.show_ememy(), (e.get_enemy_x(), e.get_enemy_y()))
        # pass player's X so enemies can occasionally steer/attack toward the ship
        e.change_y(player.get_player_x())

        # Reset enemy when it reaches bottom of screen
        if e.get_enemy_y() > ENEMY_RESET_Y_THRESHOLD:
            e.reset()

        # Player hit: deal damage and reset enemy
        if is_collision(
            e.get_enemy_x(), e.get_enemy_y(),
            player.get_player_x(), player.get_player_y(),
        ):
            player.health -= PLAYER_DAMAGE_PER_HIT
            print("Player hit! Health:", player.health)
            e.reset()


def show_bullet(
    screen_surf: pygame.Surface,
    bullets_list: list[Bullet],
    enemies_list: list[Enemy],
) -> None:
    """Draw and update bullets; handle hits and off-screen removal."""
    for b in bullets_list[:]:
        b.move_bullet()
        screen_surf.blit(b.show_bullet(), (b.get_bullet_x(), b.get_bullet_y()))

        # Remove bullet when off top of screen
        if b.get_bullet_y() < BULLET_OFFSCREEN_THRESHOLD:
            bullets_list.remove(b)
            continue

        hit_enemy = b.hit(enemies_list)
        if hit_enemy:
            b.bao_sound()
            enemies_list.remove(hit_enemy)
            bullets_list.remove(b)


def main() -> None:
    """Main game loop."""
    running = True
    global AUTO_SHOOT_INTERVAL_MS
    # time (ms) of last automatic shot
    last_shot_time = pygame.time.get_ticks()
    # rapid-fire runtime state
    rapid_fire_mode = False
    rapid_fire_activated_until = 0
    rapid_fire_cooldown_until = 0
    while running:
        screen.blit(bg, (1, 2))

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bullet = Bullet(
                        playerX=player.get_player_x(),
                        playerY=player.get_player_y(),
                    )
                    bullets.append(bullet)
                    print("shoot")
                # Adjust auto-shoot interval: ']' = faster (decrease ms), '[' = slower (increase ms)
                if event.key == pygame.K_RIGHTBRACKET:
                    AUTO_SHOOT_INTERVAL_MS = max(MIN_AUTO_SHOOT_MS, AUTO_SHOOT_INTERVAL_MS - AUTO_SHOOT_STEP_MS)
                    print(f"Auto-shoot interval: {AUTO_SHOOT_INTERVAL_MS} ms")
                if event.key == pygame.K_LEFTBRACKET:
                    AUTO_SHOOT_INTERVAL_MS = min(MAX_AUTO_SHOOT_MS, AUTO_SHOOT_INTERVAL_MS + AUTO_SHOOT_STEP_MS)
                    print(f"Auto-shoot interval: {AUTO_SHOOT_INTERVAL_MS} ms")
                # Rapid-fire activation on Shift press (only if not cooling down)
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    now = pygame.time.get_ticks()
                    if now >= rapid_fire_cooldown_until:
                        rapid_fire_mode = True
                        rapid_fire_activated_until = now + RAPID_FIRE_DURATION_MS
                        print("Rapid-fire activated")
                    else:
                        remaining = (rapid_fire_cooldown_until - now) / 1000.0
                        print(f"Rapid-fire cooling down: {remaining:.1f}s")
            if event.type == pygame.KEYUP:
                # Stop rapid-fire early on Shift release
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    now = pygame.time.get_ticks()
                    if rapid_fire_mode:
                        rapid_fire_mode = False
                        rapid_fire_cooldown_until = now + RAPID_FIRE_COOLDOWN_MS
                        print("Rapid-fire ended, cooldown started")

        # Continuous key input for movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            player.move_right()
        if keys[pygame.K_LEFT]:
            player.move_left()

        # Automatic shooting: fire a bullet every AUTO_SHOOT_INTERVAL_MS
        # Rapid-fire mode shortens the interval while active; it ends when duration expires or on key release
        now = pygame.time.get_ticks()
        # expire rapid-fire automatically when its duration passes
        if rapid_fire_mode and now >= rapid_fire_activated_until:
            rapid_fire_mode = False
            rapid_fire_cooldown_until = now + RAPID_FIRE_COOLDOWN_MS
            print("Rapid-fire duration ended, cooldown started")
        effective_interval = MIN_AUTO_SHOOT_MS if rapid_fire_mode else AUTO_SHOOT_INTERVAL_MS
        if now - last_shot_time >= effective_interval:
            bullet = Bullet(
                playerX=player.get_player_x(),
                playerY=player.get_player_y(),
            )
            bullets.append(bullet)
            last_shot_time = now
            print("auto-shoot")

        # Draw UI: current auto-shoot interval and brief instructions
        rapid_text = " (RAPID)" if rapid_fire_mode else ""
        cd_text = ""
        if now < rapid_fire_cooldown_until:
            remaining = (rapid_fire_cooldown_until - now) / 1000.0
            cd_text = f"   CD: {remaining:.1f}s"
        info_surf = font.render(
            f"Auto-shoot: {AUTO_SHOOT_INTERVAL_MS} ms{rapid_text}{cd_text}   ] faster   [ slower   Hold Shift for rapid-fire",
            True,
            (255, 255, 255),
        )
        screen.blit(info_surf, (10, 10))

        # Draw player and health bar
        screen.blit(
            player.show_player(),
            (player.get_player_x(), player.get_player_y()),
        )
        player.draw_health_bar(screen)

        # Clamp player X to screen bounds
        if player.get_player_x() > PLAYER_X_MAX:
            player.x = PLAYER_X_MAX
        if player.get_player_x() < PLAYER_X_MIN:
            player.x = PLAYER_X_MIN

        show_enemies()
        show_bullet(screen_surf=screen, bullets_list=bullets, enemies_list=enemys)

        if player.health <= 0:
            print("Game Over")
            running = False

        pygame.display.update()


if __name__ == "__main__":
    main()
