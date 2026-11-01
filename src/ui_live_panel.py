"""
LivePanel -- live game-info widget shown to the right of the board.

Displays per-player stone counts, a position-advantage bar, a trend
indicator (who is gaining ground since the last move), and board fill.

Update it after every committed move by calling update(gs, stats).
"""
import tkinter as tk
import logging

import config_ui   as UI
import config_text as CT
from game_logic import PLAYER_1, PLAYER_2

log = logging.getLogger(__name__)


class LivePanel(tk.Frame):
    """Live info panel for the game screen."""

    def __init__(self, parent, board_size: int, human_player: "int | None"):
        super().__init__(parent, bg=UI.LIVE_PANEL_BG,
                         width=UI.LIVE_PANEL_WIDTH)
        self.pack_propagate(False)
        self._board_size   = board_size
        self._human_player = human_player

        self._stones_vars = {
            PLAYER_1: tk.StringVar(value="0"),
            PLAYER_2: tk.StringVar(value="0"),
        }
        self._turn_vars = {
            PLAYER_1: tk.StringVar(value=" "),
            PLAYER_2: tk.StringVar(value=" "),
        }
        self._think_vars = {
            PLAYER_1: tk.StringVar(value=CT.LIVE_TIME_NONE),
            PLAYER_2: tk.StringVar(value=CT.LIVE_TIME_NONE),
        }
        self._adv_var    = tk.StringVar(value=CT.LIVE_EVEN)
        self._fill_var   = tk.StringVar(value="0%")

        self._bar_canvas = None
        self._bar_p1_id  = None
        self._bar_p2_id  = None
        self._adv_label  = None
        self._trend_lbl  = None

        self._build()
        log.debug("LivePanel created (board_size=%d)", board_size)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, gs, stats) -> None:
        """Refresh all live figures. Call from the main thread after each move."""
        scores = stats.position_score_trajectory

        # Stone counts
        self._stones_vars[PLAYER_1].set(str(stats.player1_moves))
        self._stones_vars[PLAYER_2].set(str(stats.player2_moves))

        # Turn marker
        if not gs.game_over:
            m = UI.LIVE_PANEL_TURN_MARKER
            self._turn_vars[PLAYER_1].set(
                m if gs.current_player == PLAYER_1 else "")
            self._turn_vars[PLAYER_2].set(
                m if gs.current_player == PLAYER_2 else "")
        else:
            self._turn_vars[PLAYER_1].set("")
            self._turn_vars[PLAYER_2].set("")

        # Advantage bar + label
        if scores:
            score = scores[-1]
            self._update_bar(score)
            if score > 0:
                adv_text  = CT.LIVE_AHEAD_P1 + "  (+" + str(score) + ")"
                adv_color = UI.LIVE_PANEL_TREND_P1_COLOR
            elif score < 0:
                adv_text  = CT.LIVE_AHEAD_P2 + "  (+" + str(-score) + ")"
                adv_color = UI.LIVE_PANEL_TREND_P2_COLOR
            else:
                adv_text  = CT.LIVE_EVEN
                adv_color = UI.LIVE_PANEL_TREND_NEUTRAL
            self._adv_var.set(adv_text)
            if self._adv_label:
                self._adv_label.configure(fg=adv_color)

        # Trend
        if len(scores) >= 2:
            delta = scores[-1] - scores[-2]
            thr   = UI.LIVE_PANEL_TREND_THRESHOLD
            if delta >= thr:
                trend_text  = CT.LIVE_GAINING_P1
                trend_color = UI.LIVE_PANEL_TREND_P1_COLOR
            elif delta <= -thr:
                trend_text  = CT.LIVE_GAINING_P2
                trend_color = UI.LIVE_PANEL_TREND_P2_COLOR
            else:
                trend_text  = CT.LIVE_STABLE
                trend_color = UI.LIVE_PANEL_TREND_NEUTRAL
            if self._trend_lbl:
                self._trend_lbl.configure(text=trend_text, fg=trend_color)
        elif len(scores) == 1 and self._trend_lbl:
            self._trend_lbl.configure(text=CT.LIVE_STABLE,
                                      fg=UI.LIVE_PANEL_TREND_NEUTRAL)

        # Board fill
        self._fill_var.set(str(stats.board_fill_pct()) + "%")

        # Think time (last move per player)
        for player in (PLAYER_1, PLAYER_2):
            t = stats.last_think_time(player)
            self._think_vars[player].set(
                CT.LIVE_TIME_NONE if t is None else self._fmt_time(t)
            )

        log.debug(
            "LivePanel updated: p1=%d p2=%d score=%s fill=%s%%",
            stats.player1_moves, stats.player2_moves,
            scores[-1] if scores else "n/a",
            stats.board_fill_pct(),
        )

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build(self) -> None:
        s = UI

        # ---- Header ----
        tk.Label(
            self, text=CT.LIVE_HEADER,
            font=s.LIVE_PANEL_SECTION_FONT,
            fg=s.LIVE_PANEL_SECTION_COLOR,
            bg=s.LIVE_PANEL_SECTION_BG,
            anchor="w",
            padx=s.LIVE_PANEL_PADX,
            pady=s.LIVE_PANEL_SECTION_PADY,
        ).pack(fill="x")

        # ---- Stones ----
        self._section(CT.LIVE_SECTION_STONES)
        for player in (PLAYER_1, PLAYER_2):
            self._player_row(player)

        # ---- Position ----
        self._section(CT.LIVE_SECTION_POS)
        self._build_bar()
        self._adv_label = tk.Label(
            self, textvariable=self._adv_var,
            font=s.LIVE_PANEL_LABEL_FONT,
            fg=s.LIVE_PANEL_TREND_NEUTRAL,
            bg=s.LIVE_PANEL_BG,
            wraplength=s.LIVE_PANEL_WIDTH - 2 * s.LIVE_PANEL_PADX,
        )
        self._adv_label.pack(
            padx=s.LIVE_PANEL_PADX,
            pady=(0, s.LIVE_PANEL_ROW_PADY),
        )

        # ---- Trend ----
        self._section(CT.LIVE_SECTION_TREND)
        self._trend_lbl = tk.Label(
            self, text=CT.LIVE_STABLE,
            font=s.LIVE_PANEL_LABEL_FONT,
            fg=s.LIVE_PANEL_TREND_NEUTRAL,
            bg=s.LIVE_PANEL_BG,
        )
        self._trend_lbl.pack(
            padx=s.LIVE_PANEL_PADX,
            pady=(s.LIVE_PANEL_ROW_PADY, s.LIVE_PANEL_PADY),
        )

        # ---- Board fill ----
        self._section(CT.LIVE_SECTION_BOARD)
        tk.Label(
            self, textvariable=self._fill_var,
            font=s.LIVE_PANEL_VALUE_FONT,
            fg=s.LIVE_PANEL_LABEL_COLOR,
            bg=s.LIVE_PANEL_BG,
        ).pack(
            padx=s.LIVE_PANEL_PADX,
            pady=(s.LIVE_PANEL_ROW_PADY, s.LIVE_PANEL_PADY),
        )

        # ---- Think time ----
        self._section(CT.LIVE_SECTION_TIME)
        for player in (PLAYER_1, PLAYER_2):
            self._think_row(player)

    def _section(self, title: str) -> None:
        s = UI
        tk.Label(
            self, text=title,
            font=s.LIVE_PANEL_SECTION_FONT,
            fg=s.LIVE_PANEL_SECTION_COLOR,
            bg=s.LIVE_PANEL_SECTION_BG,
            anchor="w",
            padx=s.LIVE_PANEL_PADX,
            pady=s.LIVE_PANEL_SECTION_PADY,
        ).pack(fill="x", pady=(s.LIVE_PANEL_PADY, 0))

    def _player_row(self, player: int) -> None:
        s       = UI
        is_p1   = (player == PLAYER_1)
        color   = s.PLAYER_1_COLOR   if is_p1 else s.PLAYER_2_COLOR
        t_color = s.TURN_COLOR_P1    if is_p1 else s.TURN_COLOR_P2

        if self._human_player == player:
            name = CT.PLAYER_HUMAN
        elif is_p1:
            name = CT.PLAYER_1_NAME
        else:
            name = CT.PLAYER_2_NAME

        row = tk.Frame(self, bg=s.LIVE_PANEL_BG)
        row.pack(fill="x",
                 padx=s.LIVE_PANEL_PADX,
                 pady=s.LIVE_PANEL_ROW_PADY)

        # Colored chip
        chip = tk.Frame(row, bg=color,
                        width=s.LIVE_PANEL_CHIP_SIZE,
                        height=s.LIVE_PANEL_CHIP_SIZE)
        chip.pack_propagate(False)
        chip.pack(side="left", padx=(0, 4), pady=2)

        # Name label
        tk.Label(row, text=name,
                 font=s.LIVE_PANEL_LABEL_FONT,
                 fg=color, bg=s.LIVE_PANEL_BG,
                 ).pack(side="left")

        # Stone count (right-aligned, prominent)
        tk.Label(row, textvariable=self._stones_vars[player],
                 font=s.LIVE_PANEL_VALUE_FONT,
                 fg=color, bg=s.LIVE_PANEL_BG,
                 width=3, anchor="e",
                 ).pack(side="right")

        # Turn marker (just inside the count)
        tk.Label(row, textvariable=self._turn_vars[player],
                 font=s.LIVE_PANEL_LABEL_FONT,
                 fg=t_color, bg=s.LIVE_PANEL_BG,
                 width=2,
                 ).pack(side="right")

    def _build_bar(self) -> None:
        s  = UI
        bw = s.LIVE_PANEL_BAR_WIDTH
        bh = s.LIVE_PANEL_BAR_HEIGHT

        frame = tk.Frame(self, bg=s.LIVE_PANEL_BG)
        frame.pack(padx=s.LIVE_PANEL_PADX,
                   pady=(s.LIVE_PANEL_ROW_PADY, 0))

        self._bar_canvas = tk.Canvas(
            frame, width=bw, height=bh,
            bg=s.LIVE_PANEL_BAR_BG,
            highlightthickness=1,
            highlightbackground=s.PANEL_DIVIDER_COLOR,
            bd=0,
        )
        self._bar_canvas.pack()

        mid = bw // 2
        self._bar_p1_id = self._bar_canvas.create_rectangle(
            0, 0, mid, bh, fill=s.PLAYER_1_COLOR, outline="",
        )
        self._bar_p2_id = self._bar_canvas.create_rectangle(
            mid, 0, bw, bh, fill=s.PLAYER_2_COLOR, outline="",
        )

    def _think_row(self, player: int) -> None:
        s     = UI
        is_p1 = (player == PLAYER_1)
        color = s.PLAYER_1_COLOR if is_p1 else s.PLAYER_2_COLOR

        if self._human_player == player:
            name = CT.PLAYER_HUMAN
        elif is_p1:
            name = CT.PLAYER_1_NAME
        else:
            name = CT.PLAYER_2_NAME

        row = tk.Frame(self, bg=s.LIVE_PANEL_BG)
        row.pack(fill="x",
                 padx=s.LIVE_PANEL_PADX,
                 pady=s.LIVE_PANEL_ROW_PADY)

        chip = tk.Frame(row, bg=color,
                        width=s.LIVE_PANEL_CHIP_SIZE,
                        height=s.LIVE_PANEL_CHIP_SIZE)
        chip.pack_propagate(False)
        chip.pack(side="left", padx=(0, 4), pady=2)

        tk.Label(row, text=name,
                 font=s.LIVE_PANEL_LABEL_FONT,
                 fg=color, bg=s.LIVE_PANEL_BG,
                 ).pack(side="left")

        tk.Label(row, textvariable=self._think_vars[player],
                 font=s.LIVE_PANEL_LABEL_FONT,
                 fg=s.LIVE_PANEL_LABEL_COLOR, bg=s.LIVE_PANEL_BG,
                 anchor="e",
                 ).pack(side="right")

    @staticmethod
    def _fmt_time(t: float) -> str:
        if t < 60.0:
            return f"{t:.1f}s"
        m = int(t) // 60
        s = int(t) % 60
        return f"{m}m{s:02d}s"

    def _update_bar(self, score: int) -> None:
        if self._bar_canvas is None:
            return
        s     = UI
        bw    = s.LIVE_PANEL_BAR_WIDTH
        bh    = s.LIVE_PANEL_BAR_HEIGHT
        max_s = max(1, s.LIVE_PANEL_BAR_MAX)
        ratio = max(-1.0, min(1.0, score / max_s))
        div   = int(bw / 2 + ratio * bw / 2)
        div   = max(0, min(bw, div))
        self._bar_canvas.coords(self._bar_p1_id, 0, 0, div, bh)
        self._bar_canvas.coords(self._bar_p2_id, div, 0, bw, bh)
