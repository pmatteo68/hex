"""
Core Hex game logic. No UI imports.

Board layout:
  board[row][col]  -- row 0 is the TOP edge, row (n-1) is the BOTTOM edge.
  Values: EMPTY=0, PLAYER_1=1, PLAYER_2=2.

Connectivity:
  Each cell (r, c) has up to 6 hex neighbors:
    (r-1,c), (r-1,c+1), (r,c-1), (r,c+1), (r+1,c-1), (r+1,c)

Win condition:
  PLAYER_1 wins by forming a connected path of their stones from
    column 0 (left edge)  to column n-1 (right edge).
  PLAYER_2 wins by forming a connected path from
    row 0 (top edge) to row n-1 (bottom edge).
  Hex has no draws (Hex theorem).

Game phases:
  PHASE_PLAYER1_TURN -- Player 1 is about to move
  PHASE_PLAYER2_TURN -- Player 2 is about to move
  PHASE_DONE         -- game over (one player has won)
"""
import logging
from collections import deque
from config_game import (
    BOARD_SIZE_DEFAULT,
    NUM_PLAYERS,
)

logger = logging.getLogger(__name__)

EMPTY    = 0
PLAYER_1 = 1
PLAYER_2 = 2

OTHER_PLAYER = {PLAYER_1: PLAYER_2, PLAYER_2: PLAYER_1}

PHASE_PLAYER1_TURN = "player1_turn"
PHASE_PLAYER2_TURN = "player2_turn"
PHASE_DONE         = "done"

HEX_NEIGHBORS = ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0))


def make_board(n: int) -> "list[list[int]]":
    return [[EMPTY] * n for _ in range(n)]


def get_neighbors(row: int, col: int, n: int) -> "list[tuple[int,int]]":
    result = []
    for dr, dc in HEX_NEIGHBORS:
        r2, c2 = row + dr, col + dc
        if 0 <= r2 < n and 0 <= c2 < n:
            result.append((r2, c2))
    return result


def find_winner(board: "list[list[int]]", last_player: int,
                last_row: int, last_col: int, n: int) -> "int | None":
    """
    Check whether last_player just completed a winning path.
    Returns last_player if they won, else None.
    Uses BFS from the starting edge, checking only the last-player's cells.
    """
    player = last_player

    if player == PLAYER_1:
        sources    = [(r, 0) for r in range(n) if board[r][0] == player]
        goal_check = lambda r, c: c == n - 1
    else:
        sources    = [(0, c) for c in range(n) if board[0][c] == player]
        goal_check = lambda r, c: r == n - 1

    if not sources:
        return None

    visited = set()
    queue = deque()
    for cell in sources:
        if cell not in visited:
            visited.add(cell)
            queue.append(cell)

    while queue:
        r, c = queue.popleft()
        if goal_check(r, c):
            return player
        for r2, c2 in get_neighbors(r, c, n):
            if (r2, c2) not in visited and board[r2][c2] == player:
                visited.add((r2, c2))
                queue.append((r2, c2))

    return None


def find_winning_path(board: "list[list[int]]", player: int, n: int) -> "list[tuple] | None":
    """
    Return a shortest path (list of (row,col) tuples) from the player's
    start edge to their goal edge, or None if no winning path exists.
    Uses BFS with parent tracking.
    """
    if player == PLAYER_1:
        sources = [(r, 0) for r in range(n) if board[r][0] == player]
        goal_check = lambda r, c: c == n - 1
    else:
        sources = [(0, c) for c in range(n) if board[0][c] == player]
        goal_check = lambda r, c: r == n - 1

    if not sources:
        return None

    parent = {}
    queue = deque()
    for cell in sources:
        parent[cell] = None
        queue.append(cell)

    goal_cell = None
    while queue:
        r, c = queue.popleft()
        if goal_check(r, c):
            goal_cell = (r, c)
            break
        for r2, c2 in get_neighbors(r, c, n):
            if (r2, c2) not in parent and board[r2][c2] == player:
                parent[(r2, c2)] = (r, c)
                queue.append((r2, c2))

    if goal_cell is None:
        return None

    path = []
    cur = goal_cell
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def shortest_virtual_path(board: "list[list[int]]", player: int, n: int) -> int:
    """
    Return the length of the shortest virtual path from the player's start
    edge to their goal edge using the resistance-distance heuristic:
      own cell  -> cost 0
      empty cell-> cost 1
      opponent  -> unreachable (infinite cost, skipped)

    Uses 0-1 BFS (deque).  Returns a large sentinel if no path exists
    (opponent has already won the board on that axis).
    """
    opponent = OTHER_PLAYER[player]
    INF = n * n + 1

    if player == PLAYER_1:
        start_cells = range(n)
        goal_check  = lambda r, c: c == n - 1
        start_gen   = lambda idx: (idx, 0)
    else:
        start_cells = range(n)
        goal_check  = lambda r, c: r == n - 1
        start_gen   = lambda idx: (0, idx)

    dist = [[INF] * n for _ in range(n)]
    dq = deque()

    for idx in start_cells:
        r, c = start_gen(idx)
        val = board[r][c]
        if val == opponent:
            continue
        cost = 0 if val == player else 1
        if cost < dist[r][c]:
            dist[r][c] = cost
            if cost == 0:
                dq.appendleft((r, c))
            else:
                dq.append((r, c))

    while dq:
        r, c = dq.popleft()
        d = dist[r][c]
        if goal_check(r, c):
            return d
        for r2, c2 in get_neighbors(r, c, n):
            val = board[r2][c2]
            if val == opponent:
                continue
            step = 0 if val == player else 1
            nd = d + step
            if nd < dist[r2][c2]:
                dist[r2][c2] = nd
                if step == 0:
                    dq.appendleft((r2, c2))
                else:
                    dq.append((r2, c2))

    return INF


def evaluate_position(board: "list[list[int]]", n: int) -> int:
    """
    Heuristic position score from Player 1's perspective.
    Positive = good for Player 1, negative = good for Player 2.
    Used by game_stats to build the advantage trajectory.
    Returns (P2 virtual path length) - (P1 virtual path length).
    """
    p1_path = shortest_virtual_path(board, PLAYER_1, n)
    p2_path = shortest_virtual_path(board, PLAYER_2, n)
    return p2_path - p1_path


class GameState:
    """Full Hex game state."""

    def __init__(self,
                 first_player: int,
                 board_size: int = BOARD_SIZE_DEFAULT):
        self.board_size     = board_size
        self.board          = make_board(board_size)
        self.move_history   : "list[tuple[int,int,int]]" = []  # (player, row, col)
        self.winner         : "int | None"  = None
        self.winning_path   : "list[tuple] | None" = None
        self.game_over      = False

        self.current_player = first_player
        self.phase = (PHASE_PLAYER1_TURN if first_player == PLAYER_1
                      else PHASE_PLAYER2_TURN)

        logger.debug(
            "GameState init: size=%d first_player=%d",
            board_size, first_player,
        )

    def get_empty_cells(self) -> "list[tuple[int,int]]":
        n = self.board_size
        return [
            (r, c)
            for r in range(n)
            for c in range(n)
            if self.board[r][c] == EMPTY
        ]

    def place_stone(self, row: int, col: int) -> None:
        """
        Place the current player's stone at (row, col).
        Raises ValueError if the cell is occupied or out of range.
        """
        n = self.board_size
        if not (0 <= row < n and 0 <= col < n):
            raise ValueError(
                f"Cell ({row},{col}) out of range for board size {n}"
            )
        if self.board[row][col] != EMPTY:
            raise ValueError(f"Cell ({row},{col}) is already occupied")

        player = self.current_player
        self.board[row][col] = player
        self.move_history.append((player, row, col))
        logger.debug(
            "Player %d places at (%d,%d)  move #%d",
            player, row, col, len(self.move_history),
        )

        winner = find_winner(self.board, player, row, col, n)
        if winner is not None:
            self.winner      = winner
            self.winning_path = find_winning_path(self.board, winner, n)
            self.game_over   = True
            self.phase       = PHASE_DONE
            logger.debug(
                "Player %d wins!  Path length=%d",
                winner, len(self.winning_path) if self.winning_path else 0,
            )
        else:
            next_p = OTHER_PLAYER[player]
            self.current_player = next_p
            self.phase = (PHASE_PLAYER1_TURN if next_p == PLAYER_1
                          else PHASE_PLAYER2_TURN)
