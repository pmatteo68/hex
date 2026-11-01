"""Main application window and controller for Hex."""
import gc
import threading
import time
import tkinter as tk
import weakref
from tkinter import filedialog, messagebox
import logging

import config_game   as CG
import config_text   as CT
import config_ui     as UI
import ai_engine     as AE
from game_logic       import GameState, PLAYER_1, PLAYER_2
from game_persistence import save_game, load_game
from game_stats       import GameStats
from ui_board         import BoardCanvas
from ui_live_panel    import LivePanel
from ui_stats         import StatsWindow

log = logging.getLogger(__name__)

_FIRST_HUMAN = "human"
_FIRST_AI    = "ai"


# ---------------------------------------------------------------------------
# Start screen
# ---------------------------------------------------------------------------

class StartScreen(tk.Frame):
    """
    Initial screen shown at launch or after New Game.
    Provides a board-size dropdown, a who-goes-first selector,
    Start, Load, Auto Play, and Quit buttons.
    """

    def __init__(self, parent, on_start, on_load, on_quit, on_autoplay):
        super().__init__(parent, bg=UI.BG_COLOR)
        self._on_start       = on_start
        self._on_load        = on_load
        self._on_quit        = on_quit
        self._on_autoplay_cb = on_autoplay
        self._build()

    def _build(self) -> None:
        s = UI
        tk.Label(self, text=CT.START_TITLE,
                 font=s.START_TITLE_FONT, fg=s.START_TITLE_COLOR,
                 bg=s.BG_COLOR).pack(pady=(s.START_TITLE_PADY, 0))

        tk.Label(self, text=CT.START_SUBTITLE,
                 font=s.START_SUBTITLE_FONT, fg=s.START_SUBTITLE_COLOR,
                 bg=s.BG_COLOR).pack(pady=(s.START_SUBTITLE_PADY, 0))

        tk.Label(self,
                 text=CT.START_ENGINE_LABEL + "  " + AE.get_name(),
                 font=s.LABEL_FONT, fg=s.LABEL_COLOR,
                 bg=s.BG_COLOR).pack(pady=(s.START_ENGINE_PADY, 0))

        # Board-size dropdown
        grid_frame = tk.Frame(self, bg=s.BG_COLOR)
        grid_frame.pack(pady=(s.START_SECTION_PADY, 0))

        self._size_var = tk.StringVar(value=str(CG.BOARD_SIZE_DEFAULT))
        size_opts = [str(v) for v in range(CG.BOARD_SIZE_MIN, CG.BOARD_SIZE_MAX + 1)]

        tk.Label(grid_frame, text=CT.START_SIZE_LABEL,
                 font=s.LABEL_FONT, fg=s.LABEL_COLOR, bg=s.BG_COLOR,
                 anchor="e").grid(row=0, column=0, sticky="e", padx=(0, 8), pady=3)
        om = tk.OptionMenu(grid_frame, self._size_var, *size_opts)
        om.config(
            bg=s.BTN_BG, fg=s.BTN_FG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            highlightthickness=0, font=s.BTN_FONT,
            relief=s.BTN_RELIEF, bd=s.MENU_BD, width=5,
        )
        om["menu"].config(
            bg=s.BTN_BG, fg=s.BTN_FG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
        )
        om.grid(row=0, column=1, sticky="w", pady=3)

        self._size_var.trace_add("write", lambda *_: self._update_hint())

        # Hint label
        self._hint_var = tk.StringVar()
        tk.Label(self, textvariable=self._hint_var,
                 font=s.LABEL_FONT, fg=s.LABEL_COLOR,
                 bg=s.BG_COLOR).pack(pady=(s.START_RULES_PADY, 0))
        self._update_hint()

        # Who goes first
        tk.Label(self, text=CT.START_WHO_FIRST,
                 font=s.LABEL_FONT, fg=s.LABEL_COLOR,
                 bg=s.BG_COLOR).pack(pady=(s.START_WHO_FIRST_PADY, 0))

        radio_frame = tk.Frame(self, bg=s.BG_COLOR)
        radio_frame.pack()

        self._first_var = tk.StringVar(
            value=_FIRST_HUMAN if CG.DEFAULT_FIRST_PLAYER == _FIRST_HUMAN
            else _FIRST_AI
        )
        for value, text in ((_FIRST_HUMAN, CT.START_FIRST_HUMAN),
                             (_FIRST_AI,    CT.START_FIRST_AI)):
            tk.Radiobutton(
                radio_frame, text=text,
                variable=self._first_var, value=value,
                font=s.BTN_FONT, fg=s.LABEL_COLOR, bg=s.BG_COLOR,
                activebackground=s.BG_COLOR, selectcolor=s.BG_COLOR,
                indicatoron=True,
            ).pack(side="left", padx=s.START_BTN_PADX)

        # Action buttons
        for label, cmd in (
            (CT.BTN_START,    self._on_start_clicked),
            (CT.BTN_LOAD_GAME, self._on_load),
            (CT.BTN_AUTOPLAY, self._on_autoplay_clicked),
            (CT.BTN_QUIT,     self._on_quit),
        ):
            tk.Button(
                self, text=label,
                font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
                activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
                relief=s.BTN_RELIEF, bd=s.BTN_BD,
                padx=s.BTN_PADX, pady=s.BTN_PADY,
                command=cmd,
            ).pack(pady=(s.START_BOTTOM_ROW_PADY // 2, 0),
                   padx=s.START_BTN_PADX, fill="x", ipadx=10)

    def _update_hint(self) -> None:
        try:
            n = int(self._size_var.get())
            self._hint_var.set(CT.make_rules_hint(n))
        except (ValueError, tk.TclError):
            pass

    def _on_start_clicked(self) -> None:
        try:
            self._on_start(int(self._size_var.get()), self._first_var.get())
        except (ValueError, tk.TclError) as exc:
            log.error("Start screen bad input: %s", exc)

    def _on_autoplay_clicked(self) -> None:
        try:
            self._on_autoplay_cb(int(self._size_var.get()))
        except (ValueError, tk.TclError) as exc:
            log.error("Auto play bad input: %s", exc)


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class App(tk.Tk):
    """Top-level Tkinter window. Manages the start/game screens and game flow."""

    def __init__(self):
        super().__init__()
        self.title(CT.WINDOW_TITLE)
        self.configure(bg=UI.BG_COLOR)
        self.resizable(False, False)

        self._gs           : "GameState | None" = None
        self._human_player : "int | None"       = None
        self._stats        : "GameStats | None" = None
        self._start_frame  : "StartScreen | None" = None
        self._game_frame   : "tk.Frame | None"    = None
        self._board_canvas : "BoardCanvas | None" = None
        self._live_panel   : "LivePanel | None"   = None
        self._status_label : "tk.Label | None"    = None
        self._autoplay_engines: "dict[int, object]" = {}
        self._autoplay = False
        self._game_id  = 0
        self._min_width = 0
        self._turn_start_ts: float = 0.0

        self._build_menu()
        self._show_start()

    # ------------------------------------------------------------------
    # Screen management
    # ------------------------------------------------------------------

    def _show_start(self) -> None:
        log.debug("Navigating to start screen")
        self._min_width = 0
        self._teardown_game()
        if self._start_frame:
            self._start_frame.destroy()
        self._start_frame = StartScreen(
            self, self._on_start_normal,
            self._on_load_game, self.quit,
            self._on_start_autoplay,
        )
        self._start_frame.pack(fill="both", expand=True,
                                padx=UI.BOARD_PADDING, pady=UI.BOARD_PADDING)
        self.after(UI.LAYOUT_INIT_DELAY_MS, self._fit_window)

    def _show_game(self, state: GameState, human_player: "int | None") -> None:
        log.debug("Navigating to game screen (human_player=%s, autoplay=%s)",
                  human_player, self._autoplay)
        if self._start_frame:
            self._start_frame.pack_forget()
            self._start_frame.destroy()
            self._start_frame = None
        self._teardown_game()

        self._gs           = state
        self._human_player = human_player
        self._stats        = GameStats()
        self._game_id     += 1

        if self._autoplay:
            self._autoplay_engines = {
                PLAYER_1: AE.create_fresh_instance(),
                PLAYER_2: AE.create_fresh_instance(),
            }
            log.debug("Autoplay engines created for both players")
        else:
            self._autoplay_engines = {}
            AE.reset()

        self._min_width = UI.MIN_WINDOW_WIDTH
        self._game_frame = tk.Frame(self, bg=UI.BG_COLOR)
        self._game_frame.pack(fill="both", expand=True)

        # Status bar must be packed before the content frame so that
        # pack(side="bottom") claims its space first.
        self._build_status_bar(self._game_frame)

        content = tk.Frame(self._game_frame, bg=UI.BG_COLOR)
        content.pack(fill="both", expand=True)

        self._board_canvas = BoardCanvas(content, state.board_size)
        self._board_canvas.pack(side="left")
        self._board_canvas.set_on_cell_click(self._on_human_cell_click)

        self._live_panel = LivePanel(content, state.board_size, human_player)
        self._live_panel.pack(side="left", fill="y",
                              padx=(UI.LIVE_PANEL_PADX, 0))

        if state.move_history:
            self._board_canvas.replay_from_history(state.move_history)

        self.after(UI.LAYOUT_INIT_DELAY_MS, self._fit_window)

        if state.game_over:
            self.after(CG.AI_INTER_MOVE_PAUSE_MS, self._on_loaded_game_over)
        else:
            self.after(CG.AI_INTER_MOVE_PAUSE_MS, self._begin_phase)

    def _teardown_game(self) -> None:
        if self._game_frame:
            self._game_frame.destroy()
            self._game_frame   = None
            self._board_canvas = None
            self._live_panel   = None
            self._status_label = None
        self._gs               = None
        self._autoplay_engines = {}

    def _build_status_bar(self, parent: tk.Frame) -> None:
        s   = UI
        bar = tk.Frame(parent, bg=s.STATUS_BG, height=s.STATUS_BAR_HEIGHT)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        btn_frame = tk.Frame(bar, bg=s.STATUS_BG)
        btn_frame.pack(side="right", padx=s.STATUS_BTN_PADX_END,
                       pady=s.STATUS_BTN_PADY)

        for label, cmd in (
            (CT.BTN_NEW_GAME,  self._on_new_game),
            (CT.BTN_SAVE_GAME, self._on_save_game),
            (CT.BTN_LOAD_GAME, self._on_load_game),
            (CT.BTN_QUIT,      self.quit),
        ):
            tk.Button(
                btn_frame, text=label,
                font=s.STATUS_BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
                activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
                relief=s.BTN_RELIEF, bd=s.BTN_BD,
                padx=s.STATUS_BTN_PADX, pady=s.STATUS_BTN_PADY,
                command=cmd,
            ).pack(side="left", padx=s.STATUS_BTN_PADX // 2)

        self._status_label = tk.Label(
            bar, text="",
            font=s.STATUS_FONT, fg=s.STATUS_COLOR, bg=s.STATUS_BG,
            anchor="w", padx=s.STATUS_LABEL_PADX,
        )
        self._status_label.pack(side="left", fill="x", expand=True)

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        s = UI
        menubar = tk.Menu(
            self, bg=s.BG_COLOR, fg=s.MENU_FG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            bd=s.MENU_BD,
        )

        game_menu = tk.Menu(
            menubar, tearoff=0, bg=s.BG_COLOR, fg=s.MENU_FG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
        )
        game_menu.add_command(label=CT.MENU_NEW,  command=self._on_new_game)
        game_menu.add_command(label=CT.MENU_SAVE, command=self._on_save_game)
        game_menu.add_command(label=CT.MENU_LOAD, command=self._on_load_game)
        game_menu.add_separator()
        game_menu.add_command(label=CT.MENU_QUIT, command=self.quit)
        menubar.add_cascade(label=CT.MENU_GAME, menu=game_menu)

        help_menu = tk.Menu(
            menubar, tearoff=0, bg=s.BG_COLOR, fg=s.MENU_FG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
        )
        help_menu.add_command(label=CT.MENU_RULES, command=self._show_rules)
        help_menu.add_command(label=CT.MENU_ABOUT, command=self._show_about)
        menubar.add_cascade(label=CT.MENU_HELP, menu=help_menu)

        self.config(menu=menubar)

    # ------------------------------------------------------------------
    # Phase management
    # ------------------------------------------------------------------

    def _begin_phase(self) -> None:
        if self._gs is None:
            return
        if self._gs.game_over:
            self._on_game_over()
            return

        player = self._gs.current_player
        self._board_canvas.set_current_player(player)
        self._update_live_panel()

        if self._autoplay:
            self._board_canvas.set_enabled(False)
            self._set_status(CT.STATUS_AI_TURN, player)
            engine = self._autoplay_engines[player]
            self.after(CG.AUTOPLAY_MOVE_DELAY_MS,
                       lambda: self._schedule_ai_move(player, engine,
                                                      self._game_id))
        elif player == self._human_player:
            self._turn_start_ts = time.monotonic()
            self._board_canvas.set_enabled(True)
            self._set_status(CT.STATUS_HUMAN_TURN, player)
        else:
            self._board_canvas.set_enabled(False)
            self._set_status(CT.STATUS_AI_TURN, player)
            self.after(CG.AI_THINK_DELAY_MS,
                       lambda: self._schedule_ai_move(player, None,
                                                      self._game_id))

    def _on_human_cell_click(self, row: int, col: int) -> None:
        if self._gs is None or self._gs.game_over:
            return
        if self._gs.current_player != self._human_player:
            return
        if self._gs.board[row][col] != 0:
            messagebox.showinfo(CT.WINDOW_TITLE, CT.MSG_OCCUPIED)
            return
        think_time = time.monotonic() - self._turn_start_ts
        self._board_canvas.set_enabled(False)
        self._commit_move(row, col, think_time)

    def _commit_move(self, row: int, col: int, think_time: float = 0.0) -> None:
        if self._gs is None:
            return
        player = self._gs.current_player
        self._gs.place_stone(row, col)
        self._stats.record_move(player, row, col,
                                self._gs.board, self._gs.board_size,
                                think_time)
        self._update_live_panel()
        self._set_status(CT.STATUS_ANIMATING)
        self._board_canvas.set_stone(row, col, player)

        if self._gs.game_over:
            if self._gs.winner is not None and self._gs.winning_path:
                self._board_canvas.flash_win(
                    self._gs.winning_path, self._gs.winner,
                    self._on_game_over,
                )
            else:
                self._on_game_over()
        else:
            self.after(CG.AI_INTER_MOVE_PAUSE_MS, self._begin_phase)

    # ------------------------------------------------------------------
    # AI thread
    # ------------------------------------------------------------------

    def _schedule_ai_move(self, player: int, engine, game_id: int) -> None:
        if game_id != self._game_id:
            return
        if self._gs is None or self._gs.game_over:
            return

        # Force cyclic GC on the main thread before launching the AI thread.
        # This collects any reference cycles left by the previous stats window
        # (matplotlib's FigureCanvasTkAgg creates PhotoImage cycles). Without
        # this, the AI thread's allocations may trigger a GC sweep that calls
        # PhotoImage.__del__ from the wrong thread.
        gc.collect()

        n          = self._gs.board_size
        board_flat = [self._gs.board[r][c]
                      for r in range(n) for c in range(n)]

        # Use a weak reference so the thread does not keep the App (tk.Tk root)
        # alive. If the window is closed while the AI is thinking, self is freed
        # on the main thread (correct); the thread then finds self_ref() == None
        # and discards the result without touching Tkinter.
        self_ref = weakref.ref(self)

        def _run() -> None:
            t0 = time.monotonic()
            if engine is None:
                move = AE.next_move(board_flat, player, n)
            else:
                move = engine.next_move(board_flat, player, n)
            think_time = time.monotonic() - t0
            app = self_ref()
            if app is not None:
                app.after(0, lambda: app._on_ai_result(move, player, game_id,
                                                       think_time))

        t = threading.Thread(target=_run, daemon=True, name=f"AI-P{player}")
        t.start()

    def _on_ai_result(self, move: tuple, player: int, game_id: int,
                      think_time: float = 0.0) -> None:
        if game_id != self._game_id:
            log.debug("Discarding stale AI result (game changed)")
            return
        if self._gs is None or self._gs.game_over:
            return
        if self._gs.current_player != player:
            log.debug("Discarding stale AI result (player mismatch)")
            return
        self._commit_move(move[0], move[1], think_time)

    # ------------------------------------------------------------------
    # Game over
    # ------------------------------------------------------------------

    def _on_game_over(self) -> None:
        if self._gs is None or self._stats is None:
            return
        winner = self._gs.winner
        self._stats.finalise(winner, "win", self._human_player)

        if winner == PLAYER_1:
            msg   = (CT.GAMEOVER_HUMAN_WINS if self._human_player == PLAYER_1
                     else CT.GAMEOVER_P1_WINS)
            color = UI.TURN_COLOR_P1
        else:
            if self._human_player == PLAYER_2:
                msg = CT.GAMEOVER_HUMAN_WINS
            elif self._human_player == PLAYER_1:
                msg = CT.GAMEOVER_AI_WINS
            else:
                msg = CT.GAMEOVER_P2_WINS
            color = UI.TURN_COLOR_P2

        self._set_status(msg)
        if self._status_label:
            self._status_label.configure(fg=color)
        self._board_canvas.set_enabled(False)
        log.debug("Game over: winner=%s", winner)

        self.after(UI.STATS_DELAY_MS, self._show_stats)

    def _on_loaded_game_over(self) -> None:
        if self._gs is None:
            return
        winner = self._gs.winner
        if winner == PLAYER_1:
            msg, color = CT.GAMEOVER_P1_WINS, UI.TURN_COLOR_P1
        else:
            msg, color = CT.GAMEOVER_P2_WINS, UI.TURN_COLOR_P2
        self._set_status(msg)
        if self._status_label:
            self._status_label.configure(fg=color)
        self._board_canvas.set_enabled(False)
        if self._gs.winning_path:
            self._board_canvas.flash_win(
                self._gs.winning_path, winner, lambda: None
            )

    def _show_stats(self) -> None:
        if self._stats is None or self._stats.total_moves == 0:
            return
        StatsWindow(self, self._stats, self._human_player)

    # ------------------------------------------------------------------
    # Menu / button handlers
    # ------------------------------------------------------------------

    def _on_new_game(self) -> None:
        log.debug("New game requested")
        self._game_id += 1
        self._show_start()

    def _on_save_game(self) -> None:
        if self._gs is None:
            messagebox.showinfo(CT.WINDOW_TITLE, CT.MSG_NO_GAME)
            return
        path = filedialog.asksaveasfilename(
            title=CT.MENU_SAVE,
            defaultextension=".json",
            filetypes=[(CT.SAVE_FILETYPE, "*.json")],
        )
        if not path:
            return
        try:
            save_game(self._gs, self._human_player, path)
            messagebox.showinfo(CT.WINDOW_TITLE, CT.MSG_SAVED.format(path=path))
        except Exception as exc:
            messagebox.showerror(CT.WINDOW_TITLE, CT.MSG_SAVE_ERROR.format(err=exc))

    def _on_load_game(self) -> None:
        path = filedialog.askopenfilename(
            title=CT.MENU_LOAD,
            filetypes=[(CT.SAVE_FILETYPE, "*.json")],
        )
        if not path:
            return
        try:
            state, human_player = load_game(path)
        except Exception as exc:
            messagebox.showerror(CT.WINDOW_TITLE, CT.MSG_LOAD_ERROR.format(err=exc))
            return
        self._autoplay = False
        self._game_id += 1
        self._show_game(state, human_player)

    def _on_start_normal(self, board_size: int, first_player: str) -> None:
        self._autoplay = False
        self._launch_game(board_size, first_player)

    def _on_start_autoplay(self, board_size: int) -> None:
        self._autoplay = True
        self._launch_game(board_size, _FIRST_HUMAN)

    def _launch_game(self, board_size: int, first_player: str) -> None:
        log.debug(
            "Launch game: size=%d first=%s autoplay=%s",
            board_size, first_player, self._autoplay,
        )
        if self._autoplay:
            human_player = None
            first_pid    = PLAYER_1
        elif first_player == _FIRST_HUMAN:
            human_player = PLAYER_1
            first_pid    = PLAYER_1
        else:
            human_player = PLAYER_2
            first_pid    = PLAYER_1

        state = GameState(first_player=first_pid, board_size=board_size)
        self._show_game(state, human_player)

    # ------------------------------------------------------------------
    # Help dialogs
    # ------------------------------------------------------------------

    def _show_rules(self) -> None:
        s   = UI
        dlg = tk.Toplevel(self)
        dlg.title(CT.MENU_RULES)
        dlg.configure(bg=s.BG_COLOR)
        dlg.resizable(False, False)
        dlg.grab_set()
        tk.Label(
            dlg, text=CT.RULES_TEXT,
            font=s.LABEL_FONT, fg=s.LABEL_COLOR, bg=s.BG_COLOR,
            wraplength=s.RULES_WRAP_WIDTH, justify="left",
            padx=s.RULES_LABEL_PADX, pady=s.RULES_LABEL_PADY,
        ).pack()
        tk.Button(
            dlg, text=CT.BTN_CLOSE,
            font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF, bd=s.BTN_BD,
            padx=s.BTN_PADX, pady=s.BTN_PADY,
            command=dlg.destroy,
        ).pack(pady=(0, s.RULES_CLOSE_PADY_BOT))
        self._center_dialog(dlg)

    def _show_about(self) -> None:
        s   = UI
        dlg = tk.Toplevel(self)
        dlg.title(CT.ABOUT_TITLE)
        dlg.configure(bg=s.BG_COLOR)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text=CT.ABOUT_SUBTITLE,
                 font=s.START_TITLE_FONT, fg=s.START_TITLE_COLOR,
                 bg=s.BG_COLOR).pack(
                     pady=(s.ABOUT_TITLE_PADY_TOP, 0), padx=s.ABOUT_PADX)

        tk.Frame(dlg, height=1, bg=s.PANEL_DIVIDER_COLOR).pack(
            fill="x", padx=s.ABOUT_DIVIDER_PADX,
            pady=(s.ABOUT_HEADER_DIVIDER_PADY, 0),
        )
        tk.Label(
            dlg, text=CT.ABOUT_BODY,
            font=s.LABEL_FONT, fg=s.LABEL_COLOR, bg=s.BG_COLOR,
            wraplength=s.ABOUT_WRAP_WIDTH, justify="center",
            padx=s.ABOUT_PADX, pady=s.ABOUT_PADY,
        ).pack()
        tk.Frame(dlg, height=1, bg=s.PANEL_DIVIDER_COLOR).pack(
            fill="x", padx=s.ABOUT_DIVIDER_PADX,
            pady=(s.ABOUT_BODY_DIVIDER_PADY, 0),
        )
        tk.Button(
            dlg, text=CT.BTN_CLOSE,
            font=s.BTN_FONT, fg=s.BTN_FG, bg=s.BTN_BG,
            activebackground=s.BTN_ACTIVE_BG, activeforeground=s.BTN_FG,
            relief=s.BTN_RELIEF, bd=s.BTN_BD,
            padx=s.BTN_PADX, pady=s.BTN_PADY,
            command=dlg.destroy,
        ).pack(pady=(s.ABOUT_CLOSE_PADY_TOP, s.ABOUT_CLOSE_PADY_BOT))

        self._center_dialog(dlg)

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _update_live_panel(self) -> None:
        if self._live_panel and self._gs and self._stats:
            self._live_panel.update(self._gs, self._stats)

    def _set_status(self, text: str, player: "int | None" = None) -> None:
        if self._status_label is None:
            return
        if player == PLAYER_1:
            color = UI.TURN_COLOR_P1
        elif player == PLAYER_2:
            color = UI.TURN_COLOR_P2
        else:
            color = UI.STATUS_COLOR
        self._status_label.configure(text=text, fg=color)
        log.debug("Status: %r", text)

    def _fit_window(self) -> None:
        self.update_idletasks()
        w  = max(self.winfo_reqwidth(), self._min_width)
        h  = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = max(0, (sw - w) // 2)
        y  = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _center_dialog(self, dlg: tk.Toplevel) -> None:
        dlg.update_idletasks()
        pw = self.winfo_width()
        ph = self.winfo_height()
        px = self.winfo_rootx()
        py = self.winfo_rooty()
        w  = dlg.winfo_reqwidth()
        h  = dlg.winfo_reqheight()
        x  = px + (pw - w) // 2
        y  = py + (ph - h) // 2
        dlg.geometry(f"+{x}+{y}")
