"""Spike Troll — display and tuning constants."""

TITLE = "Spike Troll"
SCREEN_W = 800
SCREEN_H = 480
FPS = 60

# Physics
GRAVITY = 2200.0
MOVE_SPEED = 260.0
JUMP_VEL = -620.0
PLAYER_W = 28
PLAYER_H = 36
# Forgive slightly late jumps / early taps
COYOTE_MS = 100
JUMP_BUFFER_MS = 140
FEET_PROBE = 4  # px below feet to detect ground

# Colors
BG = (24, 28, 40)
FLOOR = (60, 70, 90)
PLATFORM = (80, 95, 120)
PLAYER = (90, 180, 255)
EXIT_C = (80, 220, 120)
SPIKE = (220, 60, 70)
WARNING = (255, 200, 60)
TEXT = (230, 235, 245)
HUD = (180, 190, 210)

# Spike stays after becoming lethal
SPIKE_LIFE_MS = 4500

MAX_LEVEL = 10

# Spawn interval (ms): easy → brutal, floor at 750 so still human-beatable
LEVEL_SPAWN_MS = (
    3400,  # 1 tutorial
    3000,  # 2
    2600,  # 3
    2200,  # 4
    1900,  # 5
    1600,  # 6
    1350,  # 7
    1100,  # 8
    900,   # 9
    750,   # 10 "impossible" (still fair)
)

# Warning flash before lethal — never under 400ms
LEVEL_WARNING_MS = (
    900,
    850,
    800,
    750,
    700,
    650,
    600,
    550,
    480,
    400,
)

# How many spikes try to spawn each tick (later levels = more chaos)
LEVEL_SPIKE_BURST = (1, 1, 1, 1, 1, 1, 2, 2, 2, 2)

LEVEL_NAMES = (
    "Warmup",
    "Stroll",
    "Hop",
    "Climb",
    "Zigzag",
    "Narrow",
    "Gauntlet",
    "Pressure",
    "Nightmare",
    "Almost Impossible",
)
