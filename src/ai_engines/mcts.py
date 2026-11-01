"""
Monte Carlo Tree Search (MCTS) engine for Hex with RAVE and threat awareness.

Algorithm: UCT + RAVE + Virtual-Path Threat Awareness.

  Selection  : UCB-RAVE blends regular UCT with AMAF win rates.
  Expansion  : one new child per visit; uses player-specific blocking priority:
                 1. Dual-purpose cells (on BOTH players' virtual paths)
                    -- these advance the expander AND block the opponent.
                 2. Opponent's threat cells  -- pure defensive blocking.
                 3. Own threat cells         -- pure offensive advancing.
                 4. Adjacency bias.
                 5. Uniformly random.
               The bias probability is MCTS_EXPAND_THREAT_BIAS.
  Simulation : random rollout using Union-Find for O(alpha(n)) win
               detection; "key cells" (union of both players' virtual
               path cells) are placed at the front of the rollout order
               so both players race for them early (MCTS_ROLLOUT_BLOCK_BIAS).
  Backprop   : update UCT counts AND AMAF counts (RAVE principle).

Virtual-path threat awareness:
  Before each MCTS search two 0-1 BFS passes compute the empty cells on
  each player's shortest virtual connection path (own cells cost 0, empty
  cells cost 1, opponent cells are blocked).

  key_cells  = P1_threats UNION P2_threats  (used in rollouts only)
  opp_threats = opponent's threat set        (used per-player in expansion)

  The key distinction from a naive union approach: during tree expansion
  P2 specifically targets P1's path (blocking), while P1 targets P2's
  path.  Moves on BOTH paths (dual-purpose) are tried first because they
  serve two roles at once -- the highest-leverage play in Hex.

  1-ply tactical pre-check (before MCTS):
    If the calling player can win in one move, take it immediately.
    If the opponent can win in one move, block it immediately.
    These cases are too obvious to waste search budget on.

Union-Find virtual nodes:
  n*n   = start-edge virtual node
  n*n+1 = goal-edge virtual node
  Player 1 (left-right): win when vstart and vgoal are connected.
  Player 2 (top-bottom): win when vstart and vgoal are connected.

RAVE (All Moves As First):
  If move m was played by player P at any point in a rollout, its AMAF
  statistics on the ancestor nodes are updated as if P had played m first.
    beta = sqrt(K / (3 * parent_visits + K))
    score = (1 - beta) * uct + beta * amaf
"""
import math
import random
import logging
from collections import deque as _deque

from .base import HexAIEngine, EMPTY, PLAYER_1, PLAYER_2
from .mcts_config import (
    MCTS_ITERATIONS,
    MCTS_UCB_C,
    MCTS_RAVE_ENABLED,
    MCTS_RAVE_K,
    MCTS_EXPAND_THREAT_BIAS,
    MCTS_EXPAND_ADJ_BIAS,
    MCTS_ROLLOUT_BLOCK_BIAS,
    MCTS_ROLLOUT_ADJ_BIAS,
    MCTS_FIRST_MOVE_ITERATIONS,
    MCTS_TACTICAL_DEPTH,
)

logger = logging.getLogger(__name__)

_OTHER = {PLAYER_1: PLAYER_2, PLAYER_2: PLAYER_1}

_HEX_NEIGHBORS = ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0))


# ---------------------------------------------------------------------------
# Union-Find
# ---------------------------------------------------------------------------

class _UF:
    __slots__ = ("_parent", "_rank")

    def __init__(self, size: int):
        self._parent = list(range(size))
        self._rank   = [0] * size

    def find(self, x: int) -> int:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self._rank[ra] < self._rank[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        if self._rank[ra] == self._rank[rb]:
            self._rank[ra] += 1

    def connected(self, a: int, b: int) -> bool:
        return self.find(a) == self.find(b)


def _make_uf(board: list, n: int, player: int) -> "_UF":
    """Build a Union-Find from an existing board for the given player."""
    size   = n * n + 2
    vstart = n * n
    vgoal  = n * n + 1
    uf     = _UF(size)

    for r in range(n):
        for c in range(n):
            if board[r * n + c] == player:
                idx = r * n + c
                for dr, dc in _HEX_NEIGHBORS:
                    r2, c2 = r + dr, c + dc
                    if 0 <= r2 < n and 0 <= c2 < n:
                        if board[r2 * n + c2] == player:
                            uf.union(idx, r2 * n + c2)
                if player == PLAYER_1:
                    if c == 0:
                        uf.union(idx, vstart)
                    if c == n - 1:
                        uf.union(idx, vgoal)
                else:
                    if r == 0:
                        uf.union(idx, vstart)
                    if r == n - 1:
                        uf.union(idx, vgoal)

    return uf


def _place_uf(uf: _UF, board: list, idx: int, player: int, n: int) -> None:
    """Update the union-find after placing player's stone at flat index idx."""
    r, c   = divmod(idx, n)
    vstart = n * n
    vgoal  = n * n + 1
    for dr, dc in _HEX_NEIGHBORS:
        r2, c2 = r + dr, c + dc
        if 0 <= r2 < n and 0 <= c2 < n:
            if board[r2 * n + c2] == player:
                uf.union(idx, r2 * n + c2)
    if player == PLAYER_1:
        if c == 0:
            uf.union(idx, vstart)
        if c == n - 1:
            uf.union(idx, vgoal)
    else:
        if r == 0:
            uf.union(idx, vstart)
        if r == n - 1:
            uf.union(idx, vgoal)


# ---------------------------------------------------------------------------
# Board helpers
# ---------------------------------------------------------------------------

def _adjacent_to_any_stone(r: int, c: int, board: list, n: int) -> bool:
    """True if (r, c) has at least one occupied neighbour."""
    for dr, dc in _HEX_NEIGHBORS:
        r2, c2 = r + dr, c + dc
        if 0 <= r2 < n and 0 <= c2 < n and board[r2 * n + c2] != EMPTY:
            return True
    return False


def _adjacent_to_player(idx: int, board: list, n: int, player: int) -> bool:
    """True if flat index idx has at least one neighbour owned by player."""
    r, c = divmod(idx, n)
    for dr, dc in _HEX_NEIGHBORS:
        r2, c2 = r + dr, c + dc
        if 0 <= r2 < n and 0 <= c2 < n and board[r2 * n + c2] == player:
            return True
    return False


# ---------------------------------------------------------------------------
# Virtual-path threat detection
# ---------------------------------------------------------------------------

def _virtual_threat_cells(board: list, n: int, player: int) -> list:
    """
    Return the flat indices of EMPTY cells on the shortest virtual
    connection path for player (0-1 BFS: own=0, empty=1, opp=blocked).
    Returns [] if the opponent has cut all routes.

    These are the "threat cells": playing on them simultaneously advances
    the caller's connectivity and disrupts the opponent's shortest route.
    """
    opponent = _OTHER[player]
    INF      = n * n + 2

    dist = [INF] * (n * n)
    prev = [-2]  * (n * n)  # -2 = unvisited; -1 = came from virtual start

    if player == PLAYER_1:
        starts  = [r * n for r in range(n) if board[r * n] != opponent]
        is_goal = lambda i: i % n == n - 1          # noqa: E731
    else:
        starts  = [c for c in range(n) if board[c] != opponent]
        is_goal = lambda i: i >= (n - 1) * n        # noqa: E731

    dq = _deque()
    for idx in starts:
        cost = 0 if board[idx] == player else 1
        if cost < dist[idx]:
            dist[idx] = cost
            prev[idx] = -1
            if cost == 0:
                dq.appendleft(idx)
            else:
                dq.append(idx)

    goal_idx = -1
    while dq:
        idx = dq.popleft()
        if is_goal(idx):
            goal_idx = idx
            break
        d    = dist[idx]
        r, c = divmod(idx, n)
        for dr, dc in _HEX_NEIGHBORS:
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < n and 0 <= c2 < n:
                idx2 = r2 * n + c2
                if board[idx2] == opponent:
                    continue
                step = 0 if board[idx2] == player else 1
                nd   = d + step
                if nd < dist[idx2]:
                    dist[idx2] = nd
                    prev[idx2] = idx
                    if step == 0:
                        dq.appendleft(idx2)
                    else:
                        dq.append(idx2)

    if goal_idx == -1:
        return []

    cells = []
    cur   = goal_idx
    while cur >= 0:   # prev == -1 is "from virtual start"; loop stops there
        if board[cur] == EMPTY:
            cells.append(cur)
        cur = prev[cur]

    return cells


# ---------------------------------------------------------------------------
# Tactical blocking helper
# ---------------------------------------------------------------------------

def _find_best_block(board: list, n: int,
                     opp_threat_cells: list,
                     opponent: int,
                     blocker: int) -> int:
    """
    Given the opponent's current virtual-path threat cells, return the flat
    index of the blocking move that maximally increases the opponent's
    resulting path length (i.e. forces the longest possible detour).

    Blocking a cell that cuts ALL of the opponent's routes returns a path
    length of n*n+1 (treated as infinity), which will always be preferred.

    This is O(k * BFS) where k = len(opp_threat_cells).
    """
    INF = n * n + 1
    best_idx     = opp_threat_cells[0]
    best_new_len = -1

    for idx in opp_threat_cells:
        board[idx] = blocker
        new_cells  = _virtual_threat_cells(board, n, opponent)
        new_len    = len(new_cells) if new_cells else INF
        board[idx] = EMPTY

        if new_len > best_new_len:
            best_new_len = new_len
            best_idx     = idx

    return best_idx


# ---------------------------------------------------------------------------
# MCTS Node
# ---------------------------------------------------------------------------

class _Node:
    __slots__ = ("move", "player", "parent", "children",
                 "visits", "wins", "untried",
                 "amaf_wins", "amaf_visits")

    def __init__(self, move, player, parent, untried):
        self.move        = move
        self.player      = player
        self.parent      = parent
        self.children    = []
        self.visits      = 0
        self.wins        = 0.0
        self.untried     = untried
        self.amaf_wins   = 0.0
        self.amaf_visits = 0

    def ucb_score(self, c: float, rave_k: float) -> float:
        if self.visits == 0:
            return float("inf")
        uct = (self.wins / self.visits
               + c * math.sqrt(math.log(self.parent.visits) / self.visits))
        if not MCTS_RAVE_ENABLED or rave_k <= 0 or self.amaf_visits == 0:
            return uct
        beta = math.sqrt(rave_k / (3.0 * self.parent.visits + rave_k))
        amaf = self.amaf_wins / self.amaf_visits
        return (1.0 - beta) * uct + beta * amaf

    def best_child(self, c: float, rave_k: float) -> "_Node":
        return max(self.children, key=lambda ch: ch.ucb_score(c, rave_k))

    def is_fully_expanded(self) -> bool:
        return len(self.untried) == 0


# ---------------------------------------------------------------------------
# Expansion helper
# ---------------------------------------------------------------------------

def _pick_expansion(untried: list, board: list, n: int,
                    own_threats: frozenset,
                    opp_threats: frozenset) -> tuple:
    """
    Choose an untried move for the expanding player.

    Priority order (all gated by one random draw < MCTS_EXPAND_THREAT_BIAS):
      1. Dual-purpose: cell is on BOTH the expander's path AND the
         opponent's path.  Playing here advances the expander's own
         virtual connection while simultaneously blocking the opponent's
         shortest route -- the highest-leverage move in Hex.
      2. Blocking: cell is on the opponent's virtual path only.
         Disrupts the opponent's best route.
      3. Advancing: cell is on the expander's own virtual path only.
         Extends the expander's connectivity.
      4. Adjacency bias (MCTS_EXPAND_ADJ_BIAS): a move next to any stone.
      5. Uniformly random.
    """
    if MCTS_EXPAND_THREAT_BIAS > 0.0 and random.random() < MCTS_EXPAND_THREAT_BIAS:
        # Dual-purpose first
        if own_threats and opp_threats:
            dual = [(r, c) for r, c in untried
                    if (r * n + c) in own_threats and (r * n + c) in opp_threats]
            if dual:
                return random.choice(dual)

        # Blocking second (most defensive-urgent)
        if opp_threats:
            blocking = [(r, c) for r, c in untried if (r * n + c) in opp_threats]
            if blocking:
                return random.choice(blocking)

        # Advancing third
        if own_threats:
            advancing = [(r, c) for r, c in untried if (r * n + c) in own_threats]
            if advancing:
                return random.choice(advancing)

    if MCTS_EXPAND_ADJ_BIAS > 0.0 and random.random() < MCTS_EXPAND_ADJ_BIAS:
        adj = [(r, c) for r, c in untried
               if _adjacent_to_any_stone(r, c, board, n)]
        if adj:
            return random.choice(adj)

    return random.choice(untried)


# ---------------------------------------------------------------------------
# Rollout
# ---------------------------------------------------------------------------

def _rollout(board: list, n: int, current_player: int,
             uf1: _UF, uf2: _UF, key_cells: frozenset) -> tuple:
    """
    Play a game to completion from the current position.
    Returns (winner, sim_moves) where sim_moves = list of (player, flat_idx).
    Modifies board, uf1, uf2 in place -- always pass copies.

    key_cells: union of both players' virtual path cells. With probability
    MCTS_ROLLOUT_BLOCK_BIAS these are sorted to the FRONT of the empty list
    so both players naturally race for them in alternating turns.  This
    produces realistic "fight for the key squares" simulations without
    biasing either player's behaviour specifically -- the race is symmetric
    so neither player gets an artificial advantage.
    """
    vstart = n * n
    vgoal  = n * n + 1

    empty = [i for i, v in enumerate(board) if v == EMPTY]
    random.shuffle(empty)

    # Bring key cells to the front so both players compete for them early.
    if key_cells and MCTS_ROLLOUT_BLOCK_BIAS > 0.0:
        if random.random() < MCTS_ROLLOUT_BLOCK_BIAS:
            key_first = [v for v in empty if v in key_cells]
            rest      = [v for v in empty if v not in key_cells]
            empty = key_first + rest

    adj_bias  = MCTS_ROLLOUT_ADJ_BIAS
    sim_moves = []
    player    = current_player

    if adj_bias <= 0.0:
        # Fast path: iterate the (possibly reordered) list directly.
        for idx in empty:
            board[idx] = player
            sim_moves.append((player, idx))
            if player == PLAYER_1:
                _place_uf(uf1, board, idx, player, n)
                if uf1.connected(vstart, vgoal):
                    return PLAYER_1, sim_moves
            else:
                _place_uf(uf2, board, idx, player, n)
                if uf2.connected(vstart, vgoal):
                    return PLAYER_2, sim_moves
            player = _OTHER[player]
        return PLAYER_1, sim_moves

    # Adjacency-biased path (slower; only active when MCTS_ROLLOUT_ADJ_BIAS>0).
    remaining = list(empty)
    while remaining:
        if random.random() < adj_bias:
            adj = [idx for idx in remaining
                   if _adjacent_to_player(idx, board, n, player)]
            idx = random.choice(adj) if adj else random.choice(remaining)
        else:
            idx = random.choice(remaining)
        remaining.remove(idx)
        board[idx] = player
        sim_moves.append((player, idx))
        if player == PLAYER_1:
            _place_uf(uf1, board, idx, player, n)
            if uf1.connected(vstart, vgoal):
                return PLAYER_1, sim_moves
        else:
            _place_uf(uf2, board, idx, player, n)
            if uf2.connected(vstart, vgoal):
                return PLAYER_2, sim_moves
        player = _OTHER[player]
    return PLAYER_1, sim_moves


# ---------------------------------------------------------------------------
# MCTS engine
# ---------------------------------------------------------------------------

class MCTSEngine(HexAIEngine):

    def get_name(self) -> str:
        rave = "+RAVE" if MCTS_RAVE_ENABLED else ""
        return (f"MCTS{rave}+Threats+Tactical"
                f" ({MCTS_ITERATIONS} iters, depth={MCTS_TACTICAL_DEPTH})")

    def reset(self) -> None:
        logger.debug("MCTSEngine reset")

    def _compute_next_move(self, board: list, player: int,
                           board_size: int) -> tuple:
        n     = board_size
        empty = [(r, c)
                 for r in range(n) for c in range(n)
                 if board[r * n + c] == EMPTY]

        if not empty:
            return (0, 0)
        if len(empty) == 1:
            return empty[0]

        # ------------------------------------------------------------------
        # Compute threat cells for both players ONCE (cheap; reused by all
        # iterations).
        # ------------------------------------------------------------------
        p1_threats = _virtual_threat_cells(board, n, PLAYER_1)
        p2_threats = _virtual_threat_cells(board, n, PLAYER_2)
        key_cells  = frozenset(p1_threats) | frozenset(p2_threats)

        p1_threat_set = frozenset(p1_threats)
        p2_threat_set = frozenset(p2_threats)

        my_threats  = p1_threats if player == PLAYER_1 else p2_threats
        opp_threats = p2_threats if player == PLAYER_1 else p1_threats

        logger.debug(
            "Threats: P1=%d cells, P2=%d cells, key=%d",
            len(p1_threats), len(p2_threats), len(key_cells),
        )

        # ------------------------------------------------------------------
        # 1-ply tactical pre-check: instant win or instant block.
        # ------------------------------------------------------------------
        if len(my_threats) == 1:
            logger.debug("1-ply WIN at flat=%d", my_threats[0])
            return divmod(my_threats[0], n)

        if len(opp_threats) == 1:
            logger.debug("1-ply BLOCK at flat=%d", opp_threats[0])
            return divmod(opp_threats[0], n)

        # ------------------------------------------------------------------
        # Tactical pre-check: for short opponent paths (2..TACTICAL_DEPTH),
        # pick the blocking move that maximally extends the opponent's path.
        # This is deterministic and far more reliable than MCTS for threats
        # that random rollouts cannot resolve (e.g. a nearly-complete line).
        # ------------------------------------------------------------------
        if 1 < len(opp_threats) <= MCTS_TACTICAL_DEPTH:
            block_idx = _find_best_block(
                board, n, opp_threats, _OTHER[player], player
            )
            logger.debug(
                "tactical BLOCK flat=%d (opp_path_len=%d)", block_idx, len(opp_threats)
            )
            return divmod(block_idx, n)

        # ------------------------------------------------------------------
        # Full MCTS search.
        # ------------------------------------------------------------------
        root       = _Node(None, None, None, list(empty))
        total_done = n * n - len(empty)
        iters      = MCTS_ITERATIONS + (MCTS_FIRST_MOVE_ITERATIONS
                                        if total_done == 0 else 0)
        rave_k     = max(1.0, float(MCTS_RAVE_K)) if MCTS_RAVE_ENABLED else 0.0

        for _ in range(iters):
            node   = root
            sim_bd = board[:]
            sim_p  = player
            path   = []

            # --- Selection ---
            while node.is_fully_expanded() and node.children:
                node  = node.best_child(MCTS_UCB_C, rave_k)
                r, c  = node.move
                sim_bd[r * n + c] = node.player
                sim_p = _OTHER[node.player]
                path.append(node)

            # --- Expansion ---
            if node.untried:
                # sim_p is the player about to move.
                # They want to block _OTHER[sim_p]'s path first.
                if sim_p == PLAYER_1:
                    own_t = p1_threat_set
                    opp_t = p2_threat_set
                else:
                    own_t = p2_threat_set
                    opp_t = p1_threat_set

                move  = _pick_expansion(node.untried, sim_bd, n, own_t, opp_t)
                node.untried.remove(move)
                r, c  = move
                sim_bd[r * n + c] = sim_p
                child = _Node(move, sim_p, node, [
                    (r2, c2)
                    for r2 in range(n) for c2 in range(n)
                    if sim_bd[r2 * n + c2] == EMPTY
                ])
                node.children.append(child)
                node  = child
                path.append(node)
                sim_p = _OTHER[sim_p]

            # --- Simulation ---
            uf1    = _make_uf(sim_bd, n, PLAYER_1)
            uf2    = _make_uf(sim_bd, n, PLAYER_2)
            winner, sim_moves = _rollout(sim_bd[:], n, sim_p,
                                         uf1, uf2, key_cells)

            # --- Backpropagation ---
            if MCTS_RAVE_ENABLED:
                amaf_p1 = frozenset(idx for p, idx in sim_moves if p == PLAYER_1)
                amaf_p2 = frozenset(idx for p, idx in sim_moves if p == PLAYER_2)

            root.visits += 1

            for cur in path:
                cur.visits += 1
                if cur.player == winner:
                    cur.wins += 1.0
                if MCTS_RAVE_ENABLED and cur.move is not None:
                    move_idx = cur.move[0] * n + cur.move[1]
                    amaf_set = amaf_p1 if cur.player == PLAYER_1 else amaf_p2
                    if move_idx in amaf_set:
                        cur.amaf_visits += 1
                        if cur.player == winner:
                            cur.amaf_wins += 1.0

        best = (max(root.children, key=lambda ch: ch.visits)
                if root.children else None)
        if best is None:
            return random.choice(empty)

        logger.debug(
            "MCTS chose %s  visits=%d  win_rate=%.2f  amaf_visits=%d",
            best.move, best.visits,
            best.wins / best.visits if best.visits else 0.0,
            best.amaf_visits,
        )
        return best.move


def create() -> MCTSEngine:
    return MCTSEngine()
