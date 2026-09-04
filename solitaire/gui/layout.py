"""Parametric responsive layout manager for Solitaire Suite.

Calculates exact pixel geometries for all board piles, adaptive vertical
cascade compression to prevent screen clipping, and hit-testing for mouse interaction.
"""

from typing import Dict, List, Optional, Tuple, Any
import pygame
from solitaire.core.base_game import BaseGame
from solitaire.core.card import Card
from solitaire.core.pile import Pile, PileType


class LayoutManager:
    """Computes and maintains responsive board geometry for Klondike, FreeCell, and Spider."""

    def __init__(self) -> None:
        self.window_width: int = 1200
        self.window_height: int = 800
        self.toolbar_height: int = 56
        self.margin_x: int = 24
        self.margin_y: int = 16
        self.card_width: int = 90
        self.card_height: int = 126
        self.pile_gap_x: int = 16
        self.pile_gap_y: int = 24

        # Dynamic cache of pile and card bounding rectangles
        self.pile_rects: Dict[str, pygame.Rect] = {}
        self.card_rects: Dict[Tuple[str, int], pygame.Rect] = {}
        self.tableau_dy_down: Dict[str, int] = {}
        self.tableau_dy_up: Dict[str, int] = {}

    def update_layout(self, game: BaseGame, window_width: int, window_height: int, toolbar_height: int = 56) -> None:
        """Recalculates all pile and card bounding boxes based on window size and game mode."""
        self.window_width = max(640, window_width)
        self.window_height = max(480, window_height)
        self.toolbar_height = toolbar_height

        self.pile_rects.clear()
        self.card_rects.clear()
        self.tableau_dy_down.clear()
        self.tableau_dy_up.clear()

        mode = getattr(game, "mode_name", "").lower()
        if "freecell" in mode:
            self._layout_freecell(game)
        elif "spider" in mode:
            self._layout_spider(game)
        else:
            self._layout_klondike(game)

    # -------------------------------------------------------------------------
    # Klondike Layout (7 Tableau Columns, Stock, Waste, 4 Foundations)
    # -------------------------------------------------------------------------
    def _layout_klondike(self, game: BaseGame) -> None:
        num_cols = 7
        avail_w = self.window_width - 2 * self.margin_x
        # 7 columns with 6 gaps
        raw_w = (avail_w - (num_cols - 1) * self.pile_gap_x) / num_cols
        self.card_width = max(60, min(115, int(raw_w)))
        self.card_height = int(self.card_width * 1.4)
        total_width = num_cols * self.card_width + (num_cols - 1) * self.pile_gap_x
        start_x = max(self.margin_x, (self.window_width - total_width) // 2)

        top_y = self.toolbar_height + self.margin_y

        # Top row:
        # Col 0: Stock
        # Col 1: Waste
        # Col 2: (Empty spacer)
        # Col 3..6: Foundations 0..3
        col_x = [start_x + i * (self.card_width + self.pile_gap_x) for i in range(num_cols)]

        self.pile_rects["stock"] = pygame.Rect(col_x[0], top_y, self.card_width, self.card_height)
        self.pile_rects["waste"] = pygame.Rect(col_x[1], top_y, self.card_width, self.card_height)

        for i in range(4):
            fid = f"foundation_{i}"
            self.pile_rects[fid] = pygame.Rect(col_x[3 + i], top_y, self.card_width, self.card_height)

        # Bottom row: Tableaus 0..6
        tableau_y = top_y + self.card_height + self.pile_gap_y
        self._layout_tableau_columns(game, ["tableau_" + str(i) for i in range(num_cols)], col_x, tableau_y)

    # -------------------------------------------------------------------------
    # FreeCell Layout (8 Cascades, 4 Free Cells, 4 Foundations)
    # -------------------------------------------------------------------------
    def _layout_freecell(self, game: BaseGame) -> None:
        num_cols = 8
        avail_w = self.window_width - 2 * self.margin_x
        raw_w = (avail_w - (num_cols - 1) * self.pile_gap_x) / num_cols
        self.card_width = max(55, min(110, int(raw_w)))
        self.card_height = int(self.card_width * 1.4)
        total_width = num_cols * self.card_width + (num_cols - 1) * self.pile_gap_x
        start_x = max(self.margin_x, (self.window_width - total_width) // 2)

        top_y = self.toolbar_height + self.margin_y
        col_x = [start_x + i * (self.card_width + self.pile_gap_x) for i in range(num_cols)]

        # Top row:
        # Left 4 columns: Free Cells 0..3
        # Right 4 columns: Foundations 0..3
        for i in range(4):
            cid = f"freecell_{i}"
            self.pile_rects[cid] = pygame.Rect(col_x[i], top_y, self.card_width, self.card_height)
            self.pile_rects[f"cell_{i}"] = self.pile_rects[cid]

            fid = f"foundation_{i}"
            self.pile_rects[fid] = pygame.Rect(col_x[4 + i], top_y, self.card_width, self.card_height)

        # Bottom row: Cascades 0..7
        tableau_y = top_y + self.card_height + self.pile_gap_y
        col_names = [f"cascade_{i}" for i in range(num_cols)]
        self._layout_tableau_columns(game, col_names, col_x, tableau_y)
        # Also alias tableau_i to cascade_i
        for i in range(num_cols):
            self.pile_rects[f"tableau_{i}"] = self.pile_rects[f"cascade_{i}"]

    # -------------------------------------------------------------------------
    # Spider Layout (10 Tableau Columns, Stock, 8 Foundation slots)
    # -------------------------------------------------------------------------
    def _layout_spider(self, game: BaseGame) -> None:
        num_cols = 10
        gap_x = max(8, int(self.pile_gap_x * 0.7))
        avail_w = self.window_width - 2 * self.margin_x
        raw_w = (avail_w - (num_cols - 1) * gap_x) / num_cols
        self.card_width = max(50, min(95, int(raw_w)))
        self.card_height = int(self.card_width * 1.4)
        total_width = num_cols * self.card_width + (num_cols - 1) * gap_x
        start_x = max(self.margin_x, (self.window_width - total_width) // 2)

        top_y = self.toolbar_height + self.margin_y
        col_x = [start_x + i * (self.card_width + gap_x) for i in range(num_cols)]

        # Top row:
        # Col 0: Stock pile
        self.pile_rects["stock"] = pygame.Rect(col_x[0], top_y, self.card_width, self.card_height)

        # Foundations 0..7 (right 8 columns, or stacked)
        for i in range(8):
            fid = f"foundation_{i}"
            # Place completed foundations starting at column 2..9
            target_col = min(9, 2 + i)
            self.pile_rects[fid] = pygame.Rect(col_x[target_col], top_y, self.card_width, self.card_height)

        # Bottom row: Tableau columns 0..9
        tableau_y = top_y + self.card_height + self.pile_gap_y
        col_names = [f"tableau_{i}" for i in range(num_cols)]
        self._layout_tableau_columns(game, col_names, col_x, tableau_y)
        for i in range(num_cols):
            self.pile_rects[f"cascade_{i}"] = self.pile_rects[f"tableau_{i}"]

    # -------------------------------------------------------------------------
    # Adaptive Cascade Compression & Card Positioning
    # -------------------------------------------------------------------------
    def _layout_tableau_columns(self, game: BaseGame, col_names: List[str], col_x: List[int], start_y: int) -> None:
        avail_h = self.window_height - start_y - self.margin_y

        # Determine standard offsets
        base_dy_down = max(10, int(self.card_height * 0.16))
        base_dy_up = max(18, int(self.card_height * 0.26))

        # Check maximum height across all columns to calculate compression factor
        max_col_h = self.card_height
        for pile_id in col_names:
            pile = game.get_pile(pile_id)
            if not pile or not pile.cards:
                continue
            cards = pile.cards
            num_down = sum(1 for c in cards if not c.face_up)
            num_up = sum(1 for c in cards if c.face_up)
            # Last card occupies full card_height; preceding cards offset by dy
            h = (num_down * base_dy_down) + (max(0, num_up - 1) * base_dy_up) + self.card_height
            if h > max_col_h:
                max_col_h = h

        # Compression ratio if columns exceed available height
        scale = min(1.0, avail_h / max(1, max_col_h))
        dy_down = max(6, int(base_dy_down * scale))
        dy_up = max(12, int(base_dy_up * scale))

        for i, pile_id in enumerate(col_names):
            x = col_x[i]
            base_rect = pygame.Rect(x, start_y, self.card_width, self.card_height)
            self.pile_rects[pile_id] = base_rect
            self.tableau_dy_down[pile_id] = dy_down
            self.tableau_dy_up[pile_id] = dy_up

            pile = game.get_pile(pile_id)
            if not pile:
                continue

            cur_y = start_y
            cards = pile.cards
            for card_idx, card in enumerate(cards):
                card_rect = pygame.Rect(x, cur_y, self.card_width, self.card_height)
                self.card_rects[(pile_id, card_idx)] = card_rect
                # Step to next card
                if not card.face_up:
                    cur_y += dy_down
                else:
                    cur_y += dy_up

        # Also layout cards inside top-row piles (stock, waste, foundations, cells)
        for pid, prect in list(self.pile_rects.items()):
            if pid.startswith("tableau") or pid.startswith("cascade"):
                continue
            pile = game.get_pile(pid)
            if not pile or not pile.cards:
                continue
            # For stacked piles, top card is at the pile rect
            for card_idx in range(len(pile.cards)):
                self.card_rects[(pid, card_idx)] = prect

    # -------------------------------------------------------------------------
    # Hit Testing & Target Snapping
    # -------------------------------------------------------------------------
    def hit_test(self, x: int, y: int, game: BaseGame) -> Tuple[Optional[str], int, Optional[Card]]:
        """Determines which pile or card was clicked at coordinates (x, y).

        Returns:
            Tuple of (pile_id, card_index, card_or_None).
        """
        # 1. First check tableau / cascade columns (front to back / top card first)
        for pile_id, base_rect in self.pile_rects.items():
            if not (pile_id.startswith("tableau") or pile_id.startswith("cascade")):
                continue
            pile = game.get_pile(pile_id)
            if not pile:
                continue

            if not pile.cards:
                if base_rect.collidepoint(x, y):
                    return (pile_id, -1, None)
                continue

            # Check from top-most card down to bottom-most card
            for card_idx in range(len(pile.cards) - 1, -1, -1):
                rect = self.card_rects.get((pile_id, card_idx))
                if rect and rect.collidepoint(x, y):
                    return (pile_id, card_idx, pile.cards[card_idx])

        # 2. Check top-row piles (stock, waste, foundations, free cells)
        for pile_id, base_rect in self.pile_rects.items():
            if pile_id.startswith("tableau") or pile_id.startswith("cascade"):
                continue
            if base_rect.collidepoint(x, y):
                pile = game.get_pile(pile_id)
                if pile and pile.cards:
                    top_idx = len(pile.cards) - 1
                    return (pile_id, top_idx, pile.cards[top_idx])
                return (pile_id, -1, None)

        return (None, -1, None)

    def find_drop_target(self, drop_rect: pygame.Rect, game: BaseGame, source_pile_id: str) -> Optional[str]:
        """Finds the best target pile under the dragged card rect."""
        best_pile: Optional[str] = None
        best_overlap_area = 0

        # Check all possible piles except source pile
        for pile_id, rect in self.pile_rects.items():
            if pile_id == source_pile_id:
                continue
            # Also ignore aliases of source pile
            if (source_pile_id.startswith("cascade") or source_pile_id.startswith("tableau")) and \
               (pile_id.startswith("cascade") or pile_id.startswith("tableau")) and \
               source_pile_id.split("_")[-1] == pile_id.split("_")[-1]:
                continue

            # Calculate target collision box (for columns, use the top card or base rect)
            pile = game.get_pile(pile_id)
            target_rect = rect
            if pile and pile.cards and (pile_id.startswith("tableau") or pile_id.startswith("cascade")):
                last_idx = len(pile.cards) - 1
                card_rect = self.card_rects.get((pile_id, last_idx))
                if card_rect:
                    target_rect = card_rect

            # Compute intersection area
            if drop_rect.colliderect(target_rect):
                intersect = drop_rect.clip(target_rect)
                area = intersect.width * intersect.height
                if area > best_overlap_area:
                    best_overlap_area = area
                    best_pile = pile_id

        return best_pile
