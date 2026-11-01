"""
AI engine facade for Hex.
Loads the plugin named by config_game.AI_ENGINE and re-exports its contract.
The rest of the codebase imports only this module and never depends on a
specific engine implementation.
"""
import importlib
import logging
import config_game as CG

logger = logging.getLogger(__name__)

_engine = None


def _get():
    global _engine
    if _engine is None:
        path   = f"ai_engines.{CG.AI_ENGINE}"
        logger.debug("Loading AI engine: %s", path)
        module  = importlib.import_module(path)
        _engine = module.create()
        logger.debug("AI engine loaded: %s", _engine.get_name())
    return _engine


def get_name() -> str:
    return _get().get_name()


def next_move(board: list, player: int, board_size: int) -> tuple:
    """Return the (row, col) the AI wants to play."""
    return _get().next_move(board, player, board_size)


def reset() -> None:
    _get().reset()


def create_fresh_instance():
    """Return a new independent engine instance (own state, same algorithm).
    Use this when two separate engine agents need to play against each other
    without sharing state, e.g. in autoplay mode."""
    module = importlib.import_module(f"ai_engines.{CG.AI_ENGINE}")
    return module.create()
