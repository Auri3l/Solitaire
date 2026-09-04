"""FreeCell Solitaire Rules Engine.

Implements classic FreeCell Solitaire with exact inductive Supermove formulas,
4 open free cells, 8 cascades, 4 foundation piles, 7-tier hint heuristics,
safe foundation auto-play predicates, and full reversible command integration.
"""

from __future__ import annotations
from enum import Enum, unique
from typing import List, Optional, Tuple, Dict, Any, Union

from solitaire.core.card import Card, Suit, Rank, Color
from solitaire.core.pile import Pile, PileType, Deck
from solitaire.core.commands import (
    Command,
    CardMoveCommand,
    CommandHistory,
)
from solitaire.core.base_game import BaseGame, GameStatus, Move, MoveResult


@unique
class FreeCellMoveType(Enum):
    """Categorizes FreeCell move types."""
    CASCADE_TO_FREECELL = "cascade_to_freecell"
    FREECELL_TO_CASCADE = "freecell_to_cascade"
    CASCADE_TO_FOUNDATION = "cascade_to_foundation"
    FREECELL_TO_FOUNDATION = "freecell_to_foundation"
    CASCADE_TO_CASCADE = "cascade_to_cascade"
    FREECELL_TO_FREECELL = "freecell_to_freecell"
    FOUNDATION_TO_CASCADE = "foundation_to_cascade"
    FOUNDATION_TO_FREECELL = "foundation_to_freecell"

    def __str__(self) -> str:
        return self.value


# Canonical alias for MoveType
MoveType = FreeCellMoveType


class FreeCellGame(BaseGame):
    """Full implementation of FreeCell Solitaire game rules."""

    def __init__(
        self,
        seed: Optional[int] = None,
        allow_foundation_demotion: bool = False,
        ms_game_number: Optional[int] = None,
    ) -> None:
        self._game_status: GameStatus = GameStatus.IN_PROGRESS
        super().__init__(mode_name="freecell")
        self.seed: Optional[int] = seed
        self.allow_foundation_demotion: bool = allow_foundation_demotion
        self.ms_game_number: Optional[int] = ms_game_number

        # Core Piles
        self.cascades: List[Pile] = [
            Pile(f"cascade_{i}", PileType.TABLEAU, index=i) for i in range(8)
        ]
        self.free_cells: List[Pile] = [
            Pile(f"freecell_{i}", PileType.FREECELL, index=i) for i in range(4)
        ]
        self.foundations: List[Pile] = [
            Pile(f"foundation_{i}", PileType.FOUNDATION, index=i) for i in range(4)
        ]

        # Alias properties for interoperability
        self.tableau = self.cascades
        self.cells = self.free_cells

        # Populate lookup dictionary with primary keys and canonical aliases
        self.piles: Dict[str, Pile] = {}
        for i, c in enumerate(self.cascades):
            self.piles[f"cascade_{i}"] = c
            self.piles[f"tableau_{i}"] = c
        for i, fc in enumerate(self.free_cells):
            self.piles[f"freecell_{i}"] = fc
            self.piles[f"cell_{i}"] = fc
        for i, f in enumerate(self.foundations):
            self.piles[f"foundation_{i}"] = f

        self.initial_cards_order: List[Card] = []
        self.start_new_game(seed=seed, ms_game_number=ms_game_number)

    @property
    def game_status(self) -> GameStatus:
        if self._check_win_condition():
            return GameStatus.WON
        return self._game_status

    @game_status.setter
    def game_status(self, val: GameStatus) -> None:
        self._game_status = val

    # -------------------------------------------------------------------------
    # Game Initialization & Deal
    # -------------------------------------------------------------------------
    def start_new_game(
        self,
        seed: Optional[int] = None,
        ms_game_number: Optional[int] = None,
    ) -> None:
        """Deals a fresh standard 52-card game face-up."""
        if seed is not None:
            self.seed = seed
        if ms_game_number is not None:
            self.ms_game_number = ms_game_number

        if self.ms_game_number is not None:
            cards = self.generate_ms_deck(self.ms_game_number)
        else:
            deck = Deck.create_standard_52()
            deck.shuffle(self.seed)
            cards = deck.cards

        # All FreeCell cards are face-up
        for c in cards:
            c.is_face_up = True

        self.initial_cards_order = [c.clone() for c in cards]
        self._deal_cards(cards)

    def restart(self) -> None:
        """Restarts game with exact same initial deck layout."""
        cards = [c.clone(is_face_up=True) for c in self.initial_cards_order]
        self._deal_cards(cards)

    def _deal_cards(self, cards: List[Card]) -> None:
        """Distributes cards round-robin across the 8 cascades."""
        for c in self.cascades:
            c.clear()
        for fc in self.free_cells:
            fc.clear()
        for f in self.foundations:
            f.clear()

        self.history.clear()
        self.moves_count = 0
        self.score = 0
        self.game_status = GameStatus.IN_PROGRESS

        # Round-robin deal: 52 cards into 8 cascades
        # Cols 0..3 receive 7 cards each; Cols 4..7 receive 6 cards each
        for i, card in enumerate(cards):
            col_idx = i % 8
            card.is_face_up = True
            self.cascades[col_idx].push(card)

    @staticmethod
    def generate_ms_deck(game_number: int) -> List[Card]:
        """Generates the card distribution for Microsoft FreeCell deal numbers."""
        state = game_number

        def ms_rand() -> int:
            nonlocal state
            state = (state * 214013 + 2531011) & 0x7FFFFFFF
            return (state >> 16) & 0x7FFF

        # Clubs, Diamonds, Hearts, Spades
        ms_suits = [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]
        cards = []
        card_id = 0
        for rank in Rank:
            for suit in ms_suits:
                cards.append(Card(suit=suit, rank=rank, is_face_up=True, card_id=card_id))
                card_id += 1

        deck_size = 52
        for i in range(deck_size):
            j = (deck_size - 1) - (ms_rand() % (deck_size - i))
            cards[i], cards[j] = cards[j], cards[i]

        return cards

    # -------------------------------------------------------------------------
    # Supermove Calculations (Theorems 1 & 2)
    # -------------------------------------------------------------------------
    def get_empty_freecell_count(self) -> int:
        """Returns the number of currently unoccupied free cells (N)."""
        return sum(1 for fc in self.free_cells if fc.is_empty)

    def get_empty_cascade_count(self) -> int:
        """Returns the number of currently empty cascade columns (K)."""
        return sum(1 for c in self.cascades if c.is_empty)

    def calculate_max_supermove(
        self,
        dest_is_empty: bool = False,
        empty_cells: Optional[int] = None,
        empty_cascades: Optional[int] = None,
    ) -> int:
        """Calculates the exact maximum moveable sequence length given N and K.

        Formulas:
            Target Non-Empty: M = (1 + N) * 2^K
            Target Empty:     M = (1 + N) * 2^(K - 1)  (if K >= 1, else 0)
        """
        N = empty_cells if empty_cells is not None else self.get_empty_freecell_count()
        K = empty_cascades if empty_cascades is not None else self.get_empty_cascade_count()
        if dest_is_empty:
            if K <= 0:
                return 0
            return (1 + N) * (2 ** (K - 1))
        else:
            return (1 + N) * (2 ** K)

    def calculate_max_supermove_cards(self, dest_pile_id: str) -> int:
        """Calculates the exact maximum moveable sequence length to dest_pile_id."""
        dst_pile = self.get_pile_by_id(dest_pile_id)
        if dst_pile is None or dst_pile.pile_type != PileType.TABLEAU:
            return 1

        return self.calculate_max_supermove(dest_is_empty=dst_pile.is_empty)

    # -------------------------------------------------------------------------
    # Move Execution & Validation Pipeline
    # -------------------------------------------------------------------------
    def is_legal_move(self, move: Move) -> bool:
        """Evaluates legality without modifying state."""
        if move is None:
            return False
        if move.source_pile_id not in self.piles or move.dest_pile_id not in self.piles:
            return False
        is_valid, _, _ = self._validate_move(move)
        return is_valid

    def make_move(self, move: Move) -> MoveResult:
        """Validates and executes a move command, pushing to history on success."""
        if move is None:
            return MoveResult.fail("Move cannot be None")
        if move.source_pile_id not in self.piles:
            return MoveResult.fail(f"Unknown source pile ID: {move.source_pile_id}")
        if move.dest_pile_id not in self.piles:
            return MoveResult.fail(f"Unknown destination pile ID: {move.dest_pile_id}")
        if self.is_won():
            return MoveResult.fail("Game is already won")

        is_valid, error_msg, cmd = self._validate_move(move)
        if not is_valid or cmd is None:
            return MoveResult.fail(error_msg)

        if self.execute_command(cmd):
            if self._check_win_condition():
                self.game_status = GameStatus.WON
            return MoveResult.ok(cmd)
        return MoveResult.fail("Failed to execute move command")

    def undo(self) -> bool:
        """Rolls back the most recent command."""
        res = super().undo()
        if res:
            self.game_status = GameStatus.IN_PROGRESS
        return res

    def redo(self) -> bool:
        """Re-applies the most recently undone command."""
        res = super().redo()
        if res and self._check_win_condition():
            self.game_status = GameStatus.WON
        return res

    # -------------------------------------------------------------------------
    # Internal Validation Logic
    # -------------------------------------------------------------------------
    def _infer_move_type(self, move: Move) -> Optional[FreeCellMoveType]:
        if move.move_type is not None:
            if isinstance(move.move_type, FreeCellMoveType):
                return move.move_type
            if isinstance(move.move_type, str):
                try:
                    return FreeCellMoveType(move.move_type)
                except ValueError:
                    pass

        src = move.source_pile_id
        dst = move.dest_pile_id

        if src.startswith("cascade") or src.startswith("tableau"):
            if dst.startswith("freecell") or dst.startswith("cell"):
                return FreeCellMoveType.CASCADE_TO_FREECELL
            if dst.startswith("foundation"):
                return FreeCellMoveType.CASCADE_TO_FOUNDATION
            if dst.startswith("cascade") or dst.startswith("tableau"):
                return FreeCellMoveType.CASCADE_TO_CASCADE

        if src.startswith("freecell") or src.startswith("cell"):
            if dst.startswith("cascade") or dst.startswith("tableau"):
                return FreeCellMoveType.FREECELL_TO_CASCADE
            if dst.startswith("foundation"):
                return FreeCellMoveType.FREECELL_TO_FOUNDATION
            if dst.startswith("freecell") or dst.startswith("cell"):
                return FreeCellMoveType.FREECELL_TO_FREECELL

        if src.startswith("foundation"):
            if dst.startswith("cascade") or dst.startswith("tableau"):
                return FreeCellMoveType.FOUNDATION_TO_CASCADE
            if dst.startswith("freecell") or dst.startswith("cell"):
                return FreeCellMoveType.FOUNDATION_TO_FREECELL

        return None

    def _validate_move(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        mtype = self._infer_move_type(move)

        if mtype == FreeCellMoveType.CASCADE_TO_FREECELL:
            return self._validate_cascade_to_freecell(move)
        elif mtype == FreeCellMoveType.FREECELL_TO_CASCADE:
            return self._validate_freecell_to_cascade(move)
        elif mtype == FreeCellMoveType.CASCADE_TO_FOUNDATION:
            return self._validate_cascade_to_foundation(move)
        elif mtype == FreeCellMoveType.FREECELL_TO_FOUNDATION:
            return self._validate_freecell_to_foundation(move)
        elif mtype == FreeCellMoveType.CASCADE_TO_CASCADE:
            return self._validate_cascade_to_cascade(move)
        elif mtype == FreeCellMoveType.FREECELL_TO_FREECELL:
            return self._validate_freecell_to_freecell(move)
        elif mtype == FreeCellMoveType.FOUNDATION_TO_CASCADE:
            return self._validate_foundation_to_cascade(move)
        elif mtype == FreeCellMoveType.FOUNDATION_TO_FREECELL:
            return self._validate_foundation_to_freecell(move)

        return False, f"Unsupported move type: {mtype}", None

    def _validate_cascade_to_freecell(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        src_pile = self.get_pile_by_id(move.source_pile_id)
        dst_pile = self.get_pile_by_id(move.dest_pile_id)
        if src_pile.pile_type != PileType.TABLEAU or dst_pile.pile_type != PileType.FREECELL:
            return False, "Source must be cascade and destination must be free cell", None

        if src_pile.is_empty:
            return False, "Source cascade is empty", None
        if not dst_pile.is_empty:
            return False, "Destination Free Cell is already occupied", None
        if move.card_count > 1:
            return False, "Free Cells only accept a single card", None

        card = src_pile.peek()
        if move.card_id is not None and move.card_id != card.card_id:
            return False, f"Card ID {move.card_id} does not match top card {card.card_id}", None

        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            uncovered_card_id=None,
            nominal_score_delta=0,
            moves_delta=1,
        )
        return True, "", cmd

    def _validate_freecell_to_cascade(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        src_pile = self.get_pile_by_id(move.source_pile_id)
        dst_pile = self.get_pile_by_id(move.dest_pile_id)
        if src_pile.pile_type != PileType.FREECELL or dst_pile.pile_type != PileType.TABLEAU:
            return False, "Source must be free cell and destination must be cascade", None

        if src_pile.is_empty:
            return False, "Source Free Cell is empty", None
        if move.card_count > 1:
            return False, "Only a single card can be moved from Free Cell", None

        card = src_pile.peek()
        if move.card_id is not None and move.card_id != card.card_id:
            return False, f"Card ID {move.card_id} does not match cell card {card.card_id}", None

        is_legal, reason = self._check_cascade_placement(card, dst_pile)
        if not is_legal:
            return False, reason, None

        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            uncovered_card_id=None,
            nominal_score_delta=0,
            moves_delta=1,
        )
        return True, "", cmd

    def _validate_cascade_to_foundation(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        src_pile = self.get_pile_by_id(move.source_pile_id)
        dst_pile = self.get_pile_by_id(move.dest_pile_id)
        if src_pile.pile_type != PileType.TABLEAU or dst_pile.pile_type != PileType.FOUNDATION:
            return False, "Source must be cascade and destination must be foundation", None

        if src_pile.is_empty:
            return False, "Source cascade is empty", None
        if move.card_count > 1:
            return False, "Foundations only accept a single card at a time", None

        card = src_pile.peek()
        if move.card_id is not None and move.card_id != card.card_id:
            return False, f"Card ID {move.card_id} does not match top card {card.card_id}", None

        if not self._is_legal_foundation_placement(card, dst_pile):
            if dst_pile.is_empty and card.rank != Rank.ACE:
                return False, "Only an Ace can be placed on an empty foundation", None
            if not dst_pile.is_empty:
                top = dst_pile.peek()
                if card.suit != top.suit:
                    return False, "Foundation cards must match suit", None
                if card.rank.value != top.rank.value + 1:
                    return False, "Foundation cards must ascend by rank (+1)", None
            return False, "Illegal card placement on foundation", None

        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            uncovered_card_id=None,
            nominal_score_delta=10,
            moves_delta=1,
        )
        return True, "", cmd

    def _validate_freecell_to_foundation(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        src_pile = self.get_pile_by_id(move.source_pile_id)
        dst_pile = self.get_pile_by_id(move.dest_pile_id)
        if src_pile.pile_type != PileType.FREECELL or dst_pile.pile_type != PileType.FOUNDATION:
            return False, "Source must be free cell and destination must be foundation", None

        if src_pile.is_empty:
            return False, "Source Free Cell is empty", None
        if move.card_count > 1:
            return False, "Foundations only accept a single card at a time", None

        card = src_pile.peek()
        if move.card_id is not None and move.card_id != card.card_id:
            return False, f"Card ID {move.card_id} does not match cell card {card.card_id}", None

        if not self._is_legal_foundation_placement(card, dst_pile):
            if dst_pile.is_empty and card.rank != Rank.ACE:
                return False, "Only an Ace can be placed on an empty foundation", None
            if not dst_pile.is_empty:
                top = dst_pile.peek()
                if card.suit != top.suit:
                    return False, "Foundation cards must match suit", None
                if card.rank.value != top.rank.value + 1:
                    return False, "Foundation cards must ascend by rank (+1)", None
            return False, "Illegal card placement on foundation", None

        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            uncovered_card_id=None,
            nominal_score_delta=10,
            moves_delta=1,
        )
        return True, "", cmd

    def _validate_cascade_to_cascade(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        src_pile = self.get_pile_by_id(move.source_pile_id)
        dst_pile = self.get_pile_by_id(move.dest_pile_id)
        if src_pile.pile_type != PileType.TABLEAU or dst_pile.pile_type != PileType.TABLEAU:
            return False, "Both source and destination must be cascade columns", None

        if src_pile.pile_id == dst_pile.pile_id:
            return False, "Source and destination cascades must be different", None
        if src_pile.is_empty:
            return False, "Source cascade is empty", None

        # Resolve card count from card_id if provided
        k = move.card_count
        if move.card_id is not None:
            c_idx = src_pile.find_card_index(move.card_id)
            if c_idx is None:
                return False, f"Card ID {move.card_id} not found in source cascade", None
            k = len(src_pile) - c_idx

        if k < 1 or k > len(src_pile):
            return False, f"Invalid card count: {k}", None

        start_idx = len(src_pile) - k
        moving_cards = src_pile.cards[start_idx:]

        # 1. Verify internal alternating descending sequence
        for idx in range(len(moving_cards) - 1):
            c_curr = moving_cards[idx]
            c_next = moving_cards[idx + 1]
            if c_curr.rank.value != c_next.rank.value + 1:
                return False, "Moving sequence is not in strictly descending rank order", None
            if c_curr.color == c_next.color:
                return False, "Moving sequence does not alternate in color", None

        # 2. Check destination placement
        base_card = moving_cards[0]
        is_legal, reason = self._check_cascade_placement(base_card, dst_pile)
        if not is_legal:
            return False, reason, None

        # 3. Supermove capacity validation
        max_allowed = self.calculate_max_supermove_cards(move.dest_pile_id)
        if k > max_allowed:
            N = self.get_empty_freecell_count()
            K = self.get_empty_cascade_count()
            return False, (
                f"Cannot move {k} cards: maximum allowable supermove is {max_allowed} "
                f"(based on {N} free cells and {K} empty cascades)"
            ), None

        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[c.card_id for c in moving_cards],
            uncovered_card_id=None,
            nominal_score_delta=0,
            moves_delta=1,
        )
        return True, "", cmd

    def _validate_freecell_to_freecell(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        src_pile = self.get_pile_by_id(move.source_pile_id)
        dst_pile = self.get_pile_by_id(move.dest_pile_id)
        if src_pile.pile_type != PileType.FREECELL or dst_pile.pile_type != PileType.FREECELL:
            return False, "Both source and destination must be free cells", None

        if src_pile.pile_id == dst_pile.pile_id:
            return False, "Source and destination free cells must be different", None
        if src_pile.is_empty:
            return False, "Source Free Cell is empty", None
        if not dst_pile.is_empty:
            return False, "Destination Free Cell is already occupied", None

        card = src_pile.peek()
        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            uncovered_card_id=None,
            nominal_score_delta=0,
            moves_delta=1,
        )
        return True, "", cmd

    def _validate_foundation_to_cascade(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        if not self.allow_foundation_demotion:
            return False, "Cards cannot be moved out of foundations in FreeCell", None

        src_pile = self.get_pile_by_id(move.source_pile_id)
        dst_pile = self.get_pile_by_id(move.dest_pile_id)
        if src_pile.pile_type != PileType.FOUNDATION or dst_pile.pile_type != PileType.TABLEAU:
            return False, "Source must be foundation and destination must be cascade", None

        if src_pile.is_empty:
            return False, "Foundation pile is empty", None

        card = src_pile.peek()
        is_legal, reason = self._check_cascade_placement(card, dst_pile)
        if not is_legal:
            return False, reason, None

        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            uncovered_card_id=None,
            nominal_score_delta=-15,
            moves_delta=1,
        )
        return True, "", cmd

    def _validate_foundation_to_freecell(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        if not self.allow_foundation_demotion:
            return False, "Cards cannot be moved out of foundations in FreeCell", None

        src_pile = self.get_pile_by_id(move.source_pile_id)
        dst_pile = self.get_pile_by_id(move.dest_pile_id)

        if src_pile.pile_type != PileType.FOUNDATION or dst_pile.pile_type != PileType.FREECELL:
            return False, "Source must be foundation and destination must be free cell", None
        if src_pile.is_empty:
            return False, "Foundation pile is empty", None
        if not dst_pile.is_empty:
            return False, "Destination Free Cell is already occupied", None
        if move.card_count > 1:
            return False, "Only a single card can be moved to Free Cell", None

        card = src_pile.peek()
        if move.card_id is not None and move.card_id != card.card_id:
            return False, f"Card ID {move.card_id} does not match foundation top card {card.card_id}", None

        cmd = CardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[card.card_id],
            uncovered_card_id=None,
            nominal_score_delta=-15,
            moves_delta=1,
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

    def _check_cascade_placement(self, card: Card, c_pile: Pile) -> Tuple[bool, str]:
        if c_pile.is_empty:
            # In FreeCell, ANY card may be placed into an empty cascade
            return True, ""

        top = c_pile.peek()
        if card.color == top.color:
            return False, "Cascade cards must alternate in color (Red on Black, Black on Red)"
        if top.rank.value != card.rank.value + 1:
            return False, "Cascade cards must be placed in strictly descending rank order"

        return True, ""

    def _is_legal_cascade_placement(self, card: Card, c_pile: Pile) -> bool:
        res, _ = self._check_cascade_placement(card, c_pile)
        return res

    # -------------------------------------------------------------------------
    # Safe Auto-Play & Auto-Complete Solver
    # -------------------------------------------------------------------------
    def is_safe_foundation(self, card: Card) -> bool:
        """Card is safe if Ace, 2, or both opposite-color foundations >= rank - 1."""
        if card.rank.value <= 2:
            return True
        target_rank = card.rank.value - 1
        opp_color = Color.RED if card.color == Color.BLACK else Color.BLACK
        opp_foundations = [
            f for f in self.foundations
            if not f.is_empty and f.peek().color == opp_color
        ]
        if len(opp_foundations) < 2:
            return False
        return all(f.peek().rank.value >= target_rank for f in opp_foundations)

    def is_safe_to_autoplay(self, card: Card) -> bool:
        """Alias for is_safe_foundation."""
        return self.is_safe_foundation(card)

    def _check_win_condition(self) -> bool:
        return sum(len(f) for f in self.foundations) == 52

    def is_won(self) -> bool:
        return self.game_status == GameStatus.WON or self._check_win_condition()

    def can_auto_finish(self) -> bool:
        """Checks if all remaining cards can safely auto-play to foundations."""
        if self.is_won():
            return False

        # Lookahead: simulate safe promotions on state clone
        sim_cascades = [[c for c in col.cards] for col in self.cascades]
        sim_cells = [fc.peek() for fc in self.free_cells]
        sim_foundations: Dict[Suit, int] = {}
        for f in self.foundations:
            if not f.is_empty:
                sim_foundations[f.peek().suit] = f.peek().rank.value

        total_cards_left = sum(len(col) for col in sim_cascades) + sum(1 for c in sim_cells if c)
        if total_cards_left == 0:
            return False

        def is_safe_sim(card: Card) -> bool:
            if card.rank.value <= 2:
                return True
            req_rank = card.rank.value - 1
            opp_suits = (
                (Suit.HEARTS, Suit.DIAMONDS) if card.color == Color.BLACK
                else (Suit.SPADES, Suit.CLUBS)
            )
            return all(sim_foundations.get(s, 0) >= req_rank for s in opp_suits)

        progress = True
        while progress and total_cards_left > 0:
            progress = False
            # Check free cells
            for idx, c in enumerate(sim_cells):
                if c is None:
                    continue
                curr_rank = sim_foundations.get(c.suit, 0)
                if c.rank.value == curr_rank + 1 and is_safe_sim(c):
                    sim_foundations[c.suit] = c.rank.value
                    sim_cells[idx] = None
                    total_cards_left -= 1
                    progress = True
                    break

            if progress:
                continue

            # Check cascade tops
            for col in sim_cascades:
                if not col:
                    continue
                c = col[-1]
                curr_rank = sim_foundations.get(c.suit, 0)
                if c.rank.value == curr_rank + 1 and is_safe_sim(c):
                    sim_foundations[c.suit] = c.rank.value
                    col.pop()
                    total_cards_left -= 1
                    progress = True
                    break

        return total_cards_left == 0

    def can_auto_complete(self) -> bool:
        """Alias for can_auto_finish()."""
        return self.can_auto_finish()

    def auto_finish_step(self) -> Optional[MoveResult]:
        """Finds and executes the next safe promotion to foundation."""
        # 1. Check free cells first
        for fc_idx, fc in enumerate(self.free_cells):
            if fc.is_empty:
                continue
            card = fc.peek()
            if not self.is_safe_foundation(card):
                continue
            for f_idx, f in enumerate(self.foundations):
                if self._is_legal_foundation_placement(card, f):
                    move = Move(
                        FreeCellMoveType.FREECELL_TO_FOUNDATION,
                        f"freecell_{fc_idx}",
                        f"foundation_{f_idx}",
                        card_count=1,
                        card_id=card.card_id,
                    )
                    return self.make_move(move)

        # 2. Check cascade tops
        for c_idx, col in enumerate(self.cascades):
            if col.is_empty:
                continue
            card = col.peek()
            if not self.is_safe_foundation(card):
                continue
            for f_idx, f in enumerate(self.foundations):
                if self._is_legal_foundation_placement(card, f):
                    move = Move(
                        FreeCellMoveType.CASCADE_TO_FOUNDATION,
                        f"cascade_{c_idx}",
                        f"foundation_{f_idx}",
                        card_count=1,
                        card_id=card.card_id,
                    )
                    return self.make_move(move)

        return None

    def auto_complete_step(self) -> Optional[MoveResult]:
        """Alias for auto_finish_step()."""
        return self.auto_finish_step()

    def auto_finish_all(self) -> int:
        """Executes auto-finish loop until win or deadlock. Returns step count."""
        steps = 0
        while not self.is_won():
            res = self.auto_finish_step()
            if res is None or not res.success:
                break
            steps += 1
        return steps

    def auto_complete_all(self) -> int:
        """Alias for auto_finish_all()."""
        return self.auto_finish_all()

    # -------------------------------------------------------------------------
    # Legal Move Generation & 7-Tier Hint Engine
    # -------------------------------------------------------------------------
    def get_legal_moves(self) -> List[Move]:
        moves: List[Move] = []
        if self.is_won():
            return moves

        # 1. Moves from Free Cells
        for fc_idx, fc in enumerate(self.free_cells):
            if fc.is_empty:
                continue
            card = fc.peek()
            # To Foundations
            for f_idx, f in enumerate(self.foundations):
                if self._is_legal_foundation_placement(card, f):
                    moves.append(Move(
                        FreeCellMoveType.FREECELL_TO_FOUNDATION,
                        f"freecell_{fc_idx}",
                        f"foundation_{f_idx}",
                        card_count=1,
                        card_id=card.card_id,
                    ))
            # To Cascades
            for c_idx, col in enumerate(self.cascades):
                if self._is_legal_cascade_placement(card, col):
                    moves.append(Move(
                        FreeCellMoveType.FREECELL_TO_CASCADE,
                        f"freecell_{fc_idx}",
                        f"cascade_{c_idx}",
                        card_count=1,
                        card_id=card.card_id,
                    ))

        # 2. Moves from Cascades
        for src_idx, src_col in enumerate(self.cascades):
            if src_col.is_empty:
                continue
            top_card = src_col.peek()

            # Top card to Foundations
            for f_idx, f in enumerate(self.foundations):
                if self._is_legal_foundation_placement(top_card, f):
                    moves.append(Move(
                        FreeCellMoveType.CASCADE_TO_FOUNDATION,
                        f"cascade_{src_idx}",
                        f"foundation_{f_idx}",
                        card_count=1,
                        card_id=top_card.card_id,
                    ))

            # Top card to empty Free Cells
            for fc_idx, fc in enumerate(self.free_cells):
                if fc.is_empty:
                    moves.append(Move(
                        FreeCellMoveType.CASCADE_TO_FREECELL,
                        f"cascade_{src_idx}",
                        f"freecell_{fc_idx}",
                        card_count=1,
                        card_id=top_card.card_id,
                    ))

            # Sequence (or single card) to other Cascades
            # Find all valid alternating descending sub-sequences from top
            max_seq_len = 1
            for i in range(len(src_col) - 1, 0, -1):
                c_above = src_col[i - 1]
                c_curr = src_col[i]
                if c_above.rank.value == c_curr.rank.value + 1 and c_above.color != c_curr.color:
                    max_seq_len += 1
                else:
                    break

            for k in range(1, max_seq_len + 1):
                start_idx = len(src_col) - k
                base_c = src_col[start_idx]
                for dst_idx, dst_col in enumerate(self.cascades):
                    if dst_idx == src_idx:
                        continue
                    if self._is_legal_cascade_placement(base_c, dst_col):
                        max_allowed = self.calculate_max_supermove_cards(f"cascade_{dst_idx}")
                        if k <= max_allowed:
                            moves.append(Move(
                                FreeCellMoveType.CASCADE_TO_CASCADE,
                                f"cascade_{src_idx}",
                                f"cascade_{dst_idx}",
                                card_count=k,
                                card_id=base_c.card_id,
                            ))

        return moves

    def get_hint(self) -> Optional[Move]:
        """Returns the highest tactical utility legal move."""
        legal_moves = self.get_legal_moves()
        if not legal_moves:
            return None

        # Priority 1: Safe Foundation
        for m in legal_moves:
            if m.move_type in (
                FreeCellMoveType.FREECELL_TO_FOUNDATION,
                FreeCellMoveType.CASCADE_TO_FOUNDATION,
            ):
                src = self.get_pile_by_id(m.source_pile_id)
                card = src.peek()
                if card and self.is_safe_foundation(card):
                    return m

        # Priority 2: Cascade Liberation (emptying a column)
        for m in legal_moves:
            if m.move_type == FreeCellMoveType.CASCADE_TO_CASCADE:
                src = self.get_pile_by_id(m.source_pile_id)
                dst = self.get_pile_by_id(m.dest_pile_id)
                if len(src) == m.card_count and not dst.is_empty:
                    return m

        # Priority 3: Free Cell Evacuation
        for m in legal_moves:
            if m.move_type in (
                FreeCellMoveType.FREECELL_TO_CASCADE,
                FreeCellMoveType.FREECELL_TO_FOUNDATION,
            ):
                return m

        # Priority 4: Foundation Unlocker (expose card underneath that can move to foundation)
        for m in legal_moves:
            if m.move_type == FreeCellMoveType.CASCADE_TO_CASCADE:
                src = self.get_pile_by_id(m.source_pile_id)
                rem = len(src) - m.card_count
                if rem > 0:
                    underlying = src[rem - 1]
                    for f in self.foundations:
                        if self._is_legal_foundation_placement(underlying, f):
                            return m

        # Priority 5: Cascade Consolidation (moving sequence to non-empty cascade)
        for m in legal_moves:
            if m.move_type == FreeCellMoveType.CASCADE_TO_CASCADE:
                dst = self.get_pile_by_id(m.dest_pile_id)
                if not dst.is_empty:
                    return m

        # Priority 6: Strategic Parking to Free Cell
        for m in legal_moves:
            if m.move_type == FreeCellMoveType.CASCADE_TO_FREECELL:
                src = self.get_pile_by_id(m.source_pile_id)
                if len(src) > 1:
                    underlying = src[-2]
                    for f in self.foundations:
                        if self._is_legal_foundation_placement(underlying, f):
                            return m

        # Priority 7: Fallback to first available move
        return legal_moves[0]

    # -------------------------------------------------------------------------
    # Smart Click-to-Move Auto-Routing
    # -------------------------------------------------------------------------
    def find_best_move_for_card(self, pile_id: str, card_index: int = -1) -> Optional[Move]:
        """Auto-routes a click or double-click to the best legal destination."""
        if pile_id not in self.piles:
            return None
        src_pile = self.piles[pile_id]
        if src_pile.is_empty:
            return None

        actual_idx = card_index if card_index >= 0 else len(src_pile) + card_index
        if actual_idx < 0 or actual_idx >= len(src_pile):
            return None

        card = src_pile[actual_idx]

        # 1. Single card: Try foundations first
        if actual_idx == len(src_pile) - 1:
            for f_idx, f in enumerate(self.foundations):
                if self._is_legal_foundation_placement(card, f):
                    mtype = (
                        FreeCellMoveType.FREECELL_TO_FOUNDATION
                        if src_pile.pile_type == PileType.FREECELL
                        else FreeCellMoveType.CASCADE_TO_FOUNDATION
                    )
                    return Move(
                        mtype,
                        pile_id,
                        f"foundation_{f_idx}",
                        card_count=1,
                        card_id=card.card_id,
                    )

        # 2. Try non-empty cascades
        count = len(src_pile) - actual_idx
        for c_idx, c_col in enumerate(self.cascades):
            if c_col.pile_id == src_pile.pile_id:
                continue
            if not c_col.is_empty and self._is_legal_cascade_placement(card, c_col):
                max_allowed = self.calculate_max_supermove_cards(f"cascade_{c_idx}")
                if count <= max_allowed:
                    mtype = (
                        FreeCellMoveType.FREECELL_TO_CASCADE
                        if src_pile.pile_type == PileType.FREECELL
                        else FreeCellMoveType.CASCADE_TO_CASCADE
                    )
                    return Move(
                        mtype,
                        pile_id,
                        f"cascade_{c_idx}",
                        card_count=count,
                        card_id=card.card_id,
                    )

        # 3. If single card on cascade, try empty Free Cells
        if src_pile.pile_type == PileType.TABLEAU and actual_idx == len(src_pile) - 1:
            for fc_idx, fc in enumerate(self.free_cells):
                if fc.is_empty:
                    return Move(
                        FreeCellMoveType.CASCADE_TO_FREECELL,
                        pile_id,
                        f"freecell_{fc_idx}",
                        card_count=1,
                        card_id=card.card_id,
                    )

        # 4. Try empty cascades
        for c_idx, c_col in enumerate(self.cascades):
            if c_col.pile_id == src_pile.pile_id:
                continue
            if c_col.is_empty:
                max_allowed = self.calculate_max_supermove_cards(f"cascade_{c_idx}")
                if count <= max_allowed:
                    mtype = (
                        FreeCellMoveType.FREECELL_TO_CASCADE
                        if src_pile.pile_type == PileType.FREECELL
                        else FreeCellMoveType.CASCADE_TO_CASCADE
                    )
                    return Move(
                        mtype,
                        pile_id,
                        f"cascade_{c_idx}",
                        card_count=count,
                        card_id=card.card_id,
                    )

        return None
