"""StatsWindow -- end-of-game summary dialog with optional matplotlib chart."""
import tkinter as tk
import logging

import config_ui   as UI
import config_text as CT
from game_logic import PLAYER_1, PLAYER_2

log = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    _MPL_OK = True
except Exception:
    _MPL_OK = False
    log.debug("matplotlib unavailable -- stats chart disabled")


class StatsWindow(tk.Toplevel):
    """Modal end-of-game summary window."""

    def __init__(self, parent, stats, human_player: "int | None"):
        super().__init__(parent)
        self._stats        = stats
        self._human_player = human_player
        self._fig_canvas   = None  # FigureCanvasTkAgg, kept for cleanup
        self._mpl_fig      = None  # matplotlib Figure, kept for cleanup
        s = UI
        self.title(CT.STATS_TITLE)
        self.resizable(False, False)
        self.configure(bg=s.BG_COLOR)
        self.grab_set()
        self._build()
        self._center(parent)

    def destroy(self) -> None:
        """Override to explicitly close matplotlib objects before Tkinter teardown.

        FigureCanvasTkAgg holds a PhotoImage in a reference cycle. If this
        cycle is left for Python's cyclic GC to collect, the PhotoImage.__del__
        may fire from a background thread (e.g. the AI worker), causing a
        Tkinter thread-safety error. Explicitly closing here ensures cleanup
        happens on the main thread.
        """
        if self._fig_canvas is not None:
            try:
                self._fig_canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self._fig_canvas = None
        if self._mpl_fig is not None and _MPL_OK:
            try:
                import matplotlib.pyplot as plt
                plt.close(self._mpl_fig)
            except Exception:
                pass
            self._mpl_fig = None
        super().destroy()

    # ------------------------------------------------------------------

    def _build(self) -> None:
        s   = UI
        st  = self._stats
        pad = s.STATS_PADDING

        outer = tk.Frame(self, bg=s.BG_COLOR, padx=pad, pady=pad)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text=CT.STATS_TITLE,
            font=s.STATS_TITLE_FONT,
            fg=s.STATS_TITLE_COLOR,
            bg=s.BG_COLOR,
        ).pack(pady=(0, s.STATS_TITLE_PADY_BOT))

        self._section(outer, CT.STATS_SECTION_RESULT)
        self._row(outer, CT.STATS_WINNER_LABEL, self._winner_text())

        self._section(outer, CT.STATS_SECTION_MOVES)
        self._moves_table(outer)

        self._section(outer, CT.STATS_SECTION_BOARD)
        self._row(outer, CT.STATS_ROW_BOARD_FILL, f"{st.board_fill_pct()}%")
        wm = st.winning_move_number()
        self._row(outer, CT.STATS_ROW_WINNING_MOVE,
                  f"#{wm}" if wm is not None else CT.STATS_NA)

        self._section(outer, CT.STATS_SECTION_TIMING)
        dur = st.game_duration
        if dur is not None:
            mins, secs = divmod(int(dur), 60)
            self._row(outer, CT.STATS_DURATION_LABEL,
                      f"{mins}m {secs:02d}s" if mins else f"{secs}s")
        avg1 = st.avg_move_time(PLAYER_1)
        avg2 = st.avg_move_time(PLAYER_2)
        if avg1 > 0:
            self._row(outer, CT.STATS_ROW_AVG_TIME_P1, f"{avg1:.2f}s")
        if avg2 > 0:
            self._row(outer, CT.STATS_ROW_AVG_TIME_P2, f"{avg2:.2f}s")

        if s.STATS_SHOW_CHART and _MPL_OK:
            self._build_chart(outer)

        tk.Frame(outer, height=s.STATS_CLOSE_SPACER_H, bg=s.BG_COLOR).pack()
        tk.Button(
            outer,
            text=CT.BTN_CLOSE,
            font=s.BTN_FONT,
            fg=s.BTN_FG,
            bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG,
            activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF,
            bd=s.BTN_BD,
            padx=s.BTN_PADX,
            pady=s.BTN_PADY,
            command=self.destroy,
        ).pack(pady=(s.STATS_CLOSE_BTN_PADY_TOP, 0))

    def _section(self, parent, text: str) -> None:
        s = UI
        tk.Label(
            parent,
            text=text,
            font=s.STATS_SECTION_FONT,
            fg=s.STATS_SECTION_FG,
            bg=s.STATS_SECTION_BG,
            anchor="w",
            padx=s.STATS_ROW_PADX,
            pady=s.STATS_SECTION_PADY,
        ).pack(fill="x",
               pady=(s.STATS_SECTION_PACK_PADY_TOP, s.STATS_SECTION_PACK_PADY_BOT))

    def _row(self, parent, label: str, value: str) -> None:
        s   = UI
        row = tk.Frame(parent, bg=s.BG_COLOR)
        row.pack(fill="x", padx=s.STATS_ROW_PADX, pady=s.STATS_ROW_PADY)
        tk.Label(row, text=label, font=s.STATS_ROW_LABEL_FONT,
                 fg=s.STATS_ROW_LABEL_COLOR, bg=s.BG_COLOR,
                 anchor="w").pack(side="left")
        tk.Label(row, text=value, font=s.STATS_ROW_VALUE_FONT,
                 fg=s.STATS_ROW_VALUE_COLOR, bg=s.BG_COLOR,
                 anchor="e").pack(side="right")

    def _moves_table(self, parent) -> None:
        s  = UI
        st = self._stats

        COL_LABEL = 0
        COL_P1    = 1
        COL_P2    = 2
        NUM_COLS  = 3
        ROW_HDR   = 0
        ROW_DIV   = 1
        ROW_MOVES = 2
        ROW_TOTAL = 3

        CP = s.STATS_TABLE_COL_PAD

        frame = tk.Frame(parent, bg=s.BG_COLOR)
        frame.pack(fill="x", padx=s.STATS_ROW_PADX,
                   pady=(s.STATS_TABLE_PADY_TOP, s.STATS_TABLE_PADY_BOT))
        frame.columnconfigure(COL_LABEL, weight=1)

        hdr_kw = dict(font=s.STATS_ROW_VALUE_FONT,
                      fg=s.STATS_ROW_VALUE_COLOR, bg=s.BG_COLOR)
        lbl_kw = dict(font=s.STATS_ROW_LABEL_FONT,
                      fg=s.STATS_ROW_LABEL_COLOR, bg=s.BG_COLOR)
        val_kw = dict(font=s.STATS_ROW_VALUE_FONT,
                      fg=s.STATS_ROW_VALUE_COLOR, bg=s.BG_COLOR)

        p1_label = self._player_display_name(PLAYER_1)
        p2_label = self._player_display_name(PLAYER_2)

        tk.Label(frame, text="",       **lbl_kw).grid(
            row=ROW_HDR, column=COL_LABEL, sticky="w")
        tk.Label(frame, text=p1_label, **hdr_kw).grid(
            row=ROW_HDR, column=COL_P1, padx=(CP, 0), sticky="e")
        tk.Label(frame, text=p2_label, **hdr_kw).grid(
            row=ROW_HDR, column=COL_P2, padx=(CP, 0), sticky="e")

        dp = s.STATS_TABLE_DIVIDER_PADY
        tk.Frame(frame, height=1, bg=s.STATS_DIVIDER_COLOR).grid(
            row=ROW_DIV, column=COL_LABEL, columnspan=NUM_COLS,
            sticky="ew", pady=(dp, dp))

        tk.Label(frame, text=CT.STATS_ROW_MOVES_P1, **lbl_kw).grid(
            row=ROW_MOVES, column=COL_LABEL, sticky="w", pady=s.STATS_ROW_PADY)
        tk.Label(frame, text=str(st.player1_moves), **val_kw).grid(
            row=ROW_MOVES, column=COL_P1, padx=(CP, 0), sticky="e",
            pady=s.STATS_ROW_PADY)
        tk.Label(frame, text=str(st.player2_moves), **val_kw).grid(
            row=ROW_MOVES, column=COL_P2, padx=(CP, 0), sticky="e",
            pady=s.STATS_ROW_PADY)

        tk.Label(frame, text=CT.STATS_ROW_TOTAL_MOVES, **lbl_kw).grid(
            row=ROW_TOTAL, column=COL_LABEL, sticky="w", pady=s.STATS_ROW_PADY)
        tk.Label(frame, text=str(st.total_moves), **val_kw).grid(
            row=ROW_TOTAL, column=COL_P1, padx=(CP, 0),
            columnspan=NUM_COLS - 1, sticky="e", pady=s.STATS_ROW_PADY)

    def _winner_text(self) -> str:
        st = self._stats
        if st.winner == PLAYER_1:
            return (CT.STATS_WINNER_HUMAN if self._human_player == PLAYER_1
                    else CT.STATS_WINNER_P1)
        if st.winner == PLAYER_2:
            if self._human_player == PLAYER_2:
                return CT.STATS_WINNER_HUMAN
            if self._human_player == PLAYER_1:
                return CT.STATS_WINNER_AI
            return CT.STATS_WINNER_P2
        return CT.STATS_NA

    def _player_display_name(self, player: int) -> str:
        if self._human_player == player:
            return CT.PLAYER_HUMAN
        if self._human_player is not None:
            return CT.PLAYER_AI
        return (CT.PLAYER_1_NAME if player == PLAYER_1 else CT.PLAYER_2_NAME)

    def _build_chart(self, parent) -> None:
        s      = UI
        st     = self._stats
        scores = st.position_score_trajectory

        if not scores:
            return

        xs = list(range(1, len(scores) + 1))

        fig, ax = plt.subplots(figsize=(
            (s.STATS_WINDOW_WIDTH - 2 * s.STATS_PADDING) / s.STATS_CHART_DPI,
            s.STATS_CHART_HEIGHT_IN,
        ), dpi=s.STATS_CHART_DPI)
        fig.patch.set_facecolor(s.STATS_CHART_BG)
        ax.set_facecolor(s.STATS_CHART_BG)

        positive = [max(v, 0) for v in scores]
        negative = [min(v, 0) for v in scores]

        ax.plot(xs, scores,
                color=s.STATS_CHART_P1_COLOR,
                lw=s.STATS_CHART_LINE_WIDTH,
                label=CT.STATS_CHART_P1_LABEL,
                marker="o", markersize=3)
        ax.fill_between(xs, positive,
                        alpha=s.STATS_CHART_FILL_ALPHA,
                        color=s.STATS_CHART_P1_COLOR)
        ax.fill_between(xs, negative,
                        alpha=s.STATS_CHART_FILL_ALPHA,
                        color=s.STATS_CHART_P2_COLOR)

        ax.axhline(0, color=s.STATS_CHART_ZERO_COLOR,
                   lw=s.STATS_CHART_ZERO_WIDTH, linestyle=":")

        ax.set_xlabel(CT.STATS_CHART_X_LABEL,
                      fontsize=s.STATS_CHART_FONT_SIZE,
                      color=s.STATS_CHART_LINE_COLOR,
                      labelpad=s.STATS_CHART_LABEL_PAD)
        ax.set_ylabel(CT.STATS_CHART_Y_LABEL,
                      fontsize=s.STATS_CHART_FONT_SIZE,
                      color=s.STATS_CHART_LINE_COLOR,
                      labelpad=s.STATS_CHART_LABEL_PAD)
        ax.tick_params(labelsize=s.STATS_CHART_FONT_SIZE,
                       length=s.STATS_CHART_TICK_LENGTH,
                       pad=s.STATS_CHART_TICK_PAD,
                       colors=s.STATS_CHART_LINE_COLOR)
        for sp in ax.spines.values():
            sp.set_edgecolor(s.STATS_CHART_LINE_COLOR)
            sp.set_linewidth(s.STATS_CHART_SPINE_WIDTH)
        ax.grid(True, color=s.STATS_CHART_GRID_COLOR,
                lw=s.STATS_CHART_GRID_WIDTH, linestyle=":")
        ax.legend(fontsize=s.STATS_CHART_FONT_SIZE,
                  facecolor=s.STATS_CHART_BG,
                  edgecolor=s.STATS_CHART_LINE_COLOR,
                  labelcolor=s.STATS_CHART_LINE_COLOR)
        fig.tight_layout(pad=s.STATS_CHART_LAYOUT_PAD)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x",
                                    pady=(s.STATS_CHART_PACK_PADY_TOP, 0))
        self._fig_canvas = canvas
        self._mpl_fig    = fig
        plt.close(fig)  # remove from pyplot's figure manager; canvas keeps a ref

    def _center(self, parent) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w  = self.winfo_reqwidth()
        h  = self.winfo_reqheight()
        x  = px + (pw - w) // 2
        y  = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")
