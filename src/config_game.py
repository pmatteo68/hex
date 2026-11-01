"""
Game logic configuration for Hex.
All gameplay-affecting parameters live here.

Board convention:
  board[row][col] -- row 0 is the TOP edge (Player 2's starting edge).
  Player 1 (Red)  connects LEFT  (col=0)     to RIGHT  (col=BOARD_SIZE-1).
  Player 2 (Blue) connects TOP   (row=0)     to BOTTOM (row=BOARD_SIZE-1).
  Values: EMPTY=0, PLAYER_1=1, PLAYER_2=2.

Hard limits:
  BOARD_SIZE_MIN = 3  : playable but trivial; P1 wins in 1 move on a 3x3.
  BOARD_SIZE_MAX = 19 : standard Go-board size; MCTS becomes slow above this.
  Only square boards (n x n) are supported by the rules of Hex.

Structural constant:
  NUM_PLAYERS = 2 -- only 2-player Hex is supported. This constant is
  referenced wherever code relies on exactly two players. No other value
  is valid; the comment is here so no magic "2" appears in the source.
"""

# -- Number of players (structural; only 2 is supported) ---------------------
NUM_PLAYERS = 2

# -- Board size (n x n) -------------------------------------------------------
BOARD_SIZE_MIN     = 3
BOARD_SIZE_MAX     = 19
BOARD_SIZE_DEFAULT = 11

# -- AI engine ----------------------------------------------------------------
AI_ENGINE = "mcts"   # module name inside ai_engines/

# -- AI animation timing ------------------------------------------------------
AI_THINK_DELAY_MS      = 300   # pause (ms) before the AI move begins
AI_INTER_MOVE_PAUSE_MS = 200   # pause (ms) after a committed move

# -- Win flash animation ------------------------------------------------------
WIN_FLASH_COUNT       = 6     # on/off half-cycles
WIN_FLASH_INTERVAL_MS = 150   # ms per half-cycle

# -- Autoplay (testing / demo) ------------------------------------------------
AUTOPLAY_MOVE_DELAY_MS     = 500   # delay (ms) before each autoplay move
AUTOPLAY_HANDOFF_SPLASH_MS = 1500  # ms the auto-dismiss splash stays visible

# -- Start-screen defaults ----------------------------------------------------
# "human" = human goes first (as Player 1); "ai" = AI goes first (as Player 1)
DEFAULT_FIRST_PLAYER = "human"
