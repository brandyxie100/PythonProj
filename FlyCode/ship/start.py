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
NUMBER_OF_ENEMIES: int = 1000
COLLISION_RADIUS: int = 40
BULLET_OFFSCREEN_THRESHOLD: int = -40
PLAYER_X_MIN: int = -45
PLAYER_X_MAX: int = 645
ENEMY_RESET_Y_THRESHOLD: int = 600
PLAYER_DAMAGE_PER_HIT: int = 10

# ---------------------------------------------------------------------------
# Pygame setup
# ---------------------------------------------------------------------------
pygame.init()
bg: pygame.Surface = pygame.image.load(_res("bg3.jpg"))
screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

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
        e.change_y()

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

        # Continuous key input for movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            player.move_right()
        if keys[pygame.K_LEFT]:
            player.move_left()

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
