"""
Flappy Bird Clone - Main Game Module
=====================================
A Flappy Bird-style game using Pygame. The bird flaps to avoid pipes;
game continues until collision with pipe or ground.

Controls:
    - Mouse click: Start game and flap.
    - R: Restart game.
    - D: Delete nearest pipe pair (debug).

Run from project root: python bird.py
"""

from __future__ import annotations

import os
import random
from typing import Literal

import pygame

# ---------------------------------------------------------------------------
# Constants (extract magic numbers per project rules)
# ---------------------------------------------------------------------------
_SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
_IMG_DIR: str = os.path.join(_SCRIPT_DIR, "img")

SCREEN_WIDTH: int = 864
SCREEN_HEIGHT: int = 768
FPS: int = 60
GROUND_Y: int = 650
GROUND_TILE_WIDTH: int = 35

# Bird physics
GRAVITY: float = 0.5
MAX_FALL_VELOCITY: float = 8.0
FLAP_VELOCITY: float = -10.0
BIRD_ROTATION_FACTOR: float = -5.0
GAME_OVER_ROTATION: float = -90.0

# Pipe config
SCROLL_SPEED: int = 6
PIPE_GAP_BASE: int = 200
PIPE_GAP_VARIANCE: int = 40
PIPE_SPAWN_INTERVAL_MIN: int = 80
PIPE_SPAWN_INTERVAL_MAX: int = 120
PIPE_SPAWN_OFFSET: int = 50
PIPE_GAP_CENTER_MIN: int = 200
PIPE_GAP_CENTER_MAX: int = 450

# Animation
FLAP_COOLDOWN_FRAMES: int = 5
AUTO_PLAY_FLAP_VELOCITY_THRESHOLD: float = 3.0
AUTO_PLAY_CENTER_OFFSET: int = 30

# Pipe position enum (top pipe vs bottom pipe)
PipePosition = Literal[1, -1]
PIPE_TOP: PipePosition = 1
PIPE_BOTTOM: PipePosition = -1


def _res(path: str) -> str:
    """Resolve image path relative to img/ directory."""
    return os.path.join(_IMG_DIR, os.path.basename(path))


# ---------------------------------------------------------------------------
# Pygame setup
# ---------------------------------------------------------------------------
pygame.init()
clock: pygame.time.Clock = pygame.time.Clock()
screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

bg: pygame.Surface = pygame.image.load(_res("bg.png"))
ground_img: pygame.Surface = pygame.image.load(_res("ground.png"))

# Game state (module-level for sprite update callbacks; refactor to GameState class later)
ground_scroll: int = 0
flying: bool = False
game_over: bool = False
auto_play: bool = False
pipe_spawn_timer: int = 0
pipe_spawn_interval: int = 90


# ---------------------------------------------------------------------------
# Bird Sprite
# ---------------------------------------------------------------------------
class Bird(pygame.sprite.Sprite):
    """Player-controlled bird that flaps to gain altitude.

    Attributes:
        images: List of animation frames.
        index: Current frame index.
        counter: Frame counter for animation timing.
        vel: Vertical velocity (positive = falling).
        clicked: Prevents multiple flaps per mouse press.
    """

    def __init__(self, x: int, y: int) -> None:
        """Create a new Bird at the given position.

        Args:
            x: Initial center X.
            y: Initial center Y.
        """
        super().__init__()
        self.images: list[pygame.Surface] = []
        for i in range(1, 4):
            img = pygame.image.load(_res(f"bird{i}.png"))
            self.images.append(img)
        self.index: int = 0
        self.counter: int = 0
        self.image: pygame.Surface = self.images[self.index]
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))
        self.vel: float = 0.0
        self.clicked: bool = False

    def update(self) -> None:
        """Update bird physics, input, and animation."""
        global flying, game_over

        # Apply gravity when game has started
        if flying:
            self.vel += GRAVITY
            if self.vel > MAX_FALL_VELOCITY:
                self.vel = MAX_FALL_VELOCITY
            if self.rect.bottom < GROUND_Y:
                self.rect.y += int(self.vel)

        if not game_over:
            self._handle_flap_input()
            self._animate()
        else:
            self.image = pygame.transform.rotate(
                self.images[self.index], GAME_OVER_ROTATION
            )
            self.rect = self.image.get_rect(center=self.rect.center)

    def _handle_flap_input(self) -> None:
        """Process flap input (auto-play heuristic or mouse click)."""
        flap = False
        if auto_play:
            center_y = SCREEN_HEIGHT // 2 + AUTO_PLAY_CENTER_OFFSET
            if self.vel > AUTO_PLAY_FLAP_VELOCITY_THRESHOLD or self.rect.centery > center_y:
                flap = True
        else:
            if pygame.mouse.get_pressed()[0] and not self.clicked:
                flap = True

        if flap:
            self.clicked = True
            self.vel = FLAP_VELOCITY

        if not auto_play and not pygame.mouse.get_pressed()[0]:
            self.clicked = False

    def _animate(self) -> None:
        """Advance wing animation and apply rotation."""
        self.counter += 1
        if self.counter > FLAP_COOLDOWN_FRAMES:
            self.counter = 0
            self.index = (self.index + 1) % len(self.images)
        self.image = pygame.transform.rotate(
            self.images[self.index], self.vel * BIRD_ROTATION_FACTOR
        )
        self.rect = self.image.get_rect(center=self.rect.center)


# ---------------------------------------------------------------------------
# Pipe Sprite
# ---------------------------------------------------------------------------
class Pipe(pygame.sprite.Sprite):
    """Obstacle pipe (top or bottom half of a pipe pair).

    Attributes:
        image: Pipe texture (flipped for top pipe).
        rect: Collision and draw rectangle.
    """

    def __init__(self, x: int, y: int, position: PipePosition) -> None:
        """Create a pipe at the given position.

        Args:
            x: Left edge X in screen coordinates.
            y: For top pipe: bottom edge Y. For bottom pipe: top edge Y.
            position: PIPE_TOP (1) or PIPE_BOTTOM (-1).
        """
        super().__init__()
        self.image = pygame.image.load(_res("pipe.png"))
        self.rect = self.image.get_rect()
        if position == PIPE_TOP:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = (x, y)
        elif position == PIPE_BOTTOM:
            self.rect.topleft = (x, y)

    def update(self) -> None:
        """Move pipe left; remove when off-screen."""
        if not game_over:
            self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.kill()


# ---------------------------------------------------------------------------
# Game Setup
# ---------------------------------------------------------------------------
bird_group: pygame.sprite.Group = pygame.sprite.Group()
pipe_group: pygame.sprite.Group = pygame.sprite.Group()
flappy: Bird = Bird(100, SCREEN_HEIGHT // 2)
bird_group.add(flappy)


def spawn_pipes(x: int, gap: int) -> None:
    """Spawn a top and bottom pipe pair with a vertical gap.

    Args:
        x: Spawn X position (left edge of pipes).
        gap: Vertical gap between top and bottom pipes.
    """
    center_y = random.randint(PIPE_GAP_CENTER_MIN, PIPE_GAP_CENTER_MAX)
    top_y = center_y - gap // 2
    bottom_y = center_y + gap // 2
    top = Pipe(x, top_y, PIPE_TOP)
    bottom = Pipe(x, bottom_y, PIPE_BOTTOM)
    pipe_group.add(top)
    pipe_group.add(bottom)


def restart_game(extra_distance: int = 400) -> None:
    """Reset game state and spawn initial pipes.

    Args:
        extra_distance: X offset for first pipe spawn (beyond screen).
    """
    global game_over, flying, pipe_spawn_timer, pipe_spawn_interval

    game_over = False
    flying = False
    flappy.rect.center = (100, SCREEN_HEIGHT // 2)
    flappy.vel = 0.0
    flappy.index = 0
    flappy.counter = 0

    pipe_group.empty()
    pipe_spawn_timer = 0
    pipe_spawn_interval = random.randint(
        PIPE_SPAWN_INTERVAL_MIN, PIPE_SPAWN_INTERVAL_MAX
    )
    spawn_pipes(SCREEN_WIDTH + extra_distance, PIPE_GAP_BASE)


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------
spawn_pipes(300, PIPE_GAP_BASE)
run: bool = True

while run:
    clock.tick(FPS)
    screen.blit(bg, (0, 0))

    bird_group.draw(screen)
    bird_group.update()
    pipe_group.draw(screen)
    pipe_group.update()

    # Collision: end game when bird hits any pipe
    if pygame.sprite.spritecollide(flappy, pipe_group, False):
        game_over = True
        flying = False

    screen.blit(ground_img, (ground_scroll, GROUND_Y))

    # Ground collision
    if flappy.rect.bottom > GROUND_Y:
        game_over = True
        flying = False

    if not game_over:
        ground_scroll -= SCROLL_SPEED
        if abs(ground_scroll) > GROUND_TILE_WIDTH:
            ground_scroll = 0

        pipe_spawn_timer += 1
        if pipe_spawn_timer > pipe_spawn_interval:
            gap = PIPE_GAP_BASE + random.randint(-PIPE_GAP_VARIANCE, PIPE_GAP_VARIANCE)
            spawn_pipes(SCREEN_WIDTH + PIPE_SPAWN_OFFSET, gap)
            pipe_spawn_timer = 0
            pipe_spawn_interval = random.randint(
                PIPE_SPAWN_INTERVAL_MIN, PIPE_SPAWN_INTERVAL_MAX
            )

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and not flying
            and not game_over
        ):
            flying = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                restart_game(extra_distance=400)
            if event.key == pygame.K_d:
                candidates = [p for p in pipe_group.sprites() if p.rect.right > 0]
                if candidates:
                    first_x = min(candidate.rect.x for candidate in candidates)
                    for p in pipe_group.sprites():
                        if p.rect.x == first_x:
                            p.kill()

    pygame.display.update()

pygame.quit()
