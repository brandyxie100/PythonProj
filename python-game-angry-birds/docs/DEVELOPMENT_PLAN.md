# Skill-Driven Development Plan — Angry Birds (Python)

This document summarizes the project, maps workspace rules and skills to this codebase, and defines how to develop new features in a skill-driven manner.

---

## 1. Project Understanding

### 1.1 Overview

- **Name:** Angry Birds clone (Pygame + Pymunk)
- **Stack:** Python 3.12+, Pygame 2.6.1, Pymunk 7.2.0
- **Run:** From `src/`: `python main.py`

### 1.2 Architecture

| Component    | File           | Responsibility |
|-------------|----------------|----------------|
| Game loop   | `src/main.py`  | Display, input, physics step, collision handlers, UI overlays (pause/cleared/failed), slingshot, trajectory preview |
| Characters  | `src/characters.py` | `Bird` (launch impulse, circle body), `Pig` (target, life) |
| Levels      | `src/level.py` | `Level` with `build_0()`–`build_20()`, helpers: `open_flat`, `closed_flat`, `horizontal_pile`, `vertical_pile` |
| Structures  | `src/polygon.py` | `Polygon` (wood beams/columns, pymunk box, wood textures) |

- **Physics:** Pymunk `Space`; collision types: 0=Bird, 1=Pig, 2=Wood, 3=Static.
- **States:** `game_state`: 0=playing, 1=paused, 3=failed, 4=cleared.
- **Features:** Slingshot launch, trajectory preview, zero-gravity (S/N), wall toggle (W), 21 levels, star ratings, score.

### 1.3 Current Gaps (vs. Workflow Rules)
cd
- **No `docs/`** — Add this file and any feature/context docs.
- **No tests** — Workflow requires test-first; add `tests/` and pytest (and optionally `factory_boy` only if we introduce domain entities).
- **No `make lint` / `make test`** — Add a `Makefile` (or equivalent) so Verify step and skills can run the same commands.
- **No CONTRIBUTING.md** — Optional; add if you want PR/merge and AI-assisted workflow documented in-repo.

---

## 2. Rules and Skills Mapping

### 2.1 Workflow Rule (`.cursor/rules/workflow.mdc`)

The workflow is **branch → understand → test first → implement → verify → commit → push & PR**. For this game:

- **Branch:** From `main`; name: `feature/<context>-<description>` or `fix/<context>-<description>`.
- **Understand:** Read `docs/` (e.g. this plan, plus any new docs for a feature).
- **Bounded context:** This repo is a single game; use **context = area of change**, e.g.:
  - `physics` — Pymunk, gravity, collision, trajectory
  - `level` — Level layout, build_*(), star thresholds, bird count
  - `game` — Main loop, game states, scoring, UI overlays
  - `input` — Slingshot, keyboard (S/N/W/ESC), button clicks
  - `render` — Drawing, sprites, camera/parallax
- **Test first:** Prefer unit tests for pure logic (e.g. `to_pygame`, `vector`, `unit_vector`, `distance`, `compute_trajectory_points`); integration tests for level loading or game state where feasible.
- **Implement:** Minimal code to pass tests; docstrings (Google style) and key inline comments.
- **Verify:** Run lint and tests (see §3).
- **Commit:** Conventional Commits with scope = context above, e.g. `feat(physics): add trajectory damping`, `fix(level): correct build_12 pig positions`.
- **Push & PR:** Push branch, open PR to `main`, &lt; 400 lines per PR when possible.

### 2.2 Skill: Linear Plan Issues (`.cursor/skills/linear-plan-issues/SKILL.md`)

Use when you want to **record requirements as Linear issues** (e.g. after discussing a feature).

- **Title format:** `[p{priority}][{type}][{module}] {title}`  
  For this repo, **module** = one of: `physics`, `level`, `game`, `input`, `render` (or `shared` for cross-cutting).
- **Example:** `[p2][Feature][physics] Add trajectory damping when bird is slow`
- **Team/Project:** The skill references `AI-PoweredCVPrime`; if your Linear is for this game repo, create a dedicated Team/Project for it and use that in the skill/MCP, or reuse the same team and rely on labels/titles to distinguish.

### 2.3 Skill: Linear-Driven Dev (`.cursor/skills/linear-driven-dev/SKILL.md`)

Use when you want to **start development from Linear** (“开始开发”, “拉取需求”, “下一个任务”, “start dev”).

- **Flow:** Pick next issue (Todo/Backlog) → confirm with user → create branch from `main` → set issue to In Progress → **develop (human-driven, AI-assisted)** → on “开发完成”/“done”/“提交代码”: verify (lint + test) → propose commit message → commit → push → set issue to Done → suggest “创建PR”.
- **Branch naming:** From issue type and module:  
  `feature/<module>-<short-description>`, `fix/<module>-<short-description>`, `improvement/<module>-<short-description>`.
- **During development:** Follow workflow: understand → test first → implement → verify. Do not auto-advance to commit until the user signals completion.

### 2.4 Skill: PR–CI–Merge (`.cursor/skills/pr-ci-merge/SKILL.md`)

Use when you want to **open a PR and get it merged** (“创建PR”, “提交PR”, “检查CI”, “合并PR”, or after pushing a branch).

- **Flow:** Create PR (title/body from branch and changes) → monitor CI → fix failures (up to ~3 iterations) → confirm with user → squash merge to `main` → cleanup.
- **Prerequisites:** `gh` auth, branch pushed; repo has CI (e.g. GitHub Actions) for lint and test so the skill can “watch” checks.

---

## 3. Recommended Project Setup (So Skills & Workflow Work)

1. **Lint**
   - Add Ruff (and optionally mypy) for `src/**/*.py`.
   - Expose via `make lint` (e.g. `ruff check src/` and optionally `mypy src/`).

2. **Tests**
   - Add `tests/` with pytest.
   - Target: pure helpers in `main.py` (e.g. `to_pygame`, `vector`, `unit_vector`, `distance`, `compute_trajectory_points`) and, as needed, level-loading or state logic.
   - Expose via `make test` (e.g. `pytest tests/ -v`).

3. **Docs**
   - Keep `docs/` for this plan and any new design/context docs (e.g. `docs/physics.md`, `docs/levels.md`).

4. **Optional**
   - `CONTRIBUTING.md`: point to this plan and workflow; mention “AI-Assisted Workflow” (Linear → branch → commit → PR → merge) if you use it.
   - CI (e.g. GitHub Actions): run `make lint` and `make test` on push/PR so pr-ci-merge can monitor checks.

---

## 4. Skill-Driven Development Plan (Step-by-Step)

### Phase A: One-time setup (if not already done)

1. **Scaffolding**
   - Create `docs/` and add this plan.
   - Add `Makefile` with `lint` and `test` targets; add Ruff (and optionally mypy), pytest, `tests/` with at least one test (e.g. for `to_pygame` or `distance`).
   - Optionally add CI and `CONTRIBUTING.md`.

2. **Linear (if using Linear)**
   - Ensure a Team/Project for this game (or reuse existing) and that the Linear MCP uses it.
   - Optionally create a few starter issues (e.g. “Add trajectory damping”, “Add level 22”) using the **linear-plan-issues** skill so you can pull them with **linear-driven-dev**.

### Phase B: For each new feature or bug

1. **Capture requirement (optional but recommended)**
   - Discuss the feature/fix; then run **linear-plan-issues** to create an issue with title `[p?][Feature|Bug|Improvement][module] …`.

2. **Start development**
   - Say “开始开发” / “拉取需求” / “下一个任务” / “start dev” and use **linear-driven-dev**:
     - Pick and confirm issue → create branch (e.g. `feature/physics-trajectory-damping`) → set In Progress.
     - Develop: read `docs/`, write failing tests, implement, run `make lint` and `make test`.
     - When done, say “开发完成” / “提交代码” → review commit message → commit → push → set issue Done → “创建PR”.

3. **PR and merge**
   - Say “创建PR” / “合并PR” (or equivalent) and use **pr-ci-merge**: create PR, watch CI, fix if needed, squash merge after approval.

4. **Sync**
   - Regularly: `git fetch origin && git rebase origin/main`; push with `--force-with-lease` if you rebased.

---

## 5. Summary

| Item | Purpose |
|------|--------|
| **Workflow** | Branch → Understand → Test first → Implement → Verify → Commit → PR; scope = `physics` / `level` / `game` / `input` / `render` (or `shared`). |
| **linear-plan-issues** | Turn discussed requirements into Linear issues with `[p?][Type][module] Title`. |
| **linear-driven-dev** | Pick issue → branch → develop (test-first, then implement) → verify → commit → push → Done; wait for user before commit/PR. |
| **pr-ci-merge** | Create PR, monitor CI, fix, squash merge. |
| **Project setup** | `docs/`, `make lint`, `make test`, optional CI and CONTRIBUTING, so all steps and skills run consistently. |

Using this plan and the three skills together gives a consistent, skill-driven path from idea → Linear issue → branch → tests → implementation → commit → PR → merge.
