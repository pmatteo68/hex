"""
BoardCanvas -- Tkinter canvas widget that renders the Hex grid.

The board is drawn as a parallelogram of pointy-top hexagons.
Each row is shifted right by hex_w/2 relative to the previous row,
producing the rhombus shape characteristic of Hex.

Hex geometry (pointy-top hexagon, circumradius R):
  hex_w = sqrt(3) * R    -- flat-to-flat width
  hex_h = 2 * R          -- tip-to-tip height
  row spacing  = 1.5 * R (center-to-center, vertical)
  col spacing  = hex_w   (center-to-center, horizontal)
  row offset   = hex_w/2 (each row shifts right by this amount)

Cell center (row, col):
  cx = BOARD_PADDING + hex_w/2 + col * hex_w + row * hex_w/2
  cy = BOARD_PADDING + R       + row * 1.5 * R

Vertex k of cell (cx, cy) with circumradius R (pointy-top, 0=top):
  angle = 90 - k*60  degrees
  (cx + R * cos(angle_rad),  cy - R * sin(angle_rad))

Border strips:
  Left  (P1 color): outer edges of cells in col=0
  Right (P1 color): outer edges of cells in col=n-1
  Top   (P2 color): outer edges of cells in row=0
  Bottom(P2 color): outer edges of cells in row=n-1

Click detection:
  Find the cell whose center is closest to the click point,
  then verify the click is within the hexagon polygon.
"""
import math
import tkinter as tk
import logging

import config_ui   as UI
import config_game as CG
from game_logic import PLAYER_1, PLAYER_2, EMPTY

log = logging.getLogger(__name__)

_SQRT3 = math.sqrt(3)
_NO_CELL = (-1, -1)


def _hex_vertices(cx: float, cy: float, R: float) -> list:
    """Return the 6 (x,y) vertex coordinates of a pointy-top hexagon."""
    pts = []
    for k in range(6):
        angle_rad = math.radians(90 - k * 60)
        pts.append((cx + R * math.cos(angle_rad),
                    cy - R * math.sin(angle_rad)))
    return pts


def _point_in_polygon(px: float, py: float, poly: list) -> bool:
    """Ray-casting point-in-polygon test."""
    n = len(poly)
    inside = False
    x0, y0 = poly[-1]
    for x1, y1 in poly:
        if ((y0 > py) != (y1 > py)) and (
                px < (x1 - x0) * (py - y0) / (y1 - y0 + 1e-12) + x0):
            inside = not inside
        x0, y0 = x1, y1
    return inside


class BoardCanvas(tk.Frame):
    """
    Renders the Hex game board.

    Public API:
      set_on_cell_click(callback)       -- callback(row, col)
      set_current_player(player)        -- updates ghost stone colour
      set_enabled(True/False)           -- enable/disable interaction
      set_stone(row, col, player/None)  -- paint or clear a cell
      clear_all()                       -- reset all cells to empty
      flash_win(path, player, on_done)  -- animate winning path
      replay_from_history(history)      -- silently repaint all moves
    """

    def __init__(self, parent, board_size: int, **kwargs):
        super().__init__(parent, bg=UI.BG_COLOR, **kwargs)
        self._n            = board_size
        self._enabled      = True
        self._cur_player   = PLAYER_1
        self._hover_cell   = _NO_CELL
        self._on_click_cb  = None

        R  = UI.HEX_SIZE
        hw = _SQRT3 * R
        pad = UI.BOARD_PADDING
        bw  = UI.BORDER_WIDTH

        self._R   = R
        self._hw  = hw   # hex_w
        self._pad = pad
        self._bw  = bw

        n = board_size
        self._canvas_w = int(2 * pad + 2 * bw + (n - 1) * hw * 1.5 + 1.5 * hw + 1)
        self._canvas_h = int(2 * pad + 2 * bw + n * 1.5 * R + 0.5 * R + 1)

        self._cell_ids   : "dict[tuple, int]" = {}
        self._ghost_id   : "int | None"       = None

        self._build()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_on_cell_click(self, cb) -> None:
        self._on_click_cb = cb

    def set_current_player(self, player: int) -> None:
        self._cur_player = player
        self._refresh_ghost()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self._hide_ghost()

    def set_stone(self, row: int, col: int, player) -> None:
        oid = self._cell_ids.get((row, col))
        if oid is None:
            return
        if player == PLAYER_1:
            color = UI.PLAYER_1_COLOR
        elif player == PLAYER_2:
            color = UI.PLAYER_2_COLOR
        else:
            color = UI.CELL_EMPTY_COLOR
        self._canvas.itemconfigure(oid, fill=color)

    def clear_all(self) -> None:
        for oid in self._cell_ids.values():
            self._canvas.itemconfigure(oid, fill=UI.CELL_EMPTY_COLOR)
        self._hide_ghost()

    def replay_from_history(self, history: list) -> None:
        self.clear_all()
        for player, row, col in history:
            self.set_stone(row, col, player)

    def flash_win(self, path: list, player: int, on_done) -> None:
        flash_color = (UI.WIN_FLASH_COLOR_P1 if player == PLAYER_1
                       else UI.WIN_FLASH_COLOR_P2)
        stone_color = (UI.PLAYER_1_COLOR if player == PLAYER_1
                       else UI.PLAYER_2_COLOR)
        self._flash_step(path, stone_color, flash_color,
                         CG.WIN_FLASH_COUNT, True, on_done)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self._canvas = tk.Canvas(
            self,
            width=self._canvas_w,
            height=self._canvas_h,
            bg=UI.BG_COLOR,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack()
        self._draw_borders()
        self._draw_cells()
        self._draw_ghost()
        self._canvas.bind("<Motion>",   self._on_mouse_move)
        self._canvas.bind("<Button-1>", self._on_mouse_click)
        self._canvas.bind("<Leave>",    self._on_mouse_leave)

    def _cell_center(self, row: int, col: int) -> "tuple[float,float]":
        R  = self._R
        hw = self._hw
        bw = self._bw
        pad = self._pad
        cx = pad + bw + hw / 2 + col * hw + row * hw / 2
        cy = pad + bw + R      + row * 1.5 * R
        return cx, cy

    def _draw_borders(self) -> None:
        """
        Draw the 4 edge strips that indicate player ownership.
        Left/Right (P1 color), Top/Bottom (P2 color).
        Strategy: for each border edge, draw the triangular region between
        consecutive edge cells' outer face midpoints and a parallel outer line.
        Simplified: draw thick colored lines along each outer face.
        """
        n  = self._n
        bw = self._bw
        R  = self._R

        def _outline(cells_verts, color):
            for poly in cells_verts:
                flat = [v for pt in poly for v in pt]
                self._canvas.create_polygon(flat, fill=color, outline=color)

        # Left border: outer face v4-v5 of each cell in col=0
        # We build the full border polygon: trace v5,v4 for each row,
        # then close outward to the left.
        left_inner = []
        for row in range(n):
            cx, cy = self._cell_center(row, 0)
            verts   = _hex_vertices(cx, cy, R)
            v4, v5  = verts[4], verts[5]
            left_inner.extend([v5, v4])

        left_outer = [(x - bw, y) for x, y in left_inner]
        left_poly   = left_inner + list(reversed(left_outer))
        flat = [v for pt in left_poly for v in pt]
        self._canvas.create_polygon(flat, fill=UI.BORDER_P1_COLOR,
                                    outline=UI.BORDER_P1_COLOR)

        # Right border: outer face v1-v2 of each cell in col=n-1
        right_inner = []
        for row in range(n):
            cx, cy = self._cell_center(row, n - 1)
            verts   = _hex_vertices(cx, cy, R)
            v1, v2  = verts[1], verts[2]
            right_inner.extend([v1, v2])

        right_outer = [(x + bw, y) for x, y in right_inner]
        right_poly   = right_inner + list(reversed(right_outer))
        flat = [v for pt in right_poly for v in pt]
        self._canvas.create_polygon(flat, fill=UI.BORDER_P1_COLOR,
                                    outline=UI.BORDER_P1_COLOR)

        # Top border: for row=0, outer faces are v5-v0 and v0-v1 for each col
        top_inner = []
        for col in range(n):
            cx, cy = self._cell_center(0, col)
            verts   = _hex_vertices(cx, cy, R)
            top_inner.extend([verts[5], verts[0], verts[1]])

        top_outer = [(x, y - bw) for x, y in top_inner]
        top_poly   = top_inner + list(reversed(top_outer))
        flat = [v for pt in top_poly for v in pt]
        self._canvas.create_polygon(flat, fill=UI.BORDER_P2_COLOR,
                                    outline=UI.BORDER_P2_COLOR)

        # Bottom border: for row=n-1, outer faces are v2-v3 and v3-v4 for each col
        bot_inner = []
        for col in range(n):
            cx, cy = self._cell_center(n - 1, col)
            verts   = _hex_vertices(cx, cy, R)
            bot_inner.extend([verts[2], verts[3], verts[4]])

        bot_outer = [(x, y + bw) for x, y in bot_inner]
        bot_poly   = bot_inner + list(reversed(bot_outer))
        flat = [v for pt in bot_poly for v in pt]
        self._canvas.create_polygon(flat, fill=UI.BORDER_P2_COLOR,
                                    outline=UI.BORDER_P2_COLOR)

    def _draw_cells(self) -> None:
        n = self._n
        R = self._R
        for row in range(n):
            for col in range(n):
                cx, cy = self._cell_center(row, col)
                pts     = _hex_vertices(cx, cy, R)
                flat    = [v for pt in pts for v in pt]
                oid     = self._canvas.create_polygon(
                    flat,
                    fill=UI.CELL_EMPTY_COLOR,
                    outline=UI.CELL_OUTLINE_COLOR,
                    width=UI.CELL_OUTLINE_WIDTH,
                    tags=(f"cell_{row}_{col}",),
                )
                self._cell_ids[(row, col)] = oid

    def _draw_ghost(self) -> None:
        R    = self._R
        cx, cy = self._cell_center(0, 0)
        pts   = _hex_vertices(cx, cy, R * 0.75)
        flat  = [v for pt in pts for v in pt]
        self._ghost_id = self._canvas.create_polygon(
            flat,
            fill=UI.PLAYER_1_GHOST_COLOR,
            outline="",
            state="hidden",
            tags="ghost",
        )

    # ------------------------------------------------------------------
    # Click / hover detection
    # ------------------------------------------------------------------

    def _cell_from_xy(self, x: float, y: float) -> "tuple[int,int]":
        """Return (row, col) of the hex cell under pixel (x, y), or _NO_CELL."""
        n   = self._n
        R   = self._R
        best_dist = R * R * 2
        best_cell = _NO_CELL
        for row in range(n):
            for col in range(n):
                cx, cy = self._cell_center(row, col)
                d = (x - cx) ** 2 + (y - cy) ** 2
                if d < best_dist:
                    best_dist = d
                    best_cell = (row, col)

        if best_cell == _NO_CELL:
            return _NO_CELL
        row, col = best_cell
        cx, cy   = self._cell_center(row, col)
        poly     = _hex_vertices(cx, cy, R)
        if _point_in_polygon(x, y, poly):
            return best_cell
        return _NO_CELL

    def _on_mouse_move(self, event: tk.Event) -> None:
        if not self._enabled:
            return
        cell = self._cell_from_xy(event.x, event.y)
        if cell != self._hover_cell:
            self._hover_cell = cell
            self._refresh_ghost()

    def _on_mouse_leave(self, event: tk.Event) -> None:
        self._hover_cell = _NO_CELL
        self._hide_ghost()

    def _on_mouse_click(self, event: tk.Event) -> None:
        if not self._enabled:
            return
        cell = self._cell_from_xy(event.x, event.y)
        if cell == _NO_CELL:
            return
        log.debug("Board click cell=%s", cell)
        if self._on_click_cb:
            self._on_click_cb(cell[0], cell[1])

    # ------------------------------------------------------------------
    # Ghost stone helpers
    # ------------------------------------------------------------------

    def _refresh_ghost(self) -> None:
        if self._hover_cell == _NO_CELL or not self._enabled:
            self._hide_ghost()
            return
        row, col   = self._hover_cell
        cx, cy     = self._cell_center(row, col)
        R          = self._R
        pts        = _hex_vertices(cx, cy, R * 0.75)
        flat       = [v for pt in pts for v in pt]
        ghost_color = (UI.PLAYER_1_GHOST_COLOR if self._cur_player == PLAYER_1
                       else UI.PLAYER_2_GHOST_COLOR)
        self._canvas.coords(self._ghost_id, flat)
        self._canvas.itemconfigure(self._ghost_id,
                                   fill=ghost_color, state="normal")

    def _hide_ghost(self) -> None:
        if self._ghost_id is not None:
            self._canvas.itemconfigure(self._ghost_id, state="hidden")

    # ------------------------------------------------------------------
    # Win flash animation
    # ------------------------------------------------------------------

    def _flash_step(self, path: list, stone_color: str, flash_color: str,
                    remaining: int, flash_on: bool, on_done) -> None:
        color = flash_color if flash_on else stone_color
        for row, col in path:
            oid = self._cell_ids.get((row, col))
            if oid is not None:
                self._canvas.itemconfigure(oid, fill=color)

        if remaining == 0:
            for row, col in path:
                oid = self._cell_ids.get((row, col))
                if oid is not None:
                    self._canvas.itemconfigure(oid, fill=stone_color)
            on_done()
            return

        self._canvas.after(
            CG.WIN_FLASH_INTERVAL_MS,
            lambda: self._flash_step(path, stone_color, flash_color,
                                     remaining - 1, not flash_on, on_done),
        )
