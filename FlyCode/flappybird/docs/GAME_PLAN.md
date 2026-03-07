# Flappy Bird — Infinite Game with Escalating Difficulty

This plan describes how to evolve the game into an **infinite** run that gets **harder over time**, with **dynamic pipes** that move, wobble, or rotate.

---

## 1. Current State

- Single run until collision; restart with R.
- Pipes scroll left at fixed speed; gap and spawn interval vary slightly.
- No score, no difficulty progression, no pipe movement beyond horizontal scroll.

---

## 2. Target: Infinite + Escalating Difficulty + Dynamic Pipes

### 2.1 Infinite Game

- **No level end** — game continues until the bird hits a pipe or the ground.
- **Score** — increment when bird passes through a pipe pair (center between pipes).
- **Persistent run** — no "win" condition; player aims for high score.

### 2.2 Escalating Difficulty

Difficulty increases with **score** (or time). Parameters scale as score rises:

| Parameter            | Base   | Scaling Rule (example)                    |
|----------------------|--------|-------------------------------------------|
| Scroll speed         | 6      | +0.5 per 5 points (cap ~12)               |
| Pipe gap             | 200    | −5 per 5 points (min ~120)                |
| Pipe spawn interval  | 80–120 | −2 per 5 points (min ~50)                  |
| Gap center variance  | 200–450| Narrow range as score rises (harder angles)|

**Difficulty tiers (example):**

- **0–10 pts:** Easy — slow scroll, wide gap, generous spawn interval.
- **11–30 pts:** Medium — faster scroll, smaller gap.
- **31–60 pts:** Hard — fast scroll, narrow gap, pipes spawn closer.
- **61+ pts:** Expert — max speed, minimum gap, tight spawns.

### 2.3 Dynamic Pipes: Move, Wobble, Turn

Pipes should feel more alive and challenging:

#### A. Vertical Movement (Oscillation)

- **Sine-wave wobble:** Top and bottom pipes move up/down in sync or opposite phase.
- **Amplitude:** 20–60 px, increases with difficulty.
- **Frequency:** 0.05–0.15 rad/frame (tunable).
- **Implementation:** Each pipe stores `phase`, `amplitude`, `frequency`; in `update()`, apply `y += amplitude * sin(phase)` and increment `phase`.

#### B. Rotation (Turn / Tilt)

- **Tilt angle:** Pipes rotate slightly (e.g. ±15°) around their center.
- **Oscillating tilt:** Angle varies over time (sin wave).
- **Implementation:** Store base image; each frame: `rotated = transform.rotate(base_image, angle)`, update rect to match rotated size.

#### C. Turtle-like Movement (Slow Turn)

- **"Turtle"** = pipes that slowly change direction or orientation.
- **Interpretation 1:** Pipes drift up or down over time (linear or curved path).
- **Interpretation 2:** Pipes tilt slowly left/right like a turtle turning.
- **Implementation:** Add `tilt_velocity`; each frame `angle += tilt_velocity`, with periodic reversal or bounds.

#### D. Combined Modes (Phase 2)

- **Wobble + tilt:** Pipes both oscillate vertically and rotate.
- **Difficulty-gated:** Easy = static; Medium = wobble only; Hard = wobble + tilt.

---

## 3. Implementation Plan

### Phase 1: Foundation (Infinite + Score + Difficulty Scaling)

1. **Score system**
   - Add `score: int` and `passed_pipes: set[Pipe]` (or pipe pair id).
   - When bird's `rect.right` passes pipe's `rect.left` and we haven't counted this pair, add 1 to score.
   - Render score on screen (top-center).

2. **Difficulty scaling**
   - Add `get_difficulty_params(score: int) -> DifficultyParams` returning scroll_speed, pipe_gap, spawn_interval, gap_center_range.
   - Use these params in main loop and `spawn_pipes()`.

3. **Refactor for testability**
   - Extract `DifficultyParams` dataclass.
   - Pass `scroll_speed` into `Pipe.update()` instead of global (or pass a `GameState` object).

### Phase 2: Dynamic Pipes — Wobble

1. **Pipe pair identity**
   - Spawn top and bottom as a pair; assign shared `pair_id` and `phase`.
   - Both pipes use same `phase` for synchronized wobble.

2. **Vertical wobble in `Pipe.update()`**
   - `self.phase += frequency`
   - `offset_y = amplitude * sin(phase)`
   - `self.rect.y = base_y + offset_y` (store `base_y` at spawn).

3. **Collision**
   - Use `rect` for collision; rect updates each frame with wobble, so collision stays correct.

### Phase 3: Dynamic Pipes — Tilt / Rotation

1. **Rotatable pipe**
   - Store `base_image` and `angle`.
   - Each frame: `self.image = transform.rotate(base_image, angle)`.
   - Update `rect` to keep center stable; use `get_rect(center=...)`.

2. **Tilt modes**
   - **Static tilt:** Fixed angle per pipe (random ±10°).
   - **Oscillating tilt:** `angle = base_angle + amplitude * sin(phase)`.
   - **Turtle turn:** `angle += angular_velocity` with periodic reversal.

### Phase 4: Polish

1. **Difficulty-gated pipe behavior**
   - Score 0–10: Static pipes.
   - Score 11–30: Wobble only.
   - Score 31+: Wobble + tilt.

2. **Visual feedback**
   - Score popup when passing a pipe.
   - Optional: pipe color or glow changes with difficulty.

3. **Game over screen**
   - Show final score, high score, "Press R to restart".

---

## 4. File Structure (Proposed)

```
FlyCode/flappybird/
├── bird.py          # Main entry; game loop (keep or split)
├── game.py          # GameState, score, difficulty (optional refactor)
├── sprites/
│   ├── bird.py      # Bird class
│   └── pipe.py      # Pipe class (with wobble, tilt)
├── config.py        # Constants, DifficultyParams
├── img/
└── docs/
    └── GAME_PLAN.md # This file
```

For minimal change: keep single `bird.py` and add wobble/tilt logic to `Pipe` class.

---

## 5. Constants to Add (Phase 2–3)

```python
# Wobble
WOBBLE_AMPLITUDE_BASE: int = 20
WOBBLE_AMPLITUDE_MAX: int = 60
WOBBLE_FREQUENCY: float = 0.08

# Tilt
TILT_ANGLE_BASE: float = 10.0
TILT_AMPLITUDE: float = 15.0
TURTLE_ANGULAR_VELOCITY: float = 0.5
TURTLE_REVERSE_INTERVAL: int = 120  # frames
```

---

## 6. Summary

| Feature              | Description                                              |
|----------------------|----------------------------------------------------------|
| **Infinite**         | No end; score increases on each pipe passed             |
| **Escalating**       | Scroll speed ↑, gap ↓, spawn rate ↑ as score increases   |
| **Pipe wobble**      | Vertical sine-wave oscillation                          |
| **Pipe tilt**        | Rotation (static, oscillating, or turtle-like turn)     |
| **Difficulty gates** | Easy = static; Medium = wobble; Hard = wobble + tilt    |

Implement in order: Phase 1 (score + difficulty) → Phase 2 (wobble) → Phase 3 (tilt) → Phase 4 (polish).
