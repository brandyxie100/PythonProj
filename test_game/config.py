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

# Spike troll: warning then lethal
WARNING_MS = 700
SPIKE_LIFE_MS = 4500  # how long a spike stays after appearing

# Per-level spawn interval (ms) — meaner each room
LEVEL_SPAWN_MS = (2800, 1900, 1200)
MAX_LEVEL = 3
