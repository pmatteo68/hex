"""
Logging configuration for the game.

Reads the GAME_LOG_LEVEL environment variable (set in bin/env.cmd or bin/env.sh).
Writes to both the console and helix.log in the current working directory.
"""
import logging
import os
import sw_metadata

_LOG_FILE    = sw_metadata.getSWName().lower() + ".log"
_LOG_FORMAT  = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_LEVEL = "INFO"


def setup_logging():
    level_name = os.environ.get("GAME_LOG_LEVEL", _DEFAULT_LEVEL).upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    if not root.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(fmt)
        root.addHandler(ch)

        fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(fmt)
        root.addHandler(fh)

