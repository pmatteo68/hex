"""
Configuration for the MCTS (Monte Carlo Tree Search) Hex engine.

--- Iteration count ---
MCTS_ITERATIONS controls how many simulations are run per move.
More iterations = stronger play but longer thinking time.

Typical iteration counts vs. compute time on a standard desktop (11x11):
  1000  -- < 0.5 s  (fast, weak)
  3000  -- 0.5-1.5 s  (good balance, default)
  5000  -- 1.5-3 s    (strong)
  10000 -- several seconds; for maximum strength

--- UCB exploration constant ---
MCTS_UCB_C is the UCT exploration constant.
Standard value is sqrt(2) ~ 1.414.
Lower = exploit known-good lines more; Higher = explore more.
Typical range: 0.7 -- 2.0

--- RAVE (Rapid Action Value Estimation) ---
RAVE dramatically improves Hex MCTS by using the "All Moves As First"
principle: a move that turned out to be good in any part of a rollout is
treated as if it had been played first.

MCTS_RAVE_ENABLED: set to False to disable RAVE (pure UCT).
MCTS_RAVE_K: equivalence parameter controlling how fast RAVE influence
  fades as the regular visit count grows.
  beta = sqrt(K / (3 * parent_visits + K))
  When parent_visits = K/3, beta ~ 0.7  (mostly RAVE)
  When parent_visits = K,   beta ~ 0.5  (half/half)
  When parent_visits = 3K,  beta ~ 0.3  (mostly UCT)
  Typical range: 100 -- 2000

--- Virtual-path threat awareness ---
Before each simulation the engine computes the opponent's shortest virtual
connection path (0-1 BFS over empty and own cells). The empty cells on that
path are "threat cells" -- blocking them directly harms the opponent's best
route.

MCTS_EXPAND_THREAT_BIAS: probability that a tree expansion picks a
  threat-aware move rather than falling through to adjacency or random.
  When triggered, the priority is:
    1. Dual-purpose cell (on BOTH players' paths) -- best Hex move.
    2. Opponent's path cell (blocking only).
    3. Own path cell (advancing only).
  P2 therefore always targets P1's path first; P1 targets P2's path first.
  0.0 = no threat guidance; 1.0 = always use threat priority when possible.
  Typical range: 0.7 -- 0.95

MCTS_ROLLOUT_BLOCK_BIAS: in each rollout the empty cells are shuffled, then
  a fraction of the defending player's turn-slots are swapped with threat
  cells so the simulated defender plays them early. This makes rollout
  outcomes more realistic (the opponent does not simply walk through
  uncontested).
  0.0 = pure random shuffle; 1.0 = move all threat cells to defender's turns.
  Typical range: 0.4 -- 0.8

--- Expansion adjacency bias ---
MCTS_EXPAND_ADJ_BIAS: fraction of expansions (when no threat cells are
  available) that prefer moves adjacent to existing stones.
  Typical range: 0.0 -- 0.8

--- Rollout adjacency bias ---
MCTS_ROLLOUT_ADJ_BIAS: fraction of rollout moves that prefer cells adjacent
  to the current player's own stones. 0.0 uses the fast shuffle path.
  Typical range: 0.0 -- 0.5

--- First move bonus ---
MCTS_FIRST_MOVE_ITERATIONS: extra simulations for the very first move.
  Set to 0 because RAVE and threat awareness already guide the opening.
"""

MCTS_ITERATIONS            = 5000
MCTS_UCB_C                 = 1.414

MCTS_RAVE_ENABLED          = True
MCTS_RAVE_K                = 500

MCTS_EXPAND_THREAT_BIAS    = 0.92
MCTS_EXPAND_ADJ_BIAS       = 0.5
MCTS_ROLLOUT_BLOCK_BIAS    = 0.7
MCTS_ROLLOUT_ADJ_BIAS      = 0.0

MCTS_FIRST_MOVE_ITERATIONS = 0

# --- Tactical depth (forced blocking pre-check) ---
# When the opponent's virtual path contains <= MCTS_TACTICAL_DEPTH empty cells,
# the engine skips MCTS and instead evaluates every candidate blocking move by
# re-running the BFS after tentatively placing a stone, then picks the block
# that maximally increases the opponent's resulting path length.
#
# This guarantees a reactive block on short threats (e.g. a straight-line
# attack that has 2-4 cells left to complete) without relying on MCTS rollouts
# to find the signal in the noise.
#
# Setting this to 1 is equivalent to the existing 1-ply block check only.
# Raising it above 5 may add noticeable latency (k BFS calls per move).
# Typical range: 2 -- 5
MCTS_TACTICAL_DEPTH = 4
