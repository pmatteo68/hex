"""In-game statistics collector for Hex."""
import time
import logging
from game_logic import PLAYER_1, PLAYER_2, evaluate_position

logger = logging.getLogger(__name__)


class GameStats:

    def __init__(self):
        self._start_time      = time.monotonic()
        self._game_duration   = None

        self.winner           = None       # PLAYER_1 | PLAYER_2 | None
        self.game_over_reason = None       # "win"
        self.human_player     = None       # PLAYER_1 | PLAYER_2 | None (autoplay)

        self._move_times    : "list[float]" = []
        self._move_players  : "list[int]"   = []
        self._move_cells    : "list[tuple]" = []
        self._pos_scores    : "list[int]"   = []

        self._total_moves   = 0
        self._last_move_ts  = time.monotonic()
        self._board_size    = 0

        self._think_times : "dict[int, list[float]]" = {
            PLAYER_1: [],
            PLAYER_2: [],
        }

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_move(self, player: int, row: int, col: int,
                    board: "list[list[int]]", board_size: int,
                    think_time: float = 0.0) -> None:
        now     = time.monotonic()
        elapsed = now - self._last_move_ts
        self._last_move_ts = now

        self._move_players.append(player)
        self._move_cells.append((row, col))
        self._move_times.append(elapsed)
        self._total_moves += 1
        self._board_size = board_size

        self._think_times[player].append(think_time)

        score = evaluate_position(board, board_size)
        self._pos_scores.append(score)

        logger.debug(
            "Stats: move #%d player=%d cell=(%d,%d) elapsed=%.2fs "
            "think=%.3fs score=%d",
            self._total_moves, player, row, col, elapsed, think_time, score,
        )

    def finalise(self, winner: "int | None", game_over_reason: str,
                 human_player: "int | None") -> None:
        self._game_duration   = time.monotonic() - self._start_time
        self.winner           = winner
        self.game_over_reason = game_over_reason
        self.human_player     = human_player
        self._log_summary()

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def game_duration(self) -> float:
        return self._game_duration or 0.0

    @property
    def total_moves(self) -> int:
        return self._total_moves

    @property
    def player1_moves(self) -> int:
        return sum(1 for p in self._move_players if p == PLAYER_1)

    @property
    def player2_moves(self) -> int:
        return sum(1 for p in self._move_players if p == PLAYER_2)

    def player_move_count(self, player: int) -> int:
        return sum(1 for p in self._move_players if p == player)

    def avg_move_time(self, player: int) -> float:
        times = [t for p, t in zip(self._move_players, self._move_times)
                 if p == player]
        return sum(times) / len(times) if times else 0.0

    @property
    def position_score_trajectory(self) -> "list[int]":
        """Position score from Player 1's perspective after each move."""
        return list(self._pos_scores)

    @property
    def move_cells(self) -> "list[tuple]":
        return list(self._move_cells)

    @property
    def move_players(self) -> "list[int]":
        return list(self._move_players)

    def last_think_time(self, player: int) -> "float | None":
        """Most recent think time for this player, or None if no move yet."""
        times = self._think_times.get(player, [])
        return times[-1] if times else None

    def total_think_time(self, player: int) -> float:
        """Cumulative think time across all moves for this player."""
        return sum(self._think_times.get(player, []))

    def winning_move_number(self) -> "int | None":
        if self.game_over_reason == "win" and self._total_moves > 0:
            return self._total_moves
        return None

    def board_fill_pct(self) -> int:
        """Percentage of the board that was filled when the game ended."""
        if self._board_size == 0:
            return 0
        total_cells = self._board_size * self._board_size
        return round(100 * self._total_moves / total_cells)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_summary(self) -> None:
        dur = self.game_duration
        m, s = divmod(int(dur), 60)
        dur_str = f"{m}m{s:02d}s" if m else f"{s}s"

        w_str = (
            "Player 1" if self.winner == PLAYER_1
            else "Player 2" if self.winner == PLAYER_2
            else "None"
        )

        logger.info("=== GAME SUMMARY ===")
        logger.info(
            "[OUTCOME] result=%s reason=%s duration=%s board_size=%d",
            w_str, self.game_over_reason, dur_str, self._board_size,
        )
        logger.info(
            "[MOVES] total=%d p1=%d p2=%d board_fill=%d%%",
            self._total_moves, self.player1_moves, self.player2_moves,
            self.board_fill_pct(),
        )
        logger.info(
            "[TIMING] avg_p1=%.2fs avg_p2=%.2fs",
            self.avg_move_time(PLAYER_1),
            self.avg_move_time(PLAYER_2),
        )
        logger.info("[TRAJECTORY] pos_scores=%s", self._pos_scores)
