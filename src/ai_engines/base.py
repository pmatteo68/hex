"""Abstract base class for all Hex AI engine plugins."""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

EMPTY    = 0
PLAYER_1 = 1
PLAYER_2 = 2


class HexAIEngine(ABC):
    """
    Plugin interface for Hex AI engines.

    Implement _compute_next_move() in your subclass and add a module-level
    factory function create().  The public next_move() wrapper validates the
    result and falls back gracefully so the game can always continue.

    Implementing a custom engine
    ----------------------------
    1. Create a new module, e.g. src/ai_engines/my_engine.py.
    2. Subclass HexAIEngine and implement:
         def get_name(self) -> str
         def _compute_next_move(self, board, player, board_size) -> tuple
         def reset(self) -> None
    3. Add a module-level factory:  def create(): return MyEngine()
    4. Set AI_ENGINE = "my_engine" in src/config_game.py.

    Board encoding
    --------------
    board  : flat list of length board_size*board_size, index = row*board_size+col
             Values: 0=EMPTY, 1=PLAYER_1, 2=PLAYER_2
    player : 1 (PLAYER_1) or 2 (PLAYER_2)
    Returns: (row, col) tuple for the chosen cell
    """

    @abstractmethod
    def get_name(self) -> str:
        """Short identifier shown on the start screen and in logs."""

    def next_move(self, board: list, player: int, board_size: int) -> tuple:
        """
        Public entry point -- do NOT override in subclasses.

        Validates the (row, col) returned by _compute_next_move() and
        substitutes the first valid empty cell if the engine returns an
        occupied or out-of-range cell.
        """
        valid = [
            (r, c)
            for r in range(board_size)
            for c in range(board_size)
            if board[r * board_size + c] == EMPTY
        ]
        if not valid:
            logger.error("next_move called with no empty cells -- returning (0,0)")
            return (0, 0)

        move = self._compute_next_move(board, player, board_size)

        if move in valid:
            return move

        logger.warning(
            "%s._compute_next_move returned invalid cell %s -- "
            "substituting first valid cell %s",
            self.__class__.__name__, move, valid[0],
        )
        return valid[0]

    @abstractmethod
    def _compute_next_move(self, board: list, player: int, board_size: int) -> tuple:
        """
        Implement the move-selection algorithm here.

        board      : flat list, index = row*board_size + col
        player     : PLAYER_1 or PLAYER_2
        board_size : n (the board is n x n)
        Returns    : (row, col) of the chosen empty cell
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset any internal state for a fresh game."""
