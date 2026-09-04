"""Interaction controller for Solitaire Suite.

Manages mouse input, drag-and-drop mechanics with elevation shadows and snap-back,
smart click-to-move auto-routing, and hover/hint highlight feedback.
"""

import math
import time
from typing import Optional, List, Tuple, Dict, Any
import pygame
from solitaire.core.base_game import BaseGame, Move, MoveResult
from solitaire.core.card import Card
from solitaire.gui.card_renderer import CardRenderer
from solitaire.gui.layout import LayoutManager


class DragContext:
    """Encapsulates the state of cards currently being dragged by the player."""

    def __init__(
        self,
        cards: List[Card],
        source_pile_id: str,
        source_card_index: int,
        grab_offset_x: int,
        grab_offset_y: int,
        origin_x: int,
        origin_y: int,
    ) -> None:
        self.cards: List[Card] = cards
        self.source_pile_id: str = source_pile_id
        self.source_card_index: int = source_card_index
        self.grab_offset_x: int = grab_offset_x
        self.grab_offset_y: int = grab_offset_y
        self.origin_x: int = origin_x
        self.origin_y: int = origin_y
        self.current_x: int = origin_x
        self.current_y: int = origin_y


class InteractionController:
    """Coordinates player gestures, dragging physics, and smart click routing."""

    def __init__(self) -> None:
        self.drag_ctx: Optional[DragContext] = None
        self.mouse_down_pos: Optional[Tuple[int, int]] = None
        self.mouse_down_time: float = 0.0
        self.hovered_pile_id: Optional[str] = None
        self.hovered_card_idx: int = -1
        self.active_hint_move: Optional[Move] = None
        self.hint_timestamp: float = 0.0

    def set_hint(self, move: Optional[Move]) -> None:
        """Sets an active visual hint highlight."""
        self.active_hint_move = move
        self.hint_timestamp = time.time()

    def clear_hint(self) -> None:
        self.active_hint_move = None

    def handle_mouse_down(self, pos: Tuple[int, int], game: BaseGame, layout: LayoutManager) -> Optional[MoveResult]:
        """Initiates potential drag or click interaction."""
        self.mouse_down_pos = pos
        self.mouse_down_time = time.time()
        self.clear_hint()

        pile_id, card_idx, card = layout.hit_test(pos[0], pos[1], game)
        if not pile_id:
            return None

        pile = game.get_pile(pile_id)
        if not pile:
            return None

        # Stock pile click (deal or recycle)
        if pile_id == "stock":
            return self._handle_stock_action(game)

        # Non-empty pile with face-up card(s)
        if card and card.face_up and card_idx >= 0:
            # Determine cards to drag: clicked card and all cards above it in the column
            cards_to_drag: List[Card] = []
            if pile_id.startswith("tableau") or pile_id.startswith("cascade"):
                cards_to_drag = list(pile.cards[card_idx:])
            else:
                cards_to_drag = [card]

            card_rect = layout.card_rects.get((pile_id, card_idx))
            origin_x = card_rect.x if card_rect else pos[0]
            origin_y = card_rect.y if card_rect else pos[1]

            self.drag_ctx = DragContext(
                cards=cards_to_drag,
                source_pile_id=pile_id,
                source_card_index=card_idx,
                grab_offset_x=pos[0] - origin_x,
                grab_offset_y=pos[1] - origin_y,
                origin_x=origin_x,
                origin_y=origin_y,
            )
            self.drag_ctx.current_x = origin_x
            self.drag_ctx.current_y = origin_y

        return None

    def handle_mouse_motion(self, pos: Tuple[int, int], game: BaseGame, layout: LayoutManager) -> None:
        """Updates drag position and hover targets."""
        if self.drag_ctx is not None:
            self.drag_ctx.current_x = pos[0] - self.drag_ctx.grab_offset_x
            self.drag_ctx.current_y = pos[1] - self.drag_ctx.grab_offset_y

        pile_id, card_idx, _ = layout.hit_test(pos[0], pos[1], game)
        self.hovered_pile_id = pile_id
        self.hovered_card_idx = card_idx

    def handle_mouse_up(self, pos: Tuple[int, int], game: BaseGame, layout: LayoutManager) -> Optional[MoveResult]:
        """Resolves drop target or smart click execution."""
        if self.mouse_down_pos is None:
            return None

        dx = pos[0] - self.mouse_down_pos[0]
        dy = pos[1] - self.mouse_down_pos[1]
        dist_sq = dx * dx + dy * dy
        is_click = dist_sq < 36  # Less than 6px movement is considered a click

        result: Optional[MoveResult] = None

        if self.drag_ctx is not None:
            ctx = self.drag_ctx
            self.drag_ctx = None

            if not is_click:
                # Drag & Drop resolution
                drop_rect = pygame.Rect(ctx.current_x, ctx.current_y, layout.card_width, layout.card_height)
                target_pile = layout.find_drop_target(drop_rect, game, ctx.source_pile_id)
                if target_pile:
                    # Construct and attempt move
                    lead_card = ctx.cards[0]
                    card_cnt = len(ctx.cards)
                    move = Move(
                        source_pile_id=ctx.source_pile_id,
                        dest_pile_id=target_pile,
                        card_id=getattr(lead_card, "id", None),
                        card_count=card_cnt,
                    )
                    result = game.make_move(move)
            else:
                # Click-to-move auto-routing
                result = self._handle_smart_click(ctx.source_pile_id, ctx.source_card_index, ctx.cards[0], game)

        self.mouse_down_pos = None
        return result

    def _handle_stock_action(self, game: BaseGame) -> Optional[MoveResult]:
        """Executes stock dealing or recycling."""
        # Find legal stock moves
        for move in game.get_legal_moves():
            if str(move.move_type) == "deal_stock" or move.source_pile_id == "stock":
                return game.make_move(move)

        # Direct deal fallback
        if hasattr(game, "deal_stock"):
            res = game.deal_stock()
            if isinstance(res, MoveResult):
                return res
            return MoveResult.ok()

        return None

    def _handle_smart_click(self, source_pile: str, card_idx: int, card: Card, game: BaseGame) -> Optional[MoveResult]:
        """Automatically routes a clicked card to the most appropriate legal destination."""
        legal_moves = game.get_legal_moves()
        matching_moves = [
            m for m in legal_moves
            if m.source_pile_id == source_pile and (m.card_id is None or m.card_id == getattr(card, "id", None))
        ]

        if not matching_moves:
            return None

        # Prioritize destination: Foundations first, Tableaus second, Free Cells last
        def move_priority(m: Move) -> int:
            dst = m.dest_pile_id
            if dst.startswith("foundation"):
                return 100
            elif dst.startswith("tableau") or dst.startswith("cascade"):
                return 50
            elif dst.startswith("freecell") or dst.startswith("cell"):
                return 10
            return 1

        matching_moves.sort(key=move_priority, reverse=True)
        return game.make_move(matching_moves[0])

    # -------------------------------------------------------------------------
    # Visual Highlights & Drag Rendering
    # -------------------------------------------------------------------------
    def draw_drag(self, surface: pygame.Surface, renderer: CardRenderer, layout: LayoutManager) -> None:
        """Draws cards currently being dragged with elevated drop shadow."""
        if self.drag_ctx is None:
            return

        ctx = self.drag_ctx
        cur_x = ctx.current_x
        cur_y = ctx.current_y

        dy = layout.tableau_dy_up.get(ctx.source_pile_id, max(18, int(layout.card_height * 0.26)))
        total_drag_h = (len(ctx.cards) - 1) * dy + layout.card_height

        # Large elevated soft shadow under the entire dragged stack
        shadow_rect = pygame.Rect(cur_x + 8, cur_y + 12, layout.card_width + 4, total_drag_h + 4)
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 70), (0, 0, shadow_rect.width, shadow_rect.height), border_radius=10)
        surface.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))

        # Render each card in the dragged stack
        for i, card in enumerate(ctx.cards):
            card_y = cur_y + i * dy
            card_surf = renderer.get_card_surface(card, layout.card_width, layout.card_height)
            surface.blit(card_surf, (cur_x, card_y))

    def draw_highlights(self, surface: pygame.Surface, layout: LayoutManager, game: BaseGame) -> None:
        """Draws hint pulses and hover outlines on relevant piles."""
        now = time.time()

        # Hint highlight
        if self.active_hint_move is not None:
            # Pulse intensity using sine wave
            alpha = int(140 + 100 * math.sin((now - self.hint_timestamp) * 6))
            src_pile = self.active_hint_move.source_pile_id
            dst_pile = self.active_hint_move.dest_pile_id

            # Source highlight (Golden glow)
            src_rect = layout.pile_rects.get(src_pile)
            src_pile_obj = game.get_pile(src_pile)
            if src_pile_obj and src_pile_obj.cards and (src_pile.startswith("tableau") or src_pile.startswith("cascade")):
                # Highlight top card or specified card
                target_idx = len(src_pile_obj.cards) - self.active_hint_move.card_count
                card_r = layout.card_rects.get((src_pile, max(0, target_idx)))
                if card_r:
                    src_rect = card_r

            if src_rect:
                glow_surf = pygame.Surface((src_rect.width + 8, src_rect.height + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 215, 0, alpha), (0, 0, src_rect.width + 8, src_rect.height + 8), width=3, border_radius=8)
                surface.blit(glow_surf, (src_rect.x - 4, src_rect.y - 4))

            # Destination highlight (Cyan glow)
            dst_rect = layout.pile_rects.get(dst_pile)
            dst_pile_obj = game.get_pile(dst_pile)
            if dst_pile_obj and dst_pile_obj.cards and (dst_pile.startswith("tableau") or dst_pile.startswith("cascade")):
                last_idx = len(dst_pile_obj.cards) - 1
                card_r = layout.card_rects.get((dst_pile, last_idx))
                if card_r:
                    dst_rect = card_r

            if dst_rect:
                glow_surf = pygame.Surface((dst_rect.width + 8, dst_rect.height + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (0, 230, 255, alpha), (0, 0, dst_rect.width + 8, dst_rect.height + 8), width=3, border_radius=8)
                surface.blit(glow_surf, (dst_rect.x - 4, dst_rect.y - 4))
