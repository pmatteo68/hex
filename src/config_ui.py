"""
UI skin selector for Hex.
Set SKIN to the name of a module inside src/skins/ to switch the active skin.
"""
import importlib
import logging
import random

logger = logging.getLogger(__name__)

SKINS = (
    "default",   # Default  - cream background, red vs blue
    "midnight",  # Midnight - near-black, neon stones
    "sunset",    # Sunset   - warm amber/coral tones
    "ocean",     # Ocean    - deep navy, teal and cyan
    "forest",    # Forest   - mossy greens, bark browns
    "candy",     # Candy    - pastel bubblegum palette
)

# Active skin -- replace "default" with any name above, or use "random"
SKIN = "default" #"default"

try:
    SKIN = random.choice(SKINS) if SKIN == "random" else SKIN
    _skin = importlib.import_module(f"skins.{SKIN}")
except (ImportError, ValueError) as _err:
    logger.error("Skin '%s' could not be loaded (%s) -- falling back to default", SKIN, _err)
    from skins import default as _skin


def get_name() -> str:
    return _skin.SKIN_NAME


_DEFAULTS = {
    "START_ENGINE_LABEL_PADY_TOP": 2,
    "RULES_WRAP_WIDTH":            420,
    "RULES_LABEL_PADX":            24,
    "RULES_LABEL_PADY":            16,
    "RULES_CLOSE_PADY_BOT":        16,
    "STATS_SECTION_PACK_PADY_TOP": 8,
    "STATS_SECTION_PACK_PADY_BOT": 2,
    "STATS_CLOSE_BTN_PADY_TOP":    8,
    "STATS_CHART_PACK_PADY_TOP":   8,
    "STATS_TABLE_PADY_TOP":        4,
    "STATS_TABLE_PADY_BOT":        2,
    "STATS_TABLE_COL_PAD":         24,
    "STATS_TABLE_DIVIDER_PADY":    3,
    "STATUS_BTN_FONT":             ("Helvetica", 9),
    "MIN_WINDOW_WIDTH":            640,
    # Live panel defaults (override per skin as needed)
    "LIVE_PANEL_WIDTH":            164,
    "LIVE_PANEL_BG":               "#f5f0e8",
    "LIVE_PANEL_PADX":             12,
    "LIVE_PANEL_PADY":             8,
    "LIVE_PANEL_ROW_PADY":         3,
    "LIVE_PANEL_SECTION_FONT":     ("Helvetica", 9, "bold"),
    "LIVE_PANEL_SECTION_COLOR":    "#ffffff",
    "LIVE_PANEL_SECTION_BG":       "#795548",
    "LIVE_PANEL_SECTION_PADY":     4,
    "LIVE_PANEL_LABEL_FONT":       ("Helvetica", 9),
    "LIVE_PANEL_LABEL_COLOR":      "#5d4037",
    "LIVE_PANEL_VALUE_FONT":       ("Helvetica", 16, "bold"),
    "LIVE_PANEL_CHIP_SIZE":        12,
    "LIVE_PANEL_BAR_WIDTH":        136,
    "LIVE_PANEL_BAR_HEIGHT":       14,
    "LIVE_PANEL_BAR_MAX":          11,
    "LIVE_PANEL_BAR_BG":           "#e8dcc8",
    "LIVE_PANEL_TURN_MARKER":      ">",
    "LIVE_PANEL_TREND_P1_COLOR":   "#c62828",
    "LIVE_PANEL_TREND_P2_COLOR":   "#0d47a1",
    "LIVE_PANEL_TREND_NEUTRAL":    "#5d4037",
    "LIVE_PANEL_TREND_THRESHOLD":  1,
}


def __getattr__(name: str):
    try:
        return getattr(_skin, name)
    except AttributeError:
        if name in _DEFAULTS:
            return _DEFAULTS[name]
        raise
