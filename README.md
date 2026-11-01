# Hex

> **Version:** 1.0.0
> **Date:** Oct. 31, 2026
> **Author:** Matteo P.
> **URL:** https://github.com/pmatteo68/hex
---

A Python/Tkinter implementation of the classic **Hex** board game,
featuring a pluggable AI engine, multiple skins, autoplay mode,
game save/load, and an end-of-game statistics window with a position
advantage chart.

---

## Table of Contents

1. [Game Rules](#game-rules)
2. [Requirements](#requirements)
3. [Environment Setup](#environment-setup)
4. [Running the Game](#running-the-game)
5. [Configuration](#configuration)
6. [Skins](#skins)
7. [AI Engines](#ai-engines)
8. [Save and Load](#save-and-load)
9. [Autoplay Mode](#autoplay-mode)
10. [Logging](#logging)
11. [Project Layout](#project-layout)

---

## Game Rules

Hex is a two-player zero-sum board game played on an n x n grid of
hexagonal cells. There are no draws -- one player always wins.

- **Player 1 (Red)** must connect the **Left** edge to the **Right** edge
  with a continuous chain of red stones.
- **Player 2 (Blue)** must connect the **Top** edge to the **Bottom** edge
  with a continuous chain of blue stones.

On each turn a player places one stone on any empty cell.
The colored border strips around the board show which player owns each
pair of edges.

The first player has a theoretical advantage (strategy-stealing argument).
The start screen lets you choose the board size and who goes first.

---

## Requirements

- Python 3.9 or later (with Tkinter, which ships with the standard CPython
  distribution on all platforms)
- `matplotlib` (optional; disables the end-of-game chart if absent)

The only runtime dependency beyond the standard library is listed in
`requirements.txt`.

---

## Environment Setup

### Windows

Open a CMD window in the `v1.0.0` directory, then run:

```
create_env.cmd
```

This creates a virtual environment, activates it, and installs the
dependencies.

To open a fresh CMD window with the environment already sourced, use:

```
open_env.cmd
```

### Unix / macOS

In a terminal, from the `v1.0.0` directory:

```
chmod +x create_env.sh bin/env.sh play.sh
./create_env.sh
```

> **Important**: the `.sh` scripts are Bash scripts. On Windows, always
> use the matching `.cmd` scripts -- never run `.sh` files in CMD or
> PowerShell.

---

## Running the Game

### Windows

```
play.cmd
```

### Unix / macOS

```
./play.sh
```

Both scripts activate the virtual environment and launch the game.

---

## Configuration

All configuration is split across a small number of plain Python files
inside the `src/` directory. Open the relevant file in any text editor
to adjust behavior:

- **Game rules and parameters** -- board size range, AI timing,
  animation timing, and all other gameplay constants are in the
  game configuration file.

- **AI engine selection** -- the name of the active engine module is
  set in the same game configuration file.

- **AI engine tuning** -- each engine ships with its own configuration
  file inside `src/ai_engines/`. Adjust search depth, iteration counts,
  and other engine-specific knobs there.

- **User-visible text** -- every label, button caption, status message,
  and piece of text shown in the UI is centralised in the text
  configuration file. Change it to localise or rebrand the game.

- **UI visuals** -- colors, fonts, padding, and animation parameters
  are not in the source code; they live in the active skin (see Skins).

Every constant has a comment in the source file explaining its range
and effect. Hard limits (e.g. minimum/maximum board size) are documented
alongside the constant.

---

## Skins

A skin is a plain Python module that defines the complete visual style
of the game: colors, fonts, sizes, and timing values. Skins live in
`src/skins/`.

### Selecting a skin

Open the skin selector file (`src/config_ui.py`) and set the active skin
name to any of the bundled options, or to `"random"` to pick one at launch.

Available skins: `default`, `midnight`, `sunset`, `ocean`, `forest`, `candy`.

### Creating a custom skin

1. Copy `src/skins/default.py` to `src/skins/my_skin.py`.
2. Edit colors, fonts, and sizes to taste. Every constant is commented.
3. Register the new name in the skin selector file.

Any constant omitted from your skin file falls back to a built-in default,
so you only need to override what you want to change.

---

## AI Engines

The AI is pluggable. The facade module `src/ai_engine.py` loads whichever
engine is configured; no other part of the codebase imports an engine
directly. The built-in engine uses **Monte Carlo Tree Search** with UCT
(Upper Confidence Bound for Trees); its tuning is in its own configuration
file under `src/ai_engines/`.

### Writing a custom AI engine

1. Create a new file inside `src/ai_engines/`, e.g. `my_engine.py`.
2. Import and subclass `HexAIEngine` from `ai_engines.base`:

```python
from ai_engines.base import HexAIEngine, EMPTY, PLAYER_1, PLAYER_2

class MyEngine(HexAIEngine):

    def get_name(self) -> str:
        return "My Engine"

    def _compute_next_move(self, board: list, player: int,
                           board_size: int) -> tuple:
        # board: flat list, index = row * board_size + col
        # Values: EMPTY=0, PLAYER_1=1, PLAYER_2=2
        # PLAYER_1 connects Left to Right.
        # PLAYER_2 connects Top to Bottom.
        # Return (row, col) of the desired empty cell.
        # The public wrapper validates the result and falls back
        # to the first empty cell if you return an invalid move,
        # so the game can always continue even if your code has a bug.
        for row in range(board_size):
            for col in range(board_size):
                if board[row * board_size + col] == EMPTY:
                    return (row, col)
        return (0, 0)

    def reset(self) -> None:
        pass   # clear any internal state here

def create():
    return MyEngine()
```

3. Set the engine name in the game configuration file to the filename
   stem you chose (e.g. `"my_engine"`).

**Key contract points**:

- Implement `_compute_next_move()`, not `next_move()`. The public
  `next_move()` in the base class handles validation and fallback.
- The board is a *flat* list of `board_size * board_size` integers.
  Cell `(row, col)` is at index `row * board_size + col`.
- Your engine will be called from a background thread; keep all
  Tkinter interaction out of the engine.
- Implement `reset()` to clear any game-to-game state; it is called
  at the start of each new game.
- In autoplay mode two independent instances are created (one per
  player) using the `create()` factory function.

---

## Save and Load

During a game, use **Game > Save Game...** to write the current position
to a JSON file. Use **Game > Load Game...** to resume from a file.

An annotated example save file is provided in the `docs/` directory.

---

## Autoplay Mode

Click **Auto Play** on the start screen to run a full game without any
human intervention. Both players use independent instances of the
configured AI engine. This is useful for:

- Testing the complete game flow end-to-end, including the win animation
  and statistics window.
- Benchmarking or comparing AI engines.
- Verifying a custom skin or configuration change.

The pace between moves is controlled by a configurable delay in the
game configuration file.

---

## Logging

The game logs to the console and to `hex.log` in the working directory.

The log level is read from the `GAME_LOG_LEVEL` environment variable,
which is set in `bin/env.cmd` (Windows) and `bin/env.sh` (Unix).
Accepted values are the standard Python log levels: `DEBUG`, `INFO`,
`WARNING`, `ERROR`, `CRITICAL`.

The default is `INFO`, which produces verbose output for every internal
operation. The start banner and the end-of-game summary are always logged
at `INFO` level.

---

## Project Layout

```
v1.0.0/
  play.cmd / play.sh        -- launch the game (Windows / Unix)
  create_env.cmd / .sh      -- create the virtual environment
  open_env.cmd              -- open a pre-configured CMD window (Windows only)
  bin/                      -- environment variable scripts (sourced by the above)
  requirements.txt          -- pip dependencies
  src/
    config_*.py             -- all configuration files (game, text, UI/skin)
    game_*.py               -- game logic, statistics, and persistence
    ui_*.py                 -- all Tkinter UI modules
    ai_engine.py            -- AI plugin facade
    ai_engines/             -- AI engine implementations and their configs
    skins/                  -- visual skin modules (one file per skin)
    log_config.py           -- logging setup
    sw_metadata.py          -- version string
  docs/                     -- supplementary files and examples
```
