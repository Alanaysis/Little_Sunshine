# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Little Sunshine is a PyQt6 desktop pet — a small bird that walks, flies, eats, sleeps, and reacts to user interaction on-screen. The UI is in Chinese.

## Commands

```bash
# Run the app
python main.py

# Regenerate sprite assets (offline, requires Pillow)
python generate_bird_sprites.py

# Install dependencies
pip install -r requirements.txt          # PyQt6>=6.6
pip install Pillow                        # only needed for generate_bird_sprites.py
```

No tests, linting, or build scripts exist.

## Architecture

The app is a single `main.py` (~650 lines) with four classes:

- **`BirdWindow(QWidget)`** — Main frameless, transparent, always-on-top window. Contains the 6-state state machine (`idle`/`walk`/`fly`/`eat`/`sleep`/`pet`), 60fps game loop via `QTimer(16ms)`, rendering pipeline (glow → shadow → particles → sprite → hunger indicator), and input handling (left-drag, right-click menu, double-click feed). X11 click-through mask lets clicks pass through non-bird areas on Linux.
- **`BirdData`** — Persistence model. Saves/loads to `~/.little_sunshine.json`. On reload, applies time-based stat decay (hunger grows over offline hours, mood drops if hungry).
- **`StatusPanel(QWidget)`** — Frameless overlay showing mood/hunger/energy/love as colored progress bars.
- **`Particle`** — Visual effects (circle, heart, star, sparkle, crumb) for eating, sleeping, idle, petting feedback.

`bird_skins.py` — `BirdSkin` loads per-frame PNGs from `assets/bird/<species>/<state>_f<N>.png`. Falls back to code-drawn bird if no skin is found. 8 species available.

`generate_bird_sprites.py` — Offline PIL tool to regenerate all 32×32 pixel-art sprites. Not imported at runtime.

## Key locations in main.py

- **Lines 17–28**: Tuning constants (hunger/energy decay rates, movement speeds, animation timings, interaction rewards)
- **State machine**: `BirdWindow._update_state()` handles transitions; each state has its own `_update_<state>()` method
- **Rendering**: `BirdWindow.paintEvent()` orchestrates the draw pipeline
- **Stats**: mood, hunger, energy, love — all 0–100, interact via `BirdData`

## Data file

`~/.little_sunshine.json` stores bird name, stats, position, state, and last-saved timestamp. Gitignored.

## Conventions

- Python 3.10+, PyQt6 6.6+
- Comments and UI strings are in Chinese
- Sprite assets: `assets/bird/<species>/` with `<state>_f0..f3.png` per state (6 states × 4 frames)
