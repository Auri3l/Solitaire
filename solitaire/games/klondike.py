"""Klondike Solitaire Rules Engine.

Implements classic Klondike Solitaire in Turn 1 and Turn 3 dealing modes,
with reversible command deltas, full move validation, multi-step undo/redo,
scoring systems (Standard & Vegas), hint generation, and auto-complete solver.
"""

from __future__ import annotations
from enum import Enum, unique
from typing import List, Optional, Tuple, Dict, Any

from solitaire.core.card import Card, Suit, Rank, Color
from solitaire.core.pile import Pile, PileType, Deck
from solitaire.core.commands import (
    Command,
    CardMoveCommand,
    StockDealCommand,
    RecycleCommand,
    CommandHistory,
)
from solitaire.core.base_game import BaseGame, GameStatus, Move, MoveResult


@unique
class MoveType(Enum):
    """Categorizes Klondike move types."""
    DEAL_STOCK = "deal_stock"
    RECYCLE_STOCK = "recycle_stock"
    WASTE_TO_TABLEAU = "waste_to_tableau"
    WASTE_TO_FOUNDATION = "waste_to_foundation"
    TABLEAU_TO_TABLEAU = "tableau_to_tableau"
    TABLEAU_TO_FOUNDATION = "tableau_to_foundation"
    FOUNDATION_TO_TABLEAU = "foundation_to_tableau"

    def __str__(self) -> str:
        return self.value


@unique
class ScoringMode(Enum):
    """Scoring mode: Standard Microsoft rules or Vegas casino wagering."""
    STANDARD = "standard"
    VEGAS = "vegas"

    def __str__(self) -> str:
        return self.value


class KlondikeGame(BaseGame):
    """Full implementation of Klondike Solitaire game rules."""

    def __init__(
        self,
        turn_mode: int = 1,
        scoring_mode: ScoringMode = ScoringMode.STANDARD,
        max_recycles: Optional[int] = None,
        seed: Optional[int] = None
    ) -> None:
        super().__init__(mode_name="klondike")
        if turn_mode not in (1, 3):
            raise ValueError(f"turn_mode must be 1 or 3, got {turn_mode}")
        self.turn_mode: int = turn_mode
        self.scoring_mode: ScoringMode = scoring_mode
        self.max_recycles: Optional[int] = max_recycles
        self.seed: Optional[int] = seed

        self.stock: Pile = Pile("stock", PileType.STOCK)
        self.waste: Pile = Pile("waste", PileType.WASTE)
        self.foundations: List[Pile] = [
            Pile(f"foundation_{i}", PileType.FOUNDATION, index=i) for i in range(4)
        ]
        self.tableau: List[Pile] = [
            Pile(f"tableau_{i}", PileType.TABLEAU, index=i) for i in range(7)
        ]

        self.piles: Dict[str, Pile] = {
            "stock": self.stock,
            "waste": self.waste,
            "foundation_0": self.foundations[0],
            "foundation_1": self.foundations[1],
            "foundation_2": self.foundations[2],
            "foundation_3": self.foundations[3],
            "tableau_0": self.tableau[0],
            "tableau_1": self.tableau[1],
            "tableau_2": self.tableau[2],
            "tableau_3": self.tableau[3],
            "tableau_4": self.tableau[4],
            "tableau_5": self.tableau[5],
            "tableau_6": self.tableau[6],
        }

        self.initial_cards_order: List[Card] = []
        self.start_new_game(seed=seed)

    # -------------------------------------------------------------------------
    # Game Initialization & Deal
    # -------------------------------------------------------------------------
    def start_new_game(self, seed: Optional[int] = None) -> None:
        """Deals a fresh standard 52-card game with optional seed."""
        if seed is not None:
            self.seed = seed

        deck = Deck.create_standard_52()
        deck.shuffle(self.seed)
        self.initial_cards_order = [c.clone() for c in deck.cards]
        self._deal_cards(deck.cards)

    def restart(self) -> None:
        """Restarts game with exact same initial deck permutation."""
        cards = [c.clone() for c in self.initial_cards_order]
        self._deal_cards(cards)

    def _deal_cards(self, cards: List[Card]) -> None:
        """Distributes cards according to standard Klondike layout."""
        # Reset all piles
        self.stock.clear()
        self.waste.clear()
        for f in self.foundations:
            f.clear()
        for t in self.tableau:
            t.clear()

        # Reset counters
        self.history.clear()
        self.moves_count = 0
        self.recycles_count = 0
        self.passes_through_stock = 1
        self.score = -52 if self.scoring_mode == ScoringMode.VEGAS else 0
        self.game_status = GameStatus.IN_PROGRESS

        # Deal 28 cards to 7 tableau columns
        # Cascade i receives i + 1 cards: bottom i face-down, top card face-up
        card_idx = 0
        for col_idx in range(7):
            count = col_idx + 1
            for k in range(count):
                card = cards[card_idx]
                card_idx += 1
                card.is_face_up = (k == col_idx)
                self.tableau[col_idx].push(card)

        # Remaining 24 cards to stock face-down
        while card_idx < len(cards):
            card = cards[card_idx]
            card_idx += 1
            card.is_face_up = False
            self.stock.push(card)

    def get_pile_by_id(self, pile_id: str) -> Pile:
        """Returns pile by string ID."""
        if pile_id in self.piles:
            return self.piles[pile_id]
        raise ValueError(f"Unknown pile ID: {pile_id}")

    # -------------------------------------------------------------------------
    # Stock Operations: Deal and Recycle
    # -------------------------------------------------------------------------
    def deal_stock(self) -> MoveResult:
        """High-level action: deals from stock, or recycles waste if stock empty."""
        if not self.stock.is_empty:
            move = Move(MoveType.DEAL_STOCK, "stock", "waste")
            return self.make_move(move)
        elif not self.waste.is_empty:
            move = Move(MoveType.RECYCLE_STOCK, "waste", "stock")
            return self.make_move(move)
        else:
            return MoveResult.fail("Both stock and waste are empty")

    # -------------------------------------------------------------------------
    # Move Execution Pipeline
    # -------------------------------------------------------------------------
    def is_legal_move(self, move: Move) -> bool:
        """Checks whether move is legal without executing it."""
        if move is None:
            return False
        if move.source_pile_id not in self.piles or move.dest_pile_id not in self.piles:
            return False
        res, _, _ = self._validate_move(move)
        return res

    def make_move(self, move: Move) -> MoveResult:
        """Validates and executes a player move, pushing to history on success."""
        if move is None:
            return MoveResult.fail("Move cannot be None")
        if move.source_pile_id not in self.piles:
            return MoveResult.fail(f"Unknown pile ID: {move.source_pile_id}")
        if move.dest_pile_id not in self.piles:
            return MoveResult.fail(f"Unknown pile ID: {move.dest_pile_id}")
        if self.is_won():
            return MoveResult.fail("Game is already won")

        is_valid, error_msg, cmd = self._validate_move(move)
        if not is_valid or cmd is None:
            return MoveResult.fail(error_msg)

        # Execute command through BaseGame wrapper
        if self.execute_command(cmd):
            if self._check_win_condition():
                self.game_status = GameStatus.WON
            return MoveResult.ok(cmd)
        return MoveResult.fail("Failed to execute move command")

    def undo(self) -> bool:
        """Rolls back the most recent move."""
        res = super().undo()
        if res:
            self.game_status = GameStatus.IN_PROGRESS
        return res

    def redo(self) -> bool:
        """Re-applies the most recently undone move."""
        res = super().redo()
        if res and self._check_win_condition():
            self.game_status = GameStatus.WON
        return res

    # -------------------------------------------------------------------------
    # Internal Move Validation & Command Generation
    # -------------------------------------------------------------------------
    def _infer_move_type(self, move: Move) -> MoveType:
        if move is None:
            return MoveType.TABLEAU_TO_TABLEAU
        if move.move_type is not None:
            if isinstance(move.move_type, MoveType):
                return move.move_type
            if isinstance(move.move_type, str):
                try:
                    return MoveType(move.move_type)
                except ValueError:
                    pass

        src = move.source_pile_id
        dst = move.dest_pile_id

        if src == "stock":
            if self.stock.is_empty and not self.waste.is_empty:
                return MoveType.RECYCLE_STOCK
            return MoveType.DEAL_STOCK
        if src == "waste":
            if dst.startswith("foundation"):
                return MoveType.WASTE_TO_FOUNDATION
            if dst.startswith("tableau"):
                return MoveType.WASTE_TO_TABLEAU
            if dst == "stock":
                return MoveType.RECYCLE_STOCK
        if src.startswith("tableau"):
            if dst.startswith("foundation"):
                return MoveType.TABLEAU_TO_FOUNDATION
            if dst.startswith("tableau"):
                return MoveType.TABLEAU_TO_TABLEAU
        if src.startswith("foundation"):
            if dst.startswith("tableau"):
                return MoveType.FOUNDATION_TO_TABLEAU

        return MoveType.TABLEAU_TO_TABLEAU

    def _validate_move(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        if move is None:
            return False, "Move cannot be None", None
        if move.source_pile_id not in self.piles:
            return False, f"Unknown pile ID: {move.source_pile_id}", None
        if move.dest_pile_id not in self.piles:
            return False, f"Unknown pile ID: {move.dest_pile_id}", None

        mtype = self._infer_move_type(move)

        if mtype == MoveType.DEAL_STOCK:
            return self._validate_deal_stock(move)
        elif mtype == MoveType.RECYCLE_STOCK:
            return self._validate_recycle_stock(move)
        elif mtype == MoveType.WASTE_TO_FOUNDATION:
            return self._validate_waste_to_foundation(move)
        elif mtype == MoveType.WASTE_TO_TABLEAU:
            return self._validate_waste_to_tableau(move)
        elif mtype == MoveType.TABLEAU_TO_FOUNDATION:
            return self._validate_tableau_to_foundation(move)
        elif mtype == MoveType.TABLEAU_TO_TABLEAU:
            return self._validate_tableau_to_tableau(move)
        elif mtype == MoveType.FOUNDATION_TO_TABLEAU:
            return self._validate_foundation_to_tableau(move)

        return False, f"Unsupported move type: {mtype}", None

    def _validate_deal_stock(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        if self.stock.is_empty:
            if not self.waste.is_empty:
                return self._validate_recycle_stock(move)
            return False, "Stock is empty. Click stock to recycle waste.", None

        k = 1 if self.turn_mode == 1 else min(3, len(self.stock))
        cmd = StockDealCommand(count=k)
        return True, "", cmd

    def _validate_recycle_stock(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        if not self.stock.is_empty:
            return False, "Cannot recycle while cards remain in stock", None
        if self.waste.is_empty:
            return False, "Both stock and waste are empty", None
        if self.max_recycles is not None and self.recycles_count >= self.max_recycles:
            return False, f"Maximum stock recycles ({self.max_recycles}) reached", None

        # Penalty calculation in standard scoring
        penalty = 0
        if self.scoring_mode == ScoringMode.STANDARD:
            if self.turn_mode == 1:
                penalty = -100
            elif self.turn_mode == 3 and self.passes_through_stock >= 3:
                penalty = -20

        waste_cards = [c.card_id for c in self.waste.cards]
        cmd = RecycleCommand(
            card_ids=waste_cards,
            previous_recycles_count=self.recycles_count,
            previous_passes_through_stock=self.passes_through_stock,
            nominal_score_delta=penalty
        )
        return True, "", cmd

    def _validate_waste_to_foundation(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        if self.waste.is_empty:
            return False, "Waste pile is empty", None
        if move.card_count > 1:
            return False, "Foundations only accept one card at a time", None
        card = self.waste.peek()
        if move.card_id is not None and move.card_id != card.card_id:
            return False, f"Card ID {move.card_id} does not match top card {card.card_id}", None
        f_pile = self.get_pile_by_id(move.dest_pile_id)
        if not self._is_legal_foundation_placement(card, f_pile):
            return False, "Illegal card placement on foundation", None

        score_delta = 5 if self.scoring_mode == ScoringMode.VEGAS else 10
        cmd = CardMoveCommand(
            source_pile_id="waste",
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            nominal_score_delta=score_delta
        )
        return True, "", cmd

    def _validate_waste_to_tableau(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        if self.waste.is_empty:
            return False, "Waste pile is empty", None
        card = self.waste.peek()
        if move.card_id is not None and move.card_id != card.card_id:
            return False, f"Card ID {move.card_id} does not match top card {card.card_id}", None
        t_pile = self.get_pile_by_id(move.dest_pile_id)
        is_legal, reason = self._check_tableau_placement(card, t_pile)
        if not is_legal:
            return False, reason, None

        score_delta = 0 if self.scoring_mode == ScoringMode.VEGAS else 5
        cmd = CardMoveCommand(
            source_pile_id="waste",
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            nominal_score_delta=score_delta
        )
        return True, "", cmd

    def _validate_tableau_to_foundation(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        if move.card_count > 1:
            return False, "Foundations only accept one card at a time", None

        src_pile = self.get_pile_by_id(move.source_pile_id)
        if src_pile.is_empty:
            return False, "Tableau column is empty", None

        card = src_pile.peek()
        if not card.is_face_up:
            return False, "Cannot move face-down cards", None
        if move.card_id is not None and move.card_id != card.card_id:
            return False, f"Card ID {move.card_id} does not match top card {card.card_id}", None
        f_pile = self.get_pile_by_id(move.dest_pile_id)
        if not self._is_legal_foundation_placement(card, f_pile):
            return False, "Illegal card placement on foundation", None

        # Check auto-flip side-effect on exposed card underneath
        uncovered_id = None
        flip_score = 0
        if len(src_pile) > 1 and not src_pile.cards[-2].is_face_up:
            uncovered_id = src_pile.cards[-2].card_id
            if self.scoring_mode == ScoringMode.STANDARD:
                flip_score = 5

        base_score = 5 if self.scoring_mode == ScoringMode.VEGAS else 10
        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            uncovered_card_id=uncovered_id,
            nominal_score_delta=base_score + flip_score
        )
        return True, "", cmd

    def _validate_tableau_to_tableau(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        if move.source_pile_id == move.dest_pile_id:
            return False, "Source and destination columns must be different", None
        src_pile = self.get_pile_by_id(move.source_pile_id)
        dst_pile = self.get_pile_by_id(move.dest_pile_id)
        if src_pile.is_empty:
            return False, "Source tableau column is empty", None

        k = move.card_count
        if move.card_id is not None:
            c_idx = src_pile.find_card_index(move.card_id)
            if c_idx is None:
                return False, f"Card ID {move.card_id} not found in source pile {move.source_pile_id}", None
            k = len(src_pile) - c_idx

        if k < 1 or k > len(src_pile):
            return False, "Invalid card count", None

        start_idx = len(src_pile) - k
        moving_cards = src_pile.cards[start_idx:]
        if any(not c.is_face_up for c in moving_cards):
            return False, "Cannot move face-down cards", None

        # Verify internal sequence descending rank and alternating color
        for idx in range(len(moving_cards) - 1):
            c_curr = moving_cards[idx]
            c_next = moving_cards[idx + 1]
            if c_curr.rank.value != c_next.rank.value + 1 or c_curr.color == c_next.color:
                return False, "Moving sequence is not valid alternating descending stack", None

        base_card = moving_cards[0]
        is_legal, reason = self._check_tableau_placement(base_card, dst_pile)
        if not is_legal:
            return False, reason, None

        # Check auto-flip side-effect on exposed card
        uncovered_id = None
        flip_score = 0
        rem_count = len(src_pile) - k
        if rem_count > 0 and not src_pile.cards[rem_count - 1].is_face_up:
            uncovered_id = src_pile.cards[rem_count - 1].card_id
            if self.scoring_mode == ScoringMode.STANDARD:
                flip_score = 5

        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[c.card_id for c in moving_cards],
            uncovered_card_id=uncovered_id,
            nominal_score_delta=flip_score
        )
        return True, "", cmd

    def _validate_foundation_to_tableau(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        f_pile = self.get_pile_by_id(move.source_pile_id)
        if f_pile.is_empty:
            return False, "Foundation pile is empty", None
        card = f_pile.peek()
        if move.card_id is not None and move.card_id != card.card_id:
            return False, f"Card ID {move.card_id} does not match top card {card.card_id}", None
        t_pile = self.get_pile_by_id(move.dest_pile_id)
        is_legal, reason = self._check_tableau_placement(card, t_pile)
        if not is_legal:
            return False, reason, None

        penalty = -5 if self.scoring_mode == ScoringMode.VEGAS else -15
        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            nominal_score_delta=penalty
        )
        return True, "", cmd

    # -------------------------------------------------------------------------
    # Card Rules Predicates
    # -------------------------------------------------------------------------
    def _is_legal_foundation_placement(self, card: Card, f_pile: Pile) -> bool:
        if f_pile.is_empty:
            return card.rank == Rank.ACE
        top = f_pile.peek()
        return card.suit == top.suit and card.rank.value == top.rank.value + 1

    def _check_tableau_placement(self, card: Card, t_pile: Pile) -> Tuple[bool, str]:
        if t_pile.is_empty:
            if card.rank == Rank.KING:
                return True, ""
            return False, "Only Kings can be placed on an empty column"

        top = t_pile.peek()
        if not top.is_face_up:
            return False, "Cannot place cards on face-down card"
        if card.color == top.color:
            return False, "Tableau cards must alternate with alternating colors (Red on Black, Black on Red)"
        if top.rank.value != card.rank.value + 1:
            return False, "Tableau cards must be placed in strictly descending rank order"

        return True, ""

    def _is_legal_tableau_placement(self, card: Card, t_pile: Pile) -> bool:
        res, _ = self._check_tableau_placement(card, t_pile)
        return res

    # -------------------------------------------------------------------------
    # Win Condition & Auto-Finish
    # -------------------------------------------------------------------------
    def _check_win_condition(self) -> bool:
        return sum(len(f) for f in self.foundations) == 52

    def is_won(self) -> bool:
        return self.game_status == GameStatus.WON or self._check_win_condition()

    def can_auto_finish(self) -> bool:
        """Solvability Invariant:
        Stock is empty, Waste is empty, and all tableau cards are face-up.
        """
        if not self.stock.is_empty or not self.waste.is_empty:
            return False
        for col in self.tableau:
            if any(not c.is_face_up for c in col.cards):
                return False
        return not self.is_won()

    def can_auto_complete(self) -> bool:
        """Alias for can_auto_finish()."""
        return self.can_auto_finish()

    def auto_finish_step(self) -> Optional[MoveResult]:
        """Finds and executes the next single card promotion to foundation."""
        if not self.can_auto_finish():
            return None

        # Look for tableau top card that can move to matching foundation
        for col_idx, col in enumerate(self.tableau):
            if col.is_empty:
                continue
            top_card = col.peek()
            for f_idx, f_pile in enumerate(self.foundations):
                if self._is_legal_foundation_placement(top_card, f_pile):
                    move = Move(
                        MoveType.TABLEAU_TO_FOUNDATION,
                        f"tableau_{col_idx}",
                        f"foundation_{f_idx}",
                        card_count=1,
                        card_id=top_card.card_id
                    )
                    return self.make_move(move)
        return None

    def auto_complete_step(self) -> Optional[MoveResult]:
        """Alias for auto_finish_step()."""
        return self.auto_finish_step()

    def auto_finish_all(self) -> int:
        """Executes auto-finish loop until win or deadlock. Returns step count."""
        steps = 0
        while not self.is_won() and self.can_auto_finish():
            res = self.auto_finish_step()
            if res is None or not res.success:
                break
            steps += 1
        return steps

    def auto_complete_all(self) -> int:
        """Alias for auto_finish_all()."""
        return self.auto_finish_all()

    # -------------------------------------------------------------------------
    # Legal Move Generation & Hint Engine
    # -------------------------------------------------------------------------
    def get_legal_moves(self) -> List[Move]:
        moves: List[Move] = []
        if self.is_won():
            return moves

        # Stock deals / recycles
        if not self.stock.is_empty:
            moves.append(Move(MoveType.DEAL_STOCK, "stock", "waste"))
        elif not self.waste.is_empty:
            if self.max_recycles is None or self.recycles_count < self.max_recycles:
                moves.append(Move(MoveType.RECYCLE_STOCK, "waste", "stock"))

        # Waste moves
        if not self.waste.is_empty:
            c = self.waste.peek()
            for f_idx, f in enumerate(self.foundations):
                if self._is_legal_foundation_placement(c, f):
                    moves.append(Move(MoveType.WASTE_TO_FOUNDATION, "waste", f"foundation_{f_idx}", card_id=c.card_id))
            for t_idx, t in enumerate(self.tableau):
                if self._is_legal_tableau_placement(c, t):
                    moves.append(Move(MoveType.WASTE_TO_TABLEAU, "waste", f"tableau_{t_idx}", card_id=c.card_id))

        # Tableau moves
        for t_src_idx, t_src in enumerate(self.tableau):
            if t_src.is_empty:
                continue
            # Top card to foundation
            top_c = t_src.peek()
            for f_idx, f in enumerate(self.foundations):
                if self._is_legal_foundation_placement(top_c, f):
                    moves.append(Move(MoveType.TABLEAU_TO_FOUNDATION, f"tableau_{t_src_idx}", f"foundation_{f_idx}", card_id=top_c.card_id))

            # Sequence to other tableau columns
            face_up_indices = [idx for idx, c in enumerate(t_src.cards) if c.is_face_up]
            for start_idx in face_up_indices:
                k = len(t_src) - start_idx
                sub_cards = t_src.cards[start_idx:]
                base_c = sub_cards[0]
                for t_dst_idx, t_dst in enumerate(self.tableau):
                    if t_dst_idx == t_src_idx:
                        continue
                    if self._is_legal_tableau_placement(base_c, t_dst):
                        moves.append(Move(MoveType.TABLEAU_TO_TABLEAU, f"tableau_{t_src_idx}", f"tableau_{t_dst_idx}", card_count=k, card_id=base_c.card_id))

        # Foundation to Tableau moves
        for f_idx, f in enumerate(self.foundations):
            if f.is_empty:
                continue
            c = f.peek()
            for t_idx, t in enumerate(self.tableau):
                if self._is_legal_tableau_placement(c, t):
                    moves.append(Move(MoveType.FOUNDATION_TO_TABLEAU, f"foundation_{f_idx}", f"tableau_{t_idx}", card_id=c.card_id))

        return moves

    def get_hint(self) -> Optional[Move]:
        legal_moves = self.get_legal_moves()
        if not legal_moves:
            return None

        # Priority 1: Safe Foundation (Ace, 2, or opposite-color r-1 home)
        for m in legal_moves:
            if m.move_type in (MoveType.WASTE_TO_FOUNDATION, MoveType.TABLEAU_TO_FOUNDATION):
                src = self.get_pile_by_id(m.source_pile_id)
                card = src.peek()
                if card and (card.rank.value <= 2 or self._is_safe_foundation(card)):
                    return m

        # Priority 2: Tableau move uncovering face-down card
        for m in legal_moves:
            if m.move_type in (MoveType.TABLEAU_TO_TABLEAU, MoveType.TABLEAU_TO_FOUNDATION):
                src = self.get_pile_by_id(m.source_pile_id)
                rem = len(src) - m.card_count
                if rem > 0 and not src.cards[rem - 1].is_face_up:
                    return m

        # Priority 3: King to empty cascade if exposing a card
        for m in legal_moves:
            if m.move_type == MoveType.TABLEAU_TO_TABLEAU:
                dst = self.get_pile_by_id(m.dest_pile_id)
                if dst.is_empty:
                    return m

        # Priority 4: Waste to Tableau
        for m in legal_moves:
            if m.move_type == MoveType.WASTE_TO_TABLEAU:
                return m

        # Priority 5: Tableau to Tableau consolidation
        for m in legal_moves:
            if m.move_type == MoveType.TABLEAU_TO_TABLEAU:
                return m

        # Priority 6: Stock Deal
        for m in legal_moves:
            if m.move_type == MoveType.DEAL_STOCK:
                return m

        return legal_moves[0]

    def _is_safe_foundation(self, card: Card) -> bool:
        """Card is safe if both foundations of opposite color are at least rank - 1."""
        target_rank = card.rank.value - 1
        opp_color = Color.RED if card.color == Color.BLACK else Color.BLACK
        opp_foundations = [
            f for f in self.foundations
            if not f.is_empty and f.peek().color == opp_color
        ]
        if len(opp_foundations) < 2:
            return False
        return all(f.peek().rank.value >= target_rank for f in opp_foundations)

    def find_best_move_for_card(self, pile_id: str, card_index: int = -1) -> Optional[Move]:
        """Smart click auto-routing: finds best legal destination for card."""
        if pile_id not in self.piles:
            return None
        src_pile = self.piles[pile_id]
        if src_pile.is_empty:
            return None

        actual_idx = card_index if card_index >= 0 else len(src_pile) + card_index
        if actual_idx < 0 or actual_idx >= len(src_pile):
            return None

        card = src_pile[actual_idx]
        if not card.is_face_up:
            return None

        # 1. Try foundation if single card
        if actual_idx == len(src_pile) - 1:
            for f_idx, f_pile in enumerate(self.foundations):
                if self._is_legal_foundation_placement(card, f_pile):
                    mtype = MoveType.WASTE_TO_FOUNDATION if pile_id == "waste" else MoveType.TABLEAU_TO_FOUNDATION
                    return Move(mtype, pile_id, f"foundation_{f_idx}", card_count=1, card_id=card.card_id)

        # 2. Try non-empty tableau columns
        count = len(src_pile) - actual_idx
        for t_idx, t_pile in enumerate(self.tableau):
            if f"tableau_{t_idx}" == pile_id:
                continue
            if not t_pile.is_empty and self._is_legal_tableau_placement(card, t_pile):
                mtype = MoveType.WASTE_TO_TABLEAU if pile_id == "waste" else MoveType.TABLEAU_TO_TABLEAU
                return Move(mtype, pile_id, f"tableau_{t_idx}", card_count=count, card_id=card.card_id)

        # 3. Try empty tableau columns (only if King)
        if card.rank == Rank.KING:
            for t_idx, t_pile in enumerate(self.tableau):
                if f"tableau_{t_idx}" == pile_id:
                    continue
                if t_pile.is_empty:
                    mtype = MoveType.WASTE_TO_TABLEAU if pile_id == "waste" else MoveType.TABLEAU_TO_TABLEAU
                    return Move(mtype, pile_id, f"tableau_{t_idx}", card_count=count, card_id=card.card_id)

        return None
