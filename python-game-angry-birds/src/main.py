"""
Angry Birds Clone - Main Game Module
=====================================
A simplified Angry Birds clone using Pygame for rendering and Pymunk for
2D rigid-body physics simulation.

Controls:
    - Mouse drag on sling area to launch birds.
    - 'S' key: Activate zero-gravity mode.
    - 'N' key: Restore normal gravity.
    - 'W' key: Toggle right-side wall on/off.
    - 'ESC' key: Quit the game.

Game Flow:
    1. Player drags and releases a bird from the slingshot.
    2. The bird flies following physics simulation (gravity, collisions).
    3. Destroying pigs and wooden structures earns points.
    4. The level is cleared when all pigs are eliminated.
    5. The level fails if all birds are used and pigs remain after a timeout.

Updated for Python 3.12+ and Pymunk 7.x / Pygame 2.6.x compatibility.
"""

import os
import sys
import math
import time

import pygame
import pymunk as pm

# Import custom game modules
from characters import Bird
from level import Level

# ---------------------------------------------------------------------------
# Resource Path Helper
# ---------------------------------------------------------------------------
# Resolve all resource paths relative to this script's directory so that
# the game works regardless of the current working directory.
_SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
_RESOURCE_DIR: str = os.path.join(_SCRIPT_DIR, "..", "resources")


def _res(relative_path: str) -> str:
    """Build an absolute path to a resource file.

    Args:
        relative_path: Path relative to the resources/ directory
                       (e.g. "images/red-bird3.png").

    Returns:
        The absolute file-system path to the resource.
    """
    return os.path.join(_RESOURCE_DIR, relative_path)


# ---------------------------------------------------------------------------
# Pygame Initialization
# ---------------------------------------------------------------------------
pygame.init()

# Set up the game display window (1200 x 650 pixels)
screen: pygame.Surface = pygame.display.set_mode((1200, 650))

# ---------------------------------------------------------------------------
# Load Image Assets
# ---------------------------------------------------------------------------
# Bird sprite used for both slingshot and in-flight rendering
redbird: pygame.Surface = pygame.image.load(
    _res("images/red-bird3.png")
).convert_alpha()

# Parallax-scrollable background image
background2: pygame.Surface = pygame.image.load(
    _res("images/background3.png")
).convert_alpha()

# Slingshot image split into front and back layers for depth effect
sling_image: pygame.Surface = pygame.image.load(
    _res("images/sling-3.png")
).convert_alpha()

# Full sprite sheet containing various game element sprites
full_sprite: pygame.Surface = pygame.image.load(
    _res("images/full-sprite.png")
).convert_alpha()

# Crop a 50x50 pig sprite from the full sprite sheet, then scale to 30x30
rect = pygame.Rect(181, 1050, 50, 50)
cropped: pygame.Surface = full_sprite.subsurface(rect).copy()
pig_image: pygame.Surface = pygame.transform.scale(cropped, (30, 30))

# UI buttons sprite sheet (pause, replay, next, play)
buttons: pygame.Surface = pygame.image.load(
    _res("images/selected-buttons.png")
).convert_alpha()

# Pig image shown on the "level failed" screen
pig_happy: pygame.Surface = pygame.image.load(
    _res("images/pig_failed.png")
).convert_alpha()

# Star rating images for the "level cleared" screen
stars: pygame.Surface = pygame.image.load(
    _res("images/stars-edited.png")
).convert_alpha()

# Extract individual star images from the combined star sprite sheet
rect = pygame.Rect(0, 0, 200, 200)
star1: pygame.Surface = stars.subsurface(rect).copy()       # 1-star rating
rect = pygame.Rect(204, 0, 200, 200)
star2: pygame.Surface = stars.subsurface(rect).copy()       # 2-star rating
rect = pygame.Rect(426, 0, 200, 200)
star3: pygame.Surface = stars.subsurface(rect).copy()       # 3-star rating

# Extract individual UI button images from the buttons sprite sheet
rect = pygame.Rect(164, 10, 60, 60)
pause_button: pygame.Surface = buttons.subsurface(rect).copy()
rect = pygame.Rect(24, 4, 100, 100)
replay_button: pygame.Surface = buttons.subsurface(rect).copy()
rect = pygame.Rect(142, 365, 130, 100)
next_button: pygame.Surface = buttons.subsurface(rect).copy()
rect = pygame.Rect(18, 212, 100, 100)
play_button: pygame.Surface = buttons.subsurface(rect).copy()

# ---------------------------------------------------------------------------
# Game Clock & State Variables
# ---------------------------------------------------------------------------
clock: pygame.time.Clock = pygame.time.Clock()
running: bool = True  # Main game loop flag

# ---------------------------------------------------------------------------
# Pymunk Physics Space Setup
# ---------------------------------------------------------------------------
# Create the physics simulation space with downward gravity
space: pm.Space = pm.Space()
space.gravity = (0.0, -700.0)  # Gravity pointing downward (pymunk Y-axis)

# ---------------------------------------------------------------------------
# Game Object Lists
# ---------------------------------------------------------------------------
# These lists hold references to game objects for rendering and collision
pigs: list = []       # Active pig characters in the level
birds: list = []      # Birds currently in flight (launched)
balls: list = []      # Unused; reserved for future use
polys: list = []      # Unused; reserved for future use
beams: list = []      # Horizontal wooden beams in the level
columns: list = []    # Vertical wooden columns in the level
poly_points: list = []  # Unused; reserved for polygon vertex storage

# ---------------------------------------------------------------------------
# Slingshot & Input State Variables
# ---------------------------------------------------------------------------
ball_number: int = 0           # Unused; reserved for future use
polys_dict: dict = {}          # Unused; reserved for future use
mouse_distance: float = 0     # Distance from mouse to sling anchor
rope_lenght: int = 90         # Maximum sling rope stretch length (pixels)
angle: float = 0              # Launch angle (radians) calculated from sling
x_mouse: int = 0              # Current mouse X position
y_mouse: int = 0              # Current mouse Y position
count: int = 0                # Frame counter for bird trail dots
mouse_pressed: bool = False   # Whether the mouse is being held in sling area
t1: float = 0                 # Timestamp (ms) of the last bird launch
tick_to_next_circle: int = 10  # Unused; reserved for future use

# ---------------------------------------------------------------------------
# Color Constants (RGB tuples)
# ---------------------------------------------------------------------------
RED: tuple = (255, 0, 0)
BLUE: tuple = (0, 0, 255)
BLACK: tuple = (0, 0, 0)
WHITE: tuple = (255, 255, 255)

# ---------------------------------------------------------------------------
# Slingshot Anchor Positions (screen coordinates)
# ---------------------------------------------------------------------------
# Two anchor points form the Y-shaped sling; birds are pulled between them
sling_x, sling_y = 135, 450   # Left/back arm of the sling
sling2_x, sling2_y = 160, 450  # Right/front arm of the sling

# Trajectory: must match Bird exactly (spawn, mass, power factor)
# Gravity is read from space at runtime so zero-g mode works correctly
BIRD_SPAWN_X_PYMUNK: float = 154.0
BIRD_SPAWN_Y_PYMUNK: float = 156.0
BIRD_MASS: float = 5.0
BIRD_RADIUS: float = 12.0
POWER_FACTOR: float = 53.0
# Trajectory: use same physics step as game (dt=0.01, 2 substeps per frame)
AIM_PHYSICS_DT: float = 0.01  # Matches space.step(dt)
AIM_TRAJECTORY_MAX_T: float = 1.5
# Drawing (trajectory as dots): half the dots, gradient colors
AIM_DOT_SKIP: int = 4  # Draw every Nth point (2 = half the dots)
AIM_DOT_COLORS: list[tuple[int, int, int]] = [
    (255, 220, 80),   # Yellow (near bird)
    (255, 150, 50),   # Orange
    (255, 80, 120),   # Pink
    (100, 200, 255),  # Cyan
    (120, 255, 180),  # Mint
]
AIM_DOT_OUTLINE_COLOR: tuple = (40, 40, 60)
AIM_DOT_RADIUS: int = 5
AIM_DOT_OUTLINE_WIDTH: int = 1

# ---------------------------------------------------------------------------
# Scoring & Game State
# ---------------------------------------------------------------------------
score: int = 0           # Player's current score
game_state: int = 0      # 0=playing, 1=paused, 3=failed, 4=cleared
bird_path: list = []     # Trail points left by launched birds
counter: int = 0         # Frame counter for adding trail dots
restart_counter: bool = False   # Flag to reset the trail counter
bonus_score_once: bool = True   # Ensure bonus points are awarded only once

# ---------------------------------------------------------------------------
# Font Setup for UI Text
# ---------------------------------------------------------------------------
bold_font: pygame.font.Font = pygame.font.SysFont("arial", 30, bold=True)
bold_font2: pygame.font.Font = pygame.font.SysFont("arial", 40, bold=True)
bold_font3: pygame.font.Font = pygame.font.SysFont("arial", 50, bold=True)

# ---------------------------------------------------------------------------
# Wall Toggle State
# ---------------------------------------------------------------------------
wall: bool = True  # Whether the right-side wall is active

# ---------------------------------------------------------------------------
# Static Physics Bodies (Floor & Wall)
# ---------------------------------------------------------------------------
# A single static body shared by all static line segments
static_body: pm.Body = pm.Body(body_type=pm.Body.STATIC)

# Floor: horizontal line at y=60 spanning the full screen width
static_lines: list = [
    pm.Segment(static_body, (0.0, 60.0), (1200.0, 60.0), 0.0)
]

# Right wall: vertical line from floor to top (only active when wall=True)
static_lines1: list = [
    pm.Segment(static_body, (1200.0, 60.0), (1200.0, 800.0), 0.0)
]

# Configure physics properties for the floor segment
for line in static_lines:
    line.elasticity = 0.95    # High bounce factor
    line.friction = 1         # Full friction
    line.collision_type = 3   # Type 3 = static environment (no handler needed)

# Configure physics properties for the wall segment
for line in static_lines1:
    line.elasticity = 0.95
    line.friction = 1
    line.collision_type = 3

# Add the static body, floor, and right-side wall to the physics space
# Right wall prevents birds and pigs from going off-screen to the right
space.add(static_body)
for line in static_lines:
    space.add(line)
for line in static_lines1:
    space.add(line)


# ===========================================================================
# Utility Functions
# ===========================================================================

def to_pygame(p: pm.Vec2d) -> tuple[int, int]:
    """Convert pymunk physics coordinates to pygame screen coordinates.

    Pymunk uses a coordinate system where Y increases upward,
    while Pygame's Y increases downward. This function flips the Y axis
    and offsets by 600 (the approximate screen height minus border).

    Args:
        p: A pymunk Vec2d position vector.

    Returns:
        A (x, y) tuple in pygame screen coordinates.
    """
    return int(p.x), int(-p.y + 600)


def vector(p0: tuple, p1: tuple) -> tuple[float, float]:
    """Calculate the direction vector from point p0 to point p1.

    Args:
        p0: Starting point as (x0, y0).
        p1: Ending point as (x1, y1).

    Returns:
        A tuple (dx, dy) representing the direction vector.
    """
    a = p1[0] - p0[0]
    b = p1[1] - p0[1]
    return (a, b)


def unit_vector(v: tuple[float, float]) -> tuple[float, float]:
    """Normalize a 2D vector to unit length.

    Args:
        v: A 2D vector as (a, b).

    Returns:
        The unit vector (ua, ub) with length 1.
        If the input vector has zero length, returns a near-zero result
        to avoid division by zero.
    """
    h = ((v[0] ** 2) + (v[1] ** 2)) ** 0.5
    if h == 0:
        h = 0.000000000000001  # Prevent division by zero
    ua = v[0] / h
    ub = v[1] / h
    return (ua, ub)


def distance(xo: float, yo: float, x: float, y: float) -> float:
    """Calculate the Euclidean distance between two points.

    Args:
        xo: X coordinate of the first point.
        yo: Y coordinate of the first point.
        x: X coordinate of the second point.
        y: Y coordinate of the second point.

    Returns:
        The straight-line distance between the two points.
    """
    dx = x - xo
    dy = y - yo
    d = ((dx ** 2) + (dy ** 2)) ** 0.5
    return d


def compute_trajectory_points(
    launch_distance: float,
    angle: float,
    gravity: tuple[float, float],
) -> list[tuple[int, int]]:
    """Compute trajectory using pymunk physics for accurate match with actual flight.

    Creates a temporary space with the same gravity, spawns a body with the exact
    Bird impulse, steps the simulation, and records positions. This ensures the
    preview matches the real trajectory (including zero-gravity mode).

    Args:
        launch_distance: Signed pull distance (positive = pull left, negative = right).
        angle: Launch angle in radians (from sling, same as passed to Bird).
        gravity: Current space.gravity (x, y) so zero-g mode is respected.

    Returns:
        List of (screen_x, screen_y) coordinates along the predicted path.
    """
    # Create a minimal temp space with same gravity (no obstacles)
    temp_space = pm.Space()
    temp_space.gravity = gravity

    # Match Bird exactly: mass, radius, inertia, spawn, impulse
    inertia = pm.moment_for_circle(BIRD_MASS, 0, BIRD_RADIUS, (0, 0))
    body = pm.Body(BIRD_MASS, inertia)
    body.position = BIRD_SPAWN_X_PYMUNK, BIRD_SPAWN_Y_PYMUNK
    power = launch_distance * POWER_FACTOR
    impulse = power * pm.Vec2d(1, 0).rotated(-angle)
    body.apply_impulse_at_local_point(impulse)

    shape = pm.Circle(body, BIRD_RADIUS, (0, 0))
    temp_space.add(body, shape)

    points_screen: list[tuple[int, int]] = []
    t = 0.0
    while t <= AIM_TRAJECTORY_MAX_T:
        if body.position.y < 0:
            break
        sx, sy = to_pygame(body.position)
        points_screen.append((int(sx), int(sy)))
        temp_space.step(AIM_PHYSICS_DT)
        t += AIM_PHYSICS_DT
    # Keep full path for accuracy; caller may downsample for drawing
    return points_screen


def draw_trajectory_curve(points: list[tuple[int, int]]) -> None:
    """Draw the trajectory as colorful dots; show every Nth point to reduce count."""
    # Half the dots: use every 2nd point (trajectory still matches real motion)
    drawn = points[::AIM_DOT_SKIP]
    n = len(drawn)
    for i, (x, y) in enumerate(drawn):
        # Gradient through bright colors along the path
        color_idx = int((i / max(n - 1, 1)) * (len(AIM_DOT_COLORS) - 1) + 0.5)
        color = AIM_DOT_COLORS[min(color_idx, len(AIM_DOT_COLORS) - 1)]
        pygame.draw.circle(
            screen, AIM_DOT_OUTLINE_COLOR, (x, y),
            AIM_DOT_RADIUS + AIM_DOT_OUTLINE_WIDTH, AIM_DOT_OUTLINE_WIDTH
        )
        pygame.draw.circle(screen, color, (x, y), AIM_DOT_RADIUS)


def load_music() -> None:
    """Load and play the background music in an infinite loop.

    The music file is loaded from the resources/sounds directory.
    The -1 argument to play() means the music loops indefinitely.
    """
    song1 = _res('sounds/angry-birds.ogg')
    pygame.mixer.music.load(song1)
    pygame.mixer.music.play(-1)


def sling_action() -> None:
    """Handle the slingshot aiming and drawing while the mouse is held.

    This function:
    1. Calculates the direction and distance from the sling anchor to the mouse.
    2. Clamps the bird position to the maximum rope length if over-stretched.
    3. Draws the sling ropes (two lines) and the bird sprite at the pull position.
    4. Computes the launch angle for when the bird is released.

    Uses global variables for mouse state and sling configuration.
    """
    global mouse_distance
    global rope_lenght
    global angle
    global x_mouse
    global y_mouse

    # Calculate the vector from sling anchor to mouse position
    v = vector((sling_x, sling_y), (x_mouse, y_mouse))
    uv = unit_vector(v)
    uv1 = uv[0]  # X component of unit vector
    uv2 = uv[1]  # Y component of unit vector
    mouse_distance = distance(sling_x, sling_y, x_mouse, y_mouse)
    is_clamped = mouse_distance > rope_lenght  # Check before any modification

    # Position along the rope at maximum stretch
    pu = (uv1 * rope_lenght + sling_x, uv2 * rope_lenght + sling_y)
    bigger_rope = 102  # Extended rope length for visual line drawing

    # Bird sprite offset (center the 40x40 sprite)
    x_redbird = x_mouse - 20
    y_redbird = y_mouse - 20

    if is_clamped:
        # Mouse is beyond max rope length: clamp bird to rope end
        pux, puy = pu
        pux -= 20  # Center the sprite horizontally
        puy -= 20  # Center the sprite vertically
        pul = pux, puy
        screen.blit(redbird, pul)
        # Draw the extended rope from the sling arms to the clamped position
        pu2 = (uv1 * bigger_rope + sling_x, uv2 * bigger_rope + sling_y)
        pygame.draw.line(screen, (0, 0, 0), (sling2_x, sling2_y), pu2, 5)
        screen.blit(redbird, pul)
        pygame.draw.line(screen, (0, 0, 0), (sling_x, sling_y), pu2, 5)
    else:
        # Mouse is within rope length: bird follows the mouse
        mouse_distance += 10  # Slight offset for visual rope end
        pu3 = (uv1 * mouse_distance + sling_x, uv2 * mouse_distance + sling_y)
        pygame.draw.line(screen, (0, 0, 0), (sling2_x, sling2_y), pu3, 5)
        screen.blit(redbird, (x_redbird, y_redbird))
        pygame.draw.line(screen, (0, 0, 0), (sling_x, sling_y), pu3, 5)

    # Calculate the launch angle using arctangent of the pull direction
    dy = y_mouse - sling_y
    dx = x_mouse - sling_x
    if dx == 0:
        dx = 0.00000000000001  # Avoid division by zero
    angle = math.atan((float(dy)) / dx)

    # Parabolic trajectory: same effective distance and sign as when Bird is launched
    launch_distance = min(mouse_distance, rope_lenght)
    if x_mouse >= sling_x + 5:
        launch_distance = -launch_distance
    trajectory_points = compute_trajectory_points(
        launch_distance, angle, space.gravity
    )

    # Align trajectory start with bird's visual center (trajectory uses spawn 154,156 in pymunk)
    bird_center_x = pu[0] if is_clamped else x_mouse
    bird_center_y = pu[1] if is_clamped else y_mouse
    trajectory_start_screen = to_pygame(pm.Vec2d(BIRD_SPAWN_X_PYMUNK, BIRD_SPAWN_Y_PYMUNK))
    offset_x = bird_center_x - trajectory_start_screen[0]
    offset_y = bird_center_y - trajectory_start_screen[1]
    trajectory_points = [(int(x + offset_x), int(y + offset_y)) for x, y in trajectory_points]

    draw_trajectory_curve(trajectory_points)


def draw_level_cleared() -> None:
    """Render the 'Level Cleared' overlay screen.

    Displays:
    - "Level Cleared!" title text.
    - Star rating (1, 2, or 3 stars) based on score thresholds.
    - The final score.
    - Replay and Next level buttons.

    Also awards bonus points for remaining unused birds (once only).
    """
    global game_state
    global bonus_score_once
    global score

    level_cleared = bold_font3.render("Level Cleared!", 1, WHITE)
    score_level_cleared = bold_font2.render(str(score), 1, WHITE)

    if level.number_of_birds >= 0 and len(pigs) == 0:
        # Award bonus score for remaining birds (10,000 per unused bird)
        if bonus_score_once:
            score += (level.number_of_birds - 1) * 10000
        bonus_score_once = False
        game_state = 4  # Set state to "level cleared"

        # Draw semi-transparent overlay panel
        rect = pygame.Rect(300, 0, 600, 800)
        pygame.draw.rect(screen, BLACK, rect)
        screen.blit(level_cleared, (450, 90))

        # Display star rating based on score thresholds
        if score >= level.one_star and score <= level.two_star:
            screen.blit(star1, (310, 190))  # 1 star
        if score >= level.two_star and score <= level.three_star:
            screen.blit(star1, (310, 190))  # 2 stars
            screen.blit(star2, (500, 170))
        if score >= level.three_star:
            screen.blit(star1, (310, 190))  # 3 stars
            screen.blit(star2, (500, 170))
            screen.blit(star3, (700, 200))

        # Display score and action buttons
        screen.blit(score_level_cleared, (550, 400))
        screen.blit(replay_button, (510, 480))
        screen.blit(next_button, (620, 480))


def draw_level_failed() -> None:
    """Render the 'Level Failed' overlay screen.

    Shown when all birds have been used and pigs still remain
    after a 5-second timeout. Displays:
    - "Level Failed" title text.
    - A sad/happy pig image.
    - Replay button.
    """
    global game_state

    failed = bold_font3.render("Level Failed", 1, WHITE)

    # Check failure conditions: no birds left, 5 seconds elapsed, pigs remain
    if level.number_of_birds <= 0 and time.time() - t2 > 5 and len(pigs) > 0:
        game_state = 3  # Set state to "level failed"

        # Draw overlay panel
        rect = pygame.Rect(300, 0, 600, 800)
        pygame.draw.rect(screen, BLACK, rect)
        screen.blit(failed, (450, 90))
        screen.blit(pig_happy, (380, 120))
        screen.blit(replay_button, (520, 460))


def restart() -> None:
    """Remove all dynamic game objects from the physics space.

    Clears pigs, birds, columns, and beams from both the pymunk space
    and the game's tracking lists. Called when restarting or changing levels.
    """
    # Build removal lists to avoid modifying lists during iteration
    pigs_to_remove = []
    birds_to_remove = []
    columns_to_remove = []
    beams_to_remove = []

    for pig in pigs:
        pigs_to_remove.append(pig)
    for pig in pigs_to_remove:
        space.remove(pig.shape, pig.shape.body)
        pigs.remove(pig)

    for bird in birds:
        birds_to_remove.append(bird)
    for bird in birds_to_remove:
        space.remove(bird.shape, bird.shape.body)
        birds.remove(bird)

    for column in columns:
        columns_to_remove.append(column)
    for column in columns_to_remove:
        space.remove(column.shape, column.shape.body)
        columns.remove(column)

    for beam in beams:
        beams_to_remove.append(beam)
    for beam in beams_to_remove:
        space.remove(beam.shape, beam.shape.body)
        beams.remove(beam)


# ===========================================================================
# Collision Handler Callbacks
# ===========================================================================
# Pymunk calls these functions when specific shape types collide.
# Collision types: 0 = Bird, 1 = Pig, 2 = Wood, 3 = Static environment

def post_solve_bird_pig(arbiter, space, _) -> None:
    """Handle collision aftermath between a bird and a pig.

    When a bird hits a pig, the pig is immediately destroyed and
    the player earns 10,000 points per pig eliminated.

    Args:
        arbiter: Pymunk Arbiter containing collision data.
        space: The pymunk Space (unused, kept for callback signature).
        _: User data (unused, kept for callback signature).
    """
    surface = screen
    a, b = arbiter.shapes
    bird_body = a.body
    pig_body = b.body

    # Draw collision debug circles at impact positions
    p = to_pygame(bird_body.position)
    p2 = to_pygame(pig_body.position)
    r = 30
    pygame.draw.circle(surface, BLACK, p, r, 4)
    pygame.draw.circle(surface, RED, p2, r, 4)

    # Find and remove the pig that was hit
    pigs_to_remove = []
    for pig in pigs:
        if pig_body == pig.body:
            pig.life -= 20
            pigs_to_remove.append(pig)
            global score
            score += 10000  # Award points for destroying a pig

    for pig in pigs_to_remove:
        space.remove(pig.shape, pig.shape.body)
        pigs.remove(pig)


def post_solve_bird_wood(arbiter, space, _) -> None:
    """Handle collision aftermath between a bird and a wooden structure.

    Wooden beams and columns are destroyed only if the collision impulse
    exceeds a threshold of 1100 units. Each destroyed piece earns 5,000 points.

    Args:
        arbiter: Pymunk Arbiter containing collision data and impulse info.
        space: The pymunk Space.
        _: User data (unused).
    """
    poly_to_remove = []

    # Only destroy wood if the impact is strong enough
    if arbiter.total_impulse.length > 1100:
        a, b = arbiter.shapes  # a = bird shape, b = wood shape

        # Check if the impacted shape belongs to a column or beam
        for column in columns:
            if b == column.shape:
                poly_to_remove.append(column)
        for beam in beams:
            if b == beam.shape:
                poly_to_remove.append(beam)

        # Remove from game tracking lists
        for poly in poly_to_remove:
            if poly in columns:
                columns.remove(poly)
            if poly in beams:
                beams.remove(poly)

        # Remove the wood shape and its body from physics space
        space.remove(b, b.body)
        global score
        score += 5000  # Award points for destroying wood


def post_solve_pig_wood(arbiter, space, _) -> None:
    """Handle collision aftermath between a pig and a wooden structure.

    When falling wood hits a pig with sufficient force (impulse > 700),
    the pig takes damage. If the pig's life reaches 0, it is destroyed
    and the player earns 10,000 points.

    Args:
        arbiter: Pymunk Arbiter containing collision data and impulse info.
        space: The pymunk Space.
        _: User data (unused).
    """
    pigs_to_remove = []

    # Only damage pigs if the impact force exceeds the threshold
    if arbiter.total_impulse.length > 700:
        pig_shape, wood_shape = arbiter.shapes

        for pig in pigs:
            if pig_shape == pig.shape:
                pig.life -= 20  # Reduce pig health
                global score
                score += 10000
                if pig.life <= 0:
                    pigs_to_remove.append(pig)

    # Remove dead pigs from the space and game lists
    for pig in pigs_to_remove:
        space.remove(pig.shape, pig.shape.body)
        pigs.remove(pig)


# ===========================================================================
# Register Collision Handlers with Pymunk 7.x API
# ===========================================================================
# In Pymunk 7.0+, use space.on_collision() instead of the removed
# space.add_collision_handler().post_solve pattern.
# Collision type pairs: (Bird=0, Pig=1), (Bird=0, Wood=2), (Pig=1, Wood=2)

space.on_collision(0, 1, post_solve=post_solve_bird_pig)    # Bird vs Pig
space.on_collision(0, 2, post_solve=post_solve_bird_wood)   # Bird vs Wood
space.on_collision(1, 2, post_solve=post_solve_pig_wood)    # Pig vs Wood

# ---------------------------------------------------------------------------
# Start Background Music & Load First Level
# ---------------------------------------------------------------------------
load_music()
level: Level = Level(pigs, columns, beams, space)
level.number = 0    # Start at level 0
level.load_level()  # Build the initial level layout

# ===========================================================================
# Main Game Loop
# ===========================================================================
while running:
    # -------------------------------------------------------------------
    # Event Handling (Input Processing)
    # -------------------------------------------------------------------
    for event in pygame.event.get():
        # Quit events
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        # Toggle right-side wall with 'W' key
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_w:
            if wall:
                # Remove wall segments from physics space
                for line in static_lines1:
                    space.remove(line)
                wall = False
            else:
                # Add wall segments to physics space
                for line in static_lines1:
                    space.add(line)
                wall = True

        # Zero gravity mode with 'S' key
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_s:
            space.gravity = (0.0, -10.0)   # Near-zero gravity
            level.bool_space = True

        # Normal gravity mode with 'N' key
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_n:
            space.gravity = (0.0, -700.0)  # Standard game gravity
            level.bool_space = False

        # Detect mouse press in the slingshot interaction area
        if (pygame.mouse.get_pressed()[0] and x_mouse > 100 and
                x_mouse < 250 and y_mouse > 370 and y_mouse < 550):
            mouse_pressed = True

        # Mouse release: launch the bird from the slingshot
        if (event.type == pygame.MOUSEBUTTONUP and
                event.button == 1 and mouse_pressed):
            mouse_pressed = False

            if level.number_of_birds > 0:
                level.number_of_birds -= 1
                t1 = time.time() * 1000  # Record launch time in ms

                # Bird spawn position (near the sling anchor in pymunk coords)
                xo = 154
                yo = 156

                # Clamp the pull distance to the max rope length
                if mouse_distance > rope_lenght:
                    mouse_distance = rope_lenght

                # Determine launch direction based on mouse position
                # relative to the sling anchor
                if x_mouse < sling_x + 5:
                    bird = Bird(mouse_distance, angle, xo, yo, space)
                    birds.append(bird)
                else:
                    bird = Bird(-mouse_distance, angle, xo, yo, space)
                    birds.append(bird)

                # Record time when the last bird is launched (for fail timeout)
                if level.number_of_birds == 0:
                    t2 = time.time()

        # Handle UI button clicks
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # Pause button (top-left corner)
            if (x_mouse < 60 and y_mouse < 155 and y_mouse > 90):
                game_state = 1  # Enter paused state

            if game_state == 1:
                # Resume button in the paused screen
                if x_mouse > 500 and y_mouse > 200 and y_mouse < 300:
                    game_state = 0
                # Restart button in the paused screen
                if x_mouse > 500 and y_mouse > 300:
                    restart()
                    level.load_level()
                    game_state = 0
                    bird_path = []

            if game_state == 3:
                # Replay button in the "level failed" screen
                if x_mouse > 500 and x_mouse < 620 and y_mouse > 450:
                    restart()
                    level.load_level()
                    game_state = 0
                    bird_path = []
                    score = 0

            if game_state == 4:
                # Next level button in the "level cleared" screen
                if x_mouse > 610 and y_mouse > 450:
                    restart()
                    level.number += 1
                    game_state = 0
                    level.load_level()
                    score = 0
                    bird_path = []
                    bonus_score_once = True

                # Replay button in the "level cleared" screen
                if x_mouse < 610 and x_mouse > 500 and y_mouse > 450:
                    restart()
                    level.load_level()
                    game_state = 0
                    bird_path = []
                    score = 0

    # Update mouse position each frame
    x_mouse, y_mouse = pygame.mouse.get_pos()

    # -------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------

    # Draw background (green fill + sky/landscape image)
    screen.fill((130, 200, 100))
    screen.blit(background2, (0, -50))

    # Draw the back layer of the slingshot (behind the bird)
    rect = pygame.Rect(50, 0, 70, 220)
    screen.blit(sling_image, (138, 420), rect)

    # Draw the trajectory trail left by launched birds
    for point in bird_path:
        pygame.draw.circle(screen, WHITE, point, 5, 0)

    # Draw remaining birds in the queue (waiting to be launched)
    if level.number_of_birds > 0:
        for i in range(level.number_of_birds - 1):
            x = 100 - (i * 35)  # Space birds out to the left
            screen.blit(redbird, (x, 508))

    # Draw sling interaction or idle bird on sling
    if mouse_pressed and level.number_of_birds > 0:
        # Player is aiming: render sling pull animation
        sling_action()
    else:
        # No interaction: show bird resting on sling or just the rope
        if time.time() * 1000 - t1 > 300 and level.number_of_birds > 0:
            # Show a bird sitting on the sling (after launch cooldown)
            screen.blit(redbird, (130, 426))
        else:
            # Draw the sling rope without a bird (just after launch)
            pygame.draw.line(screen, (0, 0, 0), (sling_x, sling_y - 8),
                             (sling2_x, sling2_y - 7), 5)

    # -------------------------------------------------------------------
    # Update & Draw Active Birds
    # -------------------------------------------------------------------
    birds_to_remove = []
    pigs_to_remove = []
    counter += 1

    for bird in birds:
        # Remove birds that fall below the ground
        if bird.shape.body.position.y < 0:
            birds_to_remove.append(bird)

        # Convert physics position to screen coordinates and draw
        p = to_pygame(bird.shape.body.position)
        x, y = p
        x -= 22  # Offset sprite to center on physics body
        y -= 20
        screen.blit(redbird, (x, y))

        # Draw a debug circle around the bird (collision radius)
        pygame.draw.circle(screen, BLUE, p, int(bird.shape.radius), 2)

        # Record bird position for trail rendering (every 3 frames)
        if counter >= 3 and time.time() - t1 < 5:
            bird_path.append(p)
            restart_counter = True

    if restart_counter:
        counter = 0
        restart_counter = False

    # Remove out-of-bounds birds and pigs from the physics space
    for bird in birds_to_remove:
        space.remove(bird.shape, bird.shape.body)
        birds.remove(bird)
    for pig in pigs_to_remove:
        space.remove(pig.shape, pig.shape.body)
        pigs.remove(pig)

    # -------------------------------------------------------------------
    # Draw Static Physics Lines (Floor)
    # -------------------------------------------------------------------
    for line in static_lines:
        body = line.body
        # Calculate world-space positions for the line segment endpoints
        pv1 = body.position + line.a.rotated(body.angle)
        pv2 = body.position + line.b.rotated(body.angle)
        p1 = to_pygame(pv1)
        p2 = to_pygame(pv2)
        pygame.draw.lines(screen, (150, 150, 150), False, [p1, p2])

    # -------------------------------------------------------------------
    # Draw Pigs
    # -------------------------------------------------------------------
    i = 0
    for pig in pigs:
        i += 1
        pig = pig.shape  # Access the pymunk shape for position/rotation

        # Remove pigs that fall below the ground
        if pig.body.position.y < 0:
            pigs_to_remove.append(pig)

        # Convert physics position to screen coordinates
        p = to_pygame(pig.body.position)
        x, y = p

        # Rotate the pig image to match the physics body rotation
        angle_degrees = math.degrees(pig.body.angle)
        img = pygame.transform.rotate(pig_image, angle_degrees)
        w, h = img.get_size()
        x -= w * 0.5  # Center the rotated sprite
        y -= h * 0.5
        screen.blit(img, (x, y))

        # Draw a debug circle around the pig (collision radius)
        pygame.draw.circle(screen, BLUE, p, int(pig.radius), 2)

    # -------------------------------------------------------------------
    # Draw Wooden Structures (Columns & Beams)
    # -------------------------------------------------------------------
    for column in columns:
        column.draw_poly('columns', screen)
    for beam in beams:
        beam.draw_poly('beams', screen)

    # -------------------------------------------------------------------
    # Physics Step (Two sub-steps per frame for stability)
    # -------------------------------------------------------------------
    dt = 1.0 / 50.0 / 2.0  # Half of a 50 FPS frame duration
    for x in range(2):
        space.step(dt)  # Two updates per frame for better simulation stability

    # -------------------------------------------------------------------
    # Draw Front Layer of Slingshot (in front of the bird)
    # -------------------------------------------------------------------
    rect = pygame.Rect(0, 0, 60, 200)
    screen.blit(sling_image, (120, 420), rect)

    # -------------------------------------------------------------------
    # Draw Score & UI Elements
    # -------------------------------------------------------------------
    score_font = bold_font.render("SCORE", 1, WHITE)
    number_font = bold_font.render(str(score), 1, WHITE)
    screen.blit(score_font, (1060, 90))

    # Adjust score number position based on digit count
    if score == 0:
        screen.blit(number_font, (1100, 130))
    else:
        screen.blit(number_font, (1060, 130))

    # Draw pause button in the top-left corner
    screen.blit(pause_button, (10, 90))

    # -------------------------------------------------------------------
    # Draw Overlay Screens (Pause / Cleared / Failed)
    # -------------------------------------------------------------------
    if game_state == 1:
        # Paused: show resume and replay buttons
        screen.blit(play_button, (500, 200))
        screen.blit(replay_button, (500, 300))

    draw_level_cleared()  # Check and draw "level cleared" overlay
    draw_level_failed()   # Check and draw "level failed" overlay

    # -------------------------------------------------------------------
    # Flip Display & Cap Frame Rate
    # -------------------------------------------------------------------
    pygame.display.flip()
    clock.tick(50)  # Target 50 FPS
    pygame.display.set_caption("fps: " + str(clock.get_fps()))
