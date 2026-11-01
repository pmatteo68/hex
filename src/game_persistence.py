"""
Save and load GameState to/from a human-readable JSON file.
No UI imports -- pure I/O logic.
"""
import json
import logging
from game_logic import (
    GameState, PLAYER_1, PLAYER_2, EMPTY,
    PHASE_PLAYER1_TURN, PHASE_PLAYER2_TURN, PHASE_DONE,
    make_board,
)

logger = logging.getLogger(__name__)

FORMAT_VERSION = 1
FILE_ENCODING  = "utf-8"

_VALID_PHASES   = {PHASE_PLAYER1_TURN, PHASE_PLAYER2_TURN, PHASE_DONE}
_VALID_PLAYERS  = {PLAYER_1, PLAYER_2}


def save_game(state: GameState, human_player: "int | None", path: str) -> None:
    """
    Serialize state and the human player ID to a JSON file.
    human_player is PLAYER_1, PLAYER_2, or None (autoplay).
    """
    logger.debug("Saving game to '%s'", path)
    data = {
        "format_version" : FORMAT_VERSION,
        "human_player"   : human_player,
        "board_size"     : state.board_size,
        "board"          : state.board,
        "move_history"   : state.move_history,
        "current_player" : state.current_player,
        "phase"          : state.phase,
        "winner"         : state.winner,
        "winning_path"   : state.winning_path,
        "game_over"      : state.game_over,
    }
    try:
        with open(path, "w", encoding=FILE_ENCODING) as fh:
            json.dump(data, fh, indent=2)
        logger.info("Game saved to '%s'", path)
    except Exception as exc:
        logger.error("Failed to save to '%s': %s", path, exc)
        raise


def load_game(path: str) -> "tuple[GameState, int | None]":
    """
    Load state from path. Returns (GameState, human_player).
    Raises ValueError on schema mismatch, IOError on file errors.
    """
    logger.debug("Loading game from '%s'", path)
    try:
        with open(path, "r", encoding=FILE_ENCODING) as fh:
            data = json.load(fh)
    except Exception as exc:
        logger.error("Failed to read '%s': %s", path, exc)
        raise

    _validate(data)

    state = GameState.__new__(GameState)
    state.board_size    = int(data["board_size"])
    state.board         = [list(row) for row in data["board"]]
    state.move_history  = [tuple(m) for m in data["move_history"]]
    state.current_player = int(data["current_player"])
    state.phase          = data["phase"]
    state.winner         = data["winner"]
    state.winning_path   = (
        [tuple(cell) for cell in data["winning_path"]]
        if data["winning_path"] is not None else None
    )
    state.game_over = bool(data["game_over"])

    human_player = data.get("human_player")
    if human_player is not None:
        human_player = int(human_player)

    logger.info(
        "Game loaded from '%s' | phase=%s | moves=%d | human_player=%s",
        path, state.phase, len(state.move_history), human_player,
    )
    return state, human_player


def _validate(data: dict) -> None:
    if data.get("format_version") != FORMAT_VERSION:
        raise ValueError(
            f"Unsupported format version: {data.get('format_version')}"
        )
    required = (
        "board_size", "board", "move_history",
        "current_player", "phase", "winner", "winning_path", "game_over",
    )
    for key in required:
        if key not in data:
            raise ValueError(f"Missing field: '{key}'")
    if data["phase"] not in _VALID_PHASES:
        raise ValueError(f"Unknown phase: '{data['phase']}'")
    if data["current_player"] not in _VALID_PLAYERS:
        raise ValueError(f"Invalid current_player: {data['current_player']}")
