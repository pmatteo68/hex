"""All user-visible text for Hex -- change here to localise or rebrand."""

from sw_metadata import getSWName, getVersion
from config_game import (
    BOARD_SIZE_DEFAULT,
    BOARD_SIZE_MIN,
    BOARD_SIZE_MAX,
    NUM_PLAYERS,
)
import ai_engine

# -- Window -------------------------------------------------------------------
WINDOW_TITLE = getSWName() + " v. " + getVersion()

# -- Start screen -------------------------------------------------------------
START_TITLE    = getSWName()
START_SUBTITLE = "Connect your stones across the board to win!"

START_ENGINE_LABEL = "AI engine:"
START_WHO_FIRST    = "Who goes first?"
START_FIRST_HUMAN  = "  Human  "
START_FIRST_AI     = "  Machine  "

START_SIZE_LABEL   = "Board size:"

def make_rules_hint(board_size):
    return str(board_size) + " x " + str(board_size) + " board"

# -- Buttons ------------------------------------------------------------------
BTN_START     = "  Start Game  "
BTN_CLOSE     = "  Close  "
BTN_NEW_GAME  = "New Game"
BTN_SAVE_GAME = "Save Game"
BTN_LOAD_GAME = "Load Game"
BTN_AUTOPLAY  = "  Auto Play  "
BTN_EXIT      = "Exit"
BTN_QUIT      = "Quit"

# -- Status messages ----------------------------------------------------------
STATUS_HUMAN_TURN = "Your turn -- click a cell to place your stone"
STATUS_AI_TURN    = "Machine is thinking..."
STATUS_ANIMATING  = "..."

# -- Player names (status bar, stats, chart) ----------------------------------
PLAYER_1_NAME = "Player 1"
PLAYER_2_NAME = "Player 2"
PLAYER_HUMAN  = "Human"
PLAYER_AI     = "Machine"

# -- Phase / turn header labels -----------------------------------------------
TURN_HEADER_P1 = "Player 1's turn"
TURN_HEADER_P2 = "Player 2's turn"

# -- Game-over messages -------------------------------------------------------
GAMEOVER_P1_WINS    = "Player 1 wins!"
GAMEOVER_P2_WINS    = "Player 2 wins!"
GAMEOVER_HUMAN_WINS = "You win!"
GAMEOVER_AI_WINS    = "Machine wins!"

# -- Autoplay handoff splash --------------------------------------------------
AUTOPLAY_SPLASH_THINKING = "Machine is thinking..."

# -- Menu labels --------------------------------------------------------------
MENU_GAME  = "Game"
MENU_NEW   = "New Game"
MENU_SAVE  = "Save Game..."
MENU_LOAD  = "Load Game..."
MENU_QUIT  = "Quit"
MENU_HELP  = "Help"
MENU_RULES = "Rules"
MENU_ABOUT = "About..."

# -- Dialog messages ----------------------------------------------------------
MSG_NO_GAME    = "No game in progress."
MSG_SAVED      = "Game saved to:\n{path}"
MSG_SAVE_ERROR = "Could not save game:\n{err}"
MSG_LOAD_ERROR = "Could not load game:\n{err}"
MSG_OCCUPIED   = "That cell is already occupied -- choose another."
SAVE_FILETYPE  = "Hex saved games (*.json)"

# -- Rules text ---------------------------------------------------------------
RULES_TEXT = (
    getSWName() + "  --  Rules\n\n"
    "Two players alternate placing stones on the hexagonal grid.\n"
    "Each turn you place one stone on any empty cell.\n\n"
    "Player 1 (Red)  tries to form a connected path of red stones\n"
    "from the LEFT edge to the RIGHT edge.\n\n"
    "Player 2 (Blue) tries to form a connected path of blue stones\n"
    "from the TOP edge to the BOTTOM edge.\n\n"
    "The colored border strips around the board show which player\n"
    "owns each pair of edges.\n\n"
    "Hex has no draws -- one player always wins.\n"
    "The first player has a theoretical advantage (strategy-stealing).\n\n"
    "Default board: " + str(BOARD_SIZE_DEFAULT) + " x " + str(BOARD_SIZE_DEFAULT) + ".\n"
    "Sizes " + str(BOARD_SIZE_MIN) + " to " + str(BOARD_SIZE_MAX) + " are supported."
)

# -- About dialog -------------------------------------------------------------
ABOUT_TITLE    = "About " + getSWName()
ABOUT_SUBTITLE = getSWName()
ABOUT_BODY = (
    getSWName() + " v. " + getVersion() + "\n\n"
    "A classic combinatorial board game.\n\n"
    "AI: " + ai_engine.get_name() + "."
)

# -- Stats window -------------------------------------------------------------
STATS_TITLE          = "Game Summary"
STATS_SECTION_RESULT = "RESULT"
STATS_SECTION_MOVES  = "MOVES"
STATS_SECTION_TIMING = "TIMING"
STATS_SECTION_BOARD  = "BOARD"

STATS_WINNER_LABEL   = "Winner"
STATS_WINNER_P1      = PLAYER_1_NAME
STATS_WINNER_P2      = PLAYER_2_NAME
STATS_WINNER_HUMAN   = PLAYER_HUMAN
STATS_WINNER_AI      = PLAYER_AI

STATS_ROW_MOVES_P1       = PLAYER_1_NAME + " moves"
STATS_ROW_MOVES_P2       = PLAYER_2_NAME + " moves"
STATS_ROW_TOTAL_MOVES    = "Total moves"
STATS_ROW_WINNING_MOVE   = "Winning move"
STATS_ROW_BOARD_FILL     = "Board fill"
STATS_ROW_AVG_TIME_P1    = PLAYER_1_NAME + " avg time"
STATS_ROW_AVG_TIME_P2    = PLAYER_2_NAME + " avg time"
STATS_DURATION_LABEL     = "Game duration"
STATS_NA                 = "--"

STATS_CHART_P1_LABEL = PLAYER_1_NAME
STATS_CHART_P2_LABEL = PLAYER_2_NAME
STATS_CHART_X_LABEL  = "Move #"
STATS_CHART_Y_LABEL  = "Position advantage (P1)"
STATS_CHART_ZERO_LABEL = "Equal"

# -- Live panel (shown during play, to the right of the board) ----------------
LIVE_HEADER          = "LIVE"
LIVE_SECTION_STONES  = "STONES"
LIVE_SECTION_POS     = "POSITION"
LIVE_SECTION_TREND   = "TREND"
LIVE_SECTION_BOARD   = "BOARD"

LIVE_AHEAD_P1   = "P1 ahead"
LIVE_AHEAD_P2   = "P2 ahead"
LIVE_EVEN       = "Even"

LIVE_GAINING_P1 = "P1 gaining"
LIVE_GAINING_P2 = "P2 gaining"
LIVE_STABLE     = "Stable"

LIVE_SECTION_TIME = "TIME"
LIVE_TIME_NONE    = "--"
