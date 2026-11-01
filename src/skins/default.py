"""Default skin -- cream background, red vs blue stones, classic Hex look."""

SKIN_NAME = "Default"

# -- Window -------------------------------------------------------------------
LAYOUT_INIT_DELAY_MS = 10

# -- General background -------------------------------------------------------
BG_COLOR            = "#f5f0e8"
PANEL_BG            = "#f5f0e8"
PANEL_DIVIDER_COLOR = "#c8b89a"

# -- Board canvas -------------------------------------------------------------
HEX_SIZE            = 28      # circumradius (px) of each hexagon
BOARD_PADDING       = 30      # outer margin around the hex grid
BORDER_WIDTH        = 8       # pixel width of the player-edge border strips

BOARD_BG_COLOR      = "#f5f0e8"
CELL_EMPTY_COLOR    = "#e8dcc8"
CELL_OUTLINE_COLOR  = "#b8a898"
CELL_OUTLINE_WIDTH  = 1

PLAYER_1_COLOR       = "#d32f2f"   # red
PLAYER_2_COLOR       = "#1565c0"   # blue
PLAYER_1_GHOST_COLOR = "#f48fb1"   # light red (hover ghost)
PLAYER_2_GHOST_COLOR = "#90caf9"   # light blue (hover ghost)

WIN_FLASH_COLOR_P1   = "#ff5252"   # bright red flash
WIN_FLASH_COLOR_P2   = "#448aff"   # bright blue flash

# Border strips indicating player ownership
BORDER_P1_COLOR      = "#d32f2f"   # red  -- left + right edges
BORDER_P2_COLOR      = "#1565c0"   # blue -- top  + bottom edges

# -- Status bar ---------------------------------------------------------------
STATUS_BAR_HEIGHT    = 44
STATUS_BG            = "#e8dcc8"
STATUS_FONT          = ("Helvetica", 12)
STATUS_COLOR         = "#3e2723"
STATUS_LABEL_PADX    = 12
STATUS_BTN_PADX      = 4
STATUS_BTN_PADX_END  = 8
STATUS_BTN_PADY      = 4
STATUS_BTN_FONT      = ("Helvetica", 9)

# -- Buttons ------------------------------------------------------------------
BTN_BG          = "#795548"
BTN_FG          = "#ffffff"
BTN_ACTIVE_BG   = "#8d6e63"
BTN_FONT        = ("Helvetica", 11, "bold")
BTN_RELIEF      = "flat"
BTN_PADX        = 14
BTN_PADY        = 6
BTN_BD          = 0
MENU_BD         = 0

# -- Start screen -------------------------------------------------------------
START_TITLE_FONT      = ("Helvetica", 30, "bold")
START_TITLE_COLOR     = "#5d4037"
START_SUBTITLE_FONT   = ("Helvetica", 14)
START_SUBTITLE_COLOR  = "#795548"
START_ENGINE_PADY     = 8
START_TITLE_PADY      = 6
START_SUBTITLE_PADY   = 16
START_WHO_FIRST_PADY  = 14
START_BTN_PADX        = 8
START_RULES_PADY      = 18
START_BOTTOM_ROW_PADY = 14
START_SECTION_PADY    = 16
START_ENGINE_LABEL_PADY_TOP = 2

LABEL_FONT  = ("Helvetica", 11)
LABEL_COLOR = "#5d4037"

# -- Menu colors --------------------------------------------------------------
MENU_FG = "#3e2723"

# -- Turn indicator colors in status bar --------------------------------------
TURN_COLOR_P1   = "#c62828"
TURN_COLOR_P2   = "#0d47a1"
TURN_COLOR_DRAW = "#607d8b"

# -- About / Rules dialogs ----------------------------------------------------
ABOUT_WRAP_WIDTH          = 380
ABOUT_PADX                = 24
ABOUT_PADY                = 8
ABOUT_TITLE_PADY_TOP      = 20
ABOUT_DIVIDER_PADX        = 20
ABOUT_HEADER_DIVIDER_PADY = 10
ABOUT_BODY_DIVIDER_PADY   = 6
ABOUT_CLOSE_PADY_TOP      = 10
ABOUT_CLOSE_PADY_BOT      = 20
BOARD_BORDER              = "#c8b89a"

RULES_WRAP_WIDTH     = 420
RULES_LABEL_PADX     = 24
RULES_LABEL_PADY     = 16
RULES_CLOSE_PADY_BOT = 16

# -- Stats window -------------------------------------------------------------
STATS_WINDOW_WIDTH    = 540
STATS_PADDING         = 18
STATS_TITLE_PADY_BOT  = 10
STATS_CLOSE_SPACER_H  = 6
STATS_SECTION_BG      = BTN_BG
STATS_SECTION_FG      = BTN_FG
STATS_SECTION_FONT    = ("Helvetica", 10, "bold")
STATS_SECTION_PADY    = 6
STATS_ROW_LABEL_FONT  = ("Helvetica", 11)
STATS_ROW_VALUE_FONT  = ("Helvetica", 11, "bold")
STATS_ROW_LABEL_COLOR = STATUS_COLOR
STATS_ROW_VALUE_COLOR = "#5d4037"
STATS_ROW_PADX        = 14
STATS_ROW_PADY        = 2
STATS_DIVIDER_COLOR   = BOARD_BORDER
STATS_TITLE_FONT      = START_TITLE_FONT
STATS_TITLE_COLOR     = START_TITLE_COLOR
STATS_DELAY_MS        = 800

STATS_TABLE_PADY_TOP     = 4
STATS_TABLE_PADY_BOT     = 2
STATS_TABLE_COL_PAD      = 24
STATS_TABLE_DIVIDER_PADY = 3

STATS_SHOW_CHART        = True
STATS_CHART_HEIGHT_IN   = 2.6
STATS_CHART_DPI         = 90
STATS_CHART_BG          = BG_COLOR
STATS_CHART_P1_COLOR    = "#d32f2f"
STATS_CHART_P2_COLOR    = "#1565c0"
STATS_CHART_LINE_COLOR  = "#5d4037"
STATS_CHART_ZERO_COLOR  = "#c8b89a"
STATS_CHART_GRID_COLOR  = "#ddd0bc"
STATS_CHART_FILL_ALPHA  = 0.20
STATS_CHART_LINE_WIDTH  = 1.8
STATS_CHART_ZERO_WIDTH  = 1.0
STATS_CHART_FONT_SIZE   = 7
STATS_CHART_LABEL_PAD   = 2
STATS_CHART_TICK_LENGTH = 3
STATS_CHART_TICK_PAD    = 2
STATS_CHART_SPINE_WIDTH = 0.8
STATS_CHART_GRID_WIDTH  = 0.5
STATS_CHART_LAYOUT_PAD  = 0.6

STATS_SECTION_PACK_PADY_TOP = 8
STATS_SECTION_PACK_PADY_BOT = 2
STATS_CLOSE_BTN_PADY_TOP    = 8
STATS_CHART_PACK_PADY_TOP   = 8

MIN_WINDOW_WIDTH = 640

# -- Live panel ---------------------------------------------------------------
LIVE_PANEL_WIDTH           = 164
LIVE_PANEL_BG              = BG_COLOR
LIVE_PANEL_PADX            = 12
LIVE_PANEL_PADY            = 8
LIVE_PANEL_ROW_PADY        = 3
LIVE_PANEL_SECTION_FONT    = ("Helvetica", 9, "bold")
LIVE_PANEL_SECTION_COLOR   = "#ffffff"
LIVE_PANEL_SECTION_BG      = "#795548"
LIVE_PANEL_SECTION_PADY    = 4
LIVE_PANEL_LABEL_FONT      = ("Helvetica", 9)
LIVE_PANEL_LABEL_COLOR     = "#5d4037"
LIVE_PANEL_VALUE_FONT      = ("Helvetica", 16, "bold")
LIVE_PANEL_CHIP_SIZE       = 12
LIVE_PANEL_BAR_WIDTH       = 136
LIVE_PANEL_BAR_HEIGHT      = 14
# Clamp range for the advantage bar (set to BOARD_SIZE_DEFAULT = 11).
# Increase for larger boards; the bar clamps gracefully either way.
LIVE_PANEL_BAR_MAX         = 11
LIVE_PANEL_BAR_BG          = "#e8dcc8"
LIVE_PANEL_TURN_MARKER     = ">"
LIVE_PANEL_TREND_P1_COLOR  = "#c62828"
LIVE_PANEL_TREND_P2_COLOR  = "#0d47a1"
LIVE_PANEL_TREND_NEUTRAL   = "#5d4037"
# Minimum score delta between consecutive moves to declare a trend.
LIVE_PANEL_TREND_THRESHOLD = 1
