"""
Flappy Bird Clone - Main Game Module
=====================================
An infinite Flappy Bird-style game with escalating difficulty.
Pipes wobble and tilt as the score increases.

Controls:
    - Mouse click: Start game and flap.
    - R: Restart game.
    - D: Delete nearest pipe pair (debug).

Run from project root: python bird.py
"""

from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass
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

# Pipe config (base values; scaled by difficulty)
SCROLL_SPEED_BASE: int = 6
SCROLL_SPEED_MAX: int = 12
PIPE_GAP_BASE: int = 200
PIPE_GAP_MIN: int = 120
PIPE_SPAWN_INTERVAL_BASE: tuple[int, int] = (80, 120)
PIPE_SPAWN_INTERVAL_MIN: tuple[int, int] = (50, 70)
PIPE_SPAWN_OFFSET: int = 50
PIPE_GAP_CENTER_MIN: int = 200
PIPE_GAP_CENTER_MAX: int = 450

# Difficulty tiers (score thresholds)
TIER_EASY: int = 10
TIER_MEDIUM: int = 30
TIER_HARD: int = 60

# Wobble (Phase 2)
WOBBLE_AMPLITUDE_BASE: int = 20
WOBBLE_AMPLITUDE_MAX: int = 60
WOBBLE_FREQUENCY: float = 0.08

# Tilt (Phase 3)
TILT_AMPLITUDE: float = 15.0

# Animation
FLAP_COOLDOWN_FRAMES: int = 5
AUTO_PLAY_FLAP_VELOCITY_THRESHOLD: float = 3.0
AUTO_PLAY_CENTER_OFFSET: int = 30

# UI
FONT_SIZE_SCORE: int = 48
FONT_SIZE_GAME_OVER: int = 64
FONT_SIZE_RESTART: int = 32
GAME_OVER_OVERLAY_ALPHA: int = 180

# Restart button styling
RESTART_BTN_WIDTH: int = 240
RESTART_BTN_HEIGHT: int = 56
RESTART_BTN_COLOR: tuple[int, int, int] = (70, 130, 180)
RESTART_BTN_HOVER_COLOR: tuple[int, int, int] = (100, 160, 210)
RESTART_BTN_TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)

# Ability (invisibility + invincibility)
ABILITY_DURATION_MS: int = 3000  # 3 seconds
ABILITY_BTN_WIDTH: int = 64
ABILITY_BTN_HEIGHT: int = 64
ABILITY_BTN_MARGIN: int = 12
ABILITY_BTN_COLOR: tuple[int, int, int] = (40, 160, 40)
ABILITY_BTN_HOVER_COLOR: tuple[int, int, int] = (60, 190, 60)
ABILITY_BTN_ACTIVE_COLOR: tuple[int, int, int] = (120, 120, 120)
ABILITY_BTN_TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)

# Restart button styling
RESTART_BTN_WIDTH: int = 240
RESTART_BTN_HEIGHT: int = 56
RESTART_BTN_COLOR: tuple[int, int, int] = (70, 130, 180)
RESTART_BTN_HOVER_COLOR: tuple[int, int, int] = (100, 160, 210)
RESTART_BTN_TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
# Pipe position enum (top pipe vs bottom pipe)
PipePosition = Literal[1, -1]
PIPE_TOP: PipePosition = 1
PIPE_BOTTOM: PipePosition = -1


def _res(path: str) -> str:
    """Resolve image path relative to img/ directory."""
    return os.path.join(_IMG_DIR, os.path.basename(path))


# ---------------------------------------------------------------------------
# Phase 1: Difficulty scaling
# ---------------------------------------------------------------------------
@dataclass
class DifficultyParams:
    """Difficulty parameters scaled by score."""

    scroll_speed: int
    pipe_gap: int
    spawn_interval_range: tuple[int, int]
    gap_center_min: int
    gap_center_max: int
    wobble_amplitude: int
    wobble_enabled: bool
    tilt_enabled: bool


def get_difficulty_params(score: int) -> DifficultyParams:
    """Compute difficulty parameters based on current score.

    Args:
        score: Current player score.

    Returns:
        DifficultyParams with scaled values.
    """
    # Linear scaling per 5 points
    t = min(score / 5.0, 12.0)  # Cap at ~60 pts for max scaling
    scroll_speed = min(
        SCROLL_SPEED_BASE + int(t * 0.5),
        SCROLL_SPEED_MAX
    )
    pipe_gap = max(
        PIPE_GAP_BASE - int(t * 5),
        PIPE_GAP_MIN
    )
    si_base = PIPE_SPAWN_INTERVAL_BASE
    si_min = PIPE_SPAWN_INTERVAL_MIN
    spawn_lo = max(si_base[0] - int(t * 2), si_min[0])
    spawn_hi = max(si_base[1] - int(t * 2), si_min[1])
    spawn_interval_range = (spawn_lo, spawn_hi)

    # Narrow gap center range as score rises (harder angles)
    center_range = PIPE_GAP_CENTER_MAX - PIPE_GAP_CENTER_MIN
    shrink = int(min(t * 5, center_range // 2))
    gap_center_min = PIPE_GAP_CENTER_MIN + shrink // 2
    gap_center_max = PIPE_GAP_CENTER_MAX - shrink // 2

    # Wobble: enable from tier 2, amplitude scales with score
    wobble_enabled = score >= TIER_EASY
    wobble_amplitude = 0
    if wobble_enabled:
        wobble_amplitude = min(
            WOBBLE_AMPLITUDE_BASE + int(t * 3),
            WOBBLE_AMPLITUDE_MAX
        )

    # Tilt: enable from tier 3
    tilt_enabled = score >= TIER_MEDIUM

    return DifficultyParams(
        scroll_speed=scroll_speed,
        pipe_gap=pipe_gap,
        spawn_interval_range=spawn_interval_range,
        gap_center_min=gap_center_min,
        gap_center_max=gap_center_max,
        wobble_amplitude=wobble_amplitude,
        wobble_enabled=wobble_enabled,
        tilt_enabled=tilt_enabled,
    )


# ---------------------------------------------------------------------------
# Pygame setup
# ---------------------------------------------------------------------------
pygame.init()
clock: pygame.time.Clock = pygame.time.Clock()
screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

bg: pygame.Surface = pygame.image.load(_res("bg.png"))
ground_img: pygame.Surface = pygame.image.load(_res("ground.png"))

# Game state (module-level for sprite update callbacks)
ground_scroll: int = 0
flying: bool = False
game_over: bool = False
auto_play: bool = False
pipe_spawn_timer: int = 0
pipe_spawn_interval: int = 90
score: int = 0
high_score: int = 0
passed_pair_ids: set[int] = set()
next_pair_id: int = 0
scroll_speed: int = SCROLL_SPEED_BASE  # Updated each frame from difficulty
# Rectangle for restart button (set when drawing game-over screen)
restart_button_rect: pygame.Rect | None = None
# Ability state
ability_active: bool = False
ability_end_time: int = 0
ability_button_rect: pygame.Rect | None = None


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
            # honor ability invisibility while on the game-over display
            if ability_active:
                try:
                    self.image.set_alpha(128)
                except Exception:
                    pass
            else:
                try:
                    self.image.set_alpha(255)
                except Exception:
                    pass

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

        # If ability is active, make bird semi-transparent; otherwise fully visible
        if ability_active:
            try:
                self.image.set_alpha(128)
            except Exception:
                pass
        else:
            try:
                self.image.set_alpha(255)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Pipe Sprite (Phase 2: wobble, Phase 3: tilt)
# ---------------------------------------------------------------------------
# Cache pipe image to avoid loading per pipe
_pipe_image_cache: pygame.Surface | None = None


def _get_pipe_image() -> pygame.Surface:
    """Load and cache the pipe image."""
    global _pipe_image_cache
    if _pipe_image_cache is None:
        _pipe_image_cache = pygame.image.load(_res("pipe.png"))
    return _pipe_image_cache


class Pipe(pygame.sprite.Sprite):
    """Obstacle pipe (top or bottom half of a pipe pair).

    Supports vertical wobble and tilt based on difficulty tier.
    """

    def __init__(
        self,
        x: int,
        y: int,
        position: PipePosition,
        pair_id: int,
        phase: float,
        wobble_amplitude: int,
        wobble_enabled: bool,
        tilt_enabled: bool,
    ) -> None:
        """Create a pipe at the given position.

        Args:
            x: Left edge X in screen coordinates.
            y: For top pipe: bottom edge Y. For bottom pipe: top edge Y.
            position: PIPE_TOP (1) or PIPE_BOTTOM (-1).
            pair_id: Unique id for this pipe pair (for scoring).
            phase: Shared phase for wobble (radians).
            wobble_amplitude: Vertical oscillation amplitude (pixels).
            wobble_enabled: Whether to apply wobble.
            tilt_enabled: Whether to apply tilt.
        """
        super().__init__()
        base = _get_pipe_image().copy()
        if position == PIPE_TOP:
            base = pygame.transform.flip(base, False, True)
            self._anchor_bottomleft = True
        else:
            self._anchor_bottomleft = False

        self._base_image: pygame.Surface = base
        self.image: pygame.Surface = base
        self.rect: pygame.Rect = base.get_rect()
        if position == PIPE_TOP:
            self.rect.bottomleft = (x, y)
        else:
            self.rect.topleft = (x, y)

        self._base_x: float = float(x)
        self._base_y: float = float(y)
        self.pair_id: int = pair_id
        self._phase: float = phase
        self._wobble_amplitude: int = wobble_amplitude
        self._wobble_enabled: bool = wobble_enabled
        self._tilt_enabled: bool = tilt_enabled
        self._tilt_angle: float = 0.0

    def update(self) -> None:
        """Move pipe left; apply wobble and tilt; remove when off-screen."""
        global scroll_speed, game_over

        if not game_over:
            self._base_x -= scroll_speed
        self.rect.x = int(self._base_x)

        # Phase 2: vertical wobble (sine-wave oscillation)
        if self._wobble_enabled and self._wobble_amplitude > 0:
            self._phase += WOBBLE_FREQUENCY
            offset_y = self._wobble_amplitude * math.sin(self._phase)
            current_y = self._base_y + offset_y
        else:
            current_y = self._base_y

        if self._anchor_bottomleft:
            self.rect.bottom = int(current_y)
        else:
            self.rect.top = int(current_y)

        # Phase 3: tilt (oscillating rotation)
        if self._tilt_enabled:
            self._tilt_angle = TILT_AMPLITUDE * math.sin(self._phase)
            self.image = pygame.transform.rotate(
                self._base_image, self._tilt_angle
            )
            center = self.rect.center
            self.rect = self.image.get_rect(center=center)
        else:
            self.image = self._base_image

        if self.rect.right < 0:
            self.kill()

    def break_pipe(self) -> None:
        """Break this pipe into particles and remove the pipe sprite."""
        # Spawn a burst of particles from the pipe bounds
        rect = self.rect
        # Use pipe color sampled from the pipe image (approximate)
        try:
            color = self._base_image.get_at((0, 0))
        except Exception:
            color = (80, 180, 80)

        for _ in range(12):
            px = random.randint(rect.left, rect.right)
            py = random.randint(rect.top, rect.bottom)
            vx = random.uniform(-4.0, 4.0) - (scroll_speed * 0.02)
            vy = random.uniform(-6.0, -1.0)
            particle = _Particle(px, py, color, vx, vy)
            particle_group.add(particle)

        # remove pipe
        self.kill()


# ---------------------------------------------------------------------------
# Particle effect for broken pipes
# ---------------------------------------------------------------------------
class _Particle(pygame.sprite.Sprite):
    """Small physics particle used to visualize broken pipe fragments."""

    def __init__(self, x: int, y: int, color: tuple[int, int, int], vx: float, vy: float) -> None:
        super().__init__()
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        try:
            pygame.draw.rect(self.image, color, self.image.get_rect())
        except Exception:
            self.image.fill((120, 200, 120))
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy
        self.life = random.randint(30, 60)

    def update(self) -> None:
        self.vy += GRAVITY * 0.4
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self.life -= 1
        if self.life <= 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ---------------------------------------------------------------------------
# Game Setup
# ---------------------------------------------------------------------------
bird_group: pygame.sprite.Group = pygame.sprite.Group()
pipe_group: pygame.sprite.Group = pygame.sprite.Group()
particle_group: pygame.sprite.Group = pygame.sprite.Group()
flappy: Bird = Bird(100, SCREEN_HEIGHT // 2)
bird_group.add(flappy)

# Font for score and game over (Phase 4)
font_score: pygame.font.Font = pygame.font.SysFont("arial", FONT_SIZE_SCORE, bold=True)
font_game_over: pygame.font.Font = pygame.font.SysFont("arial", FONT_SIZE_GAME_OVER, bold=True)
font_restart: pygame.font.Font = pygame.font.SysFont("arial", FONT_SIZE_RESTART)


def spawn_pipes(
    x: int,
    gap: int,
    gap_center_min: int,
    gap_center_max: int,
    params: DifficultyParams,
) -> None:
    """Spawn a top and bottom pipe pair with a vertical gap.

    Args:
        x: Spawn X position (left edge of pipes).
        gap: Vertical gap between top and bottom pipes.
        gap_center_min: Min Y for gap center.
        gap_center_max: Max Y for gap center.
        params: Current difficulty params (wobble, tilt).
    """
    global next_pair_id

    center_y = random.randint(gap_center_min, gap_center_max)
    top_y = center_y - gap // 2
    bottom_y = center_y + gap // 2
    pair_id = next_pair_id
    next_pair_id += 1
    phase = random.uniform(0, 2 * math.pi)  # Random phase per pair

    top = Pipe(
        x, top_y, PIPE_TOP,
        pair_id, phase,
        params.wobble_amplitude,
        params.wobble_enabled,
        params.tilt_enabled,
    )
    bottom = Pipe(
        x, bottom_y, PIPE_BOTTOM,
        pair_id, phase,
        params.wobble_amplitude,
        params.wobble_enabled,
        params.tilt_enabled,
    )
    pipe_group.add(top)
    pipe_group.add(bottom)


def restart_game(extra_distance: int = 400) -> None:
    """Reset game state and spawn initial pipes."""
    global game_over, flying, pipe_spawn_timer, pipe_spawn_interval
    global score, passed_pair_ids, scroll_speed

    game_over = False
    flying = False
    score = 0
    passed_pair_ids.clear()
    scroll_speed = SCROLL_SPEED_BASE

    flappy.rect.center = (100, SCREEN_HEIGHT // 2)
    flappy.vel = 0.0
    flappy.index = 0
    flappy.counter = 0

    pipe_group.empty()
    pipe_spawn_timer = 0
    params = get_difficulty_params(0)
    lo, hi = params.spawn_interval_range
    pipe_spawn_interval = random.randint(lo, hi)
    spawn_pipes(
        SCREEN_WIDTH + extra_distance,
        params.pipe_gap,
        params.gap_center_min,
        params.gap_center_max,
        params,
    )


def draw_game_over_screen() -> None:
    """Draw semi-transparent overlay with score and restart hint."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(GAME_OVER_OVERLAY_ALPHA)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    text_go = font_game_over.render("Game Over", True, (255, 255, 255))
    text_score = font_score.render(f"Score: {score}", True, (255, 255, 255))
    text_high = font_score.render(f"Best: {high_score}", True, (255, 220, 100))
    text_restart = font_restart.render("Press R to restart", True, (200, 200, 200))

    rect_go = text_go.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
    rect_score = text_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
    rect_high = text_high.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
    rect_restart = text_restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))

    screen.blit(text_go, rect_go)
    screen.blit(text_score, rect_score)
    screen.blit(text_high, rect_high)
    screen.blit(text_restart, rect_restart)

    # Draw a clickable Restart button below the text
    global restart_button_rect
    mouse_pos = pygame.mouse.get_pos()
    btn_center_y = SCREEN_HEIGHT // 2 + 140
    restart_button_rect = pygame.Rect(0, 0, RESTART_BTN_WIDTH, RESTART_BTN_HEIGHT)
    restart_button_rect.center = (SCREEN_WIDTH // 2, btn_center_y)
    hover = restart_button_rect.collidepoint(mouse_pos)
    btn_color = RESTART_BTN_HOVER_COLOR if hover else RESTART_BTN_COLOR
    pygame.draw.rect(screen, btn_color, restart_button_rect, border_radius=8)
    text_btn = font_restart.render("Restart", True, RESTART_BTN_TEXT_COLOR)
    rect_btn = text_btn.get_rect(center=restart_button_rect.center)
    screen.blit(text_btn, rect_btn)


def draw_ability_button() -> None:
    """Draw ability button at the top-right corner and update rect."""
    global ability_button_rect, ability_active

    margin = ABILITY_BTN_MARGIN
    ability_button_rect = pygame.Rect(0, 0, ABILITY_BTN_WIDTH, ABILITY_BTN_HEIGHT)
    ability_button_rect.topright = (SCREEN_WIDTH - margin, margin)
    mouse_pos = pygame.mouse.get_pos()
    hover = ability_button_rect.collidepoint(mouse_pos)

    if ability_active:
        btn_color = ABILITY_BTN_ACTIVE_COLOR
    else:
        btn_color = ABILITY_BTN_HOVER_COLOR if hover else ABILITY_BTN_COLOR

    pygame.draw.rect(screen, btn_color, ability_button_rect, border_radius=8)
    text_btn = font_restart.render("Inv", True, ABILITY_BTN_TEXT_COLOR)
    rect_btn = text_btn.get_rect(center=ability_button_rect.center)
    screen.blit(text_btn, rect_btn)


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------
params_init = get_difficulty_params(0)
spawn_pipes(300, params_init.pipe_gap, params_init.gap_center_min, params_init.gap_center_max, params_init)
run: bool = True

while run:
    clock.tick(FPS)
    screen.blit(bg, (0, 0))

    # Phase 1: update difficulty and scroll speed from score
    params = get_difficulty_params(score)
    scroll_speed = params.scroll_speed

    bird_group.draw(screen)
    bird_group.update()
    pipe_group.draw(screen)
    pipe_group.update()
    # update and draw particles (from broken pipes)
    particle_group.update()
    particle_group.draw(screen)

    # Ability timer: disable after duration
    if ability_active and pygame.time.get_ticks() >= ability_end_time:
        ability_active = False

    # Draw ability button (top-right)
    if not game_over:
        draw_ability_button()

    # Phase 1: score when bird passes a pipe pair
    for pipe in pipe_group.sprites():
        if pipe.pair_id not in passed_pair_ids and flappy.rect.left > pipe.rect.right:
            passed_pair_ids.add(pipe.pair_id)
            score += 1
            high_score = max(high_score, score)

    # Collision: when bird hits any pipe
    collided = pygame.sprite.spritecollide(flappy, pipe_group, False)
    if collided:
        if ability_active:
            for p in collided:
                try:
                    p.break_pipe()
                except Exception:
                    p.kill()
        else:
            game_over = True
            flying = False

    screen.blit(ground_img, (ground_scroll, GROUND_Y))

    # Ground collision
    if flappy.rect.bottom > GROUND_Y:
        game_over = True
        flying = False

    if not game_over:
        ground_scroll -= scroll_speed
        if abs(ground_scroll) > GROUND_TILE_WIDTH:
            ground_scroll = 0

        pipe_spawn_timer += 1
        if pipe_spawn_timer > pipe_spawn_interval:
            spawn_pipes(
                SCREEN_WIDTH + PIPE_SPAWN_OFFSET,
                params.pipe_gap,
                params.gap_center_min,
                params.gap_center_max,
                params,
            )
            pipe_spawn_timer = 0
            lo, hi = params.spawn_interval_range
            pipe_spawn_interval = random.randint(lo, hi)
    else:
        # Phase 4: game over screen
        draw_game_over_screen()

    # Draw score (top-center) when playing
    if not game_over:
        text_score = font_score.render(str(score), True, (255, 255, 255))
        rect_score = text_score.get_rect(midtop=(SCREEN_WIDTH // 2, 20))
        screen.blit(text_score, rect_score)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and not flying
            and not game_over
        ):
            flying = True
        # Ability button click (only while playing)
        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            if ability_button_rect and ability_button_rect.collidepoint(event.pos) and not ability_active:
                ability_active = True
                ability_end_time = pygame.time.get_ticks() + ABILITY_DURATION_MS
        # If we're on the game over screen, clicking the restart button restarts
        if event.type == pygame.MOUSEBUTTONDOWN and game_over:
            if restart_button_rect and restart_button_rect.collidepoint(event.pos):
                restart_game(extra_distance=400)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                restart_game(extra_distance=400)
            if event.key == pygame.K_d:
                candidates = [p for p in pipe_group.sprites() if p.rect.right > 0]
                if candidates:
                    first_x = min(p.rect.x for p in candidates)
                    for p in pipe_group.sprites():
                        if p.rect.x == first_x:
                            p.kill()

    pygame.display.update()

pygame.quit()
