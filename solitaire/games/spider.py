"""Spider Solitaire Rules Engine.

Implements classic Spider Solitaire across 1-suit, 2-suit, and 4-suit variants,
with 10 tableau columns, 50-card stock deals, empty column guards, permissive
building, restrictive same-suit sequence moving, atomic 13-card King-to-Ace
run clearing, and fully reversible command deltas with fog-of-war restoration.
"""

from __future__ import annotations
from enum import Enum, unique
from typing import List, Optional, Tuple, Dict, Any, Union

from solitaire.core.card import Card, Suit, Rank, Color
from solitaire.core.pile import Pile, PileType, Deck
from solitaire.core.commands import (
    Command,
    CardMoveCommand,
    StockDealCommand,
    CommandHistory,
)
from solitaire.core.base_game import BaseGame, GameStatus, Move, MoveResult


@unique
class SpiderDifficulty(Enum):
    """Spider Solitaire suit difficulty variants."""
    ONE_SUIT = 1       # Beginner: 104 Spades (8 x 13)
    TWO_SUIT = 2       # Intermediate: 52 Spades + 52 Hearts (4 x 13 + 4 x 13)
    FOUR_SUIT = 4      # Advanced: 26 Spades + 26 Hearts + 26 Diamonds + 26 Clubs (2 x 52)

    @classmethod
    def from_value(cls, val: Union[int, str, SpiderDifficulty]) -> SpiderDifficulty:
        if isinstance(val, SpiderDifficulty):
            return val
        if isinstance(val, int) and val in (1, 2, 4):
            return cls(val)
        if isinstance(val, str):
            clean = val.strip().lower()
            if clean in ("1", "one", "beginner", "1-suit", "spider1"):
                return cls.ONE_SUIT
            if clean in ("2", "two", "intermediate", "2-suit", "spider2"):
                return cls.TWO_SUIT
            if clean in ("4", "four", "advanced", "4-suit", "spider4"):
                return cls.FOUR_SUIT
        raise ValueError(f"Invalid Spider difficulty: {val}. Must be 1, 2, or 4 suits.")


@unique
class SpiderMoveType(Enum):
    """Categorizes Spider move types."""
    TABLEAU_TO_TABLEAU = "tableau_to_tableau"
    DEAL_STOCK = "deal_stock"
    CLEAR_RUN = "clear_run"

    def __str__(self) -> str:
        return self.value


# Canonical alias for MoveType
MoveType = SpiderMoveType


class SpiderClearRunCommand(Command):
    """Atomically removes a completed 13-card run (King to Ace same suit)
    from a tableau column to a foundation pile, awarding 100 points.
    """

    def __init__(
        self,
        tableau_id: str,
        foundation_id: str,
        card_ids: List[int],
        uncovered_card_id: Optional[int] = None,
        score_delta: int = 100,
    ) -> None:
        self.tableau_id = str(tableau_id)
        self.foundation_id = str(foundation_id)
        self.card_ids = list(card_ids)
        self.uncovered_card_id = uncovered_card_id
        self._score_delta = score_delta

    @property
    def score_delta(self) -> int:
        return self._score_delta

    @property
    def moves_delta(self) -> int:
        return 0  # Run clearance is an automatic side effect, not a player turn

    def execute(self, game: Any) -> bool:
        tab = game.get_pile_by_id(self.tableau_id)
        fnd = game.get_pile_by_id(self.foundation_id)
        if tab is None or fnd is None:
            return False

        cards = tab.remove_from(len(tab) - len(self.card_ids))
        fnd.push_many(cards)

        if self.uncovered_card_id is not None and not tab.is_empty:
            top = tab.peek()
            if top and top.card_id == self.uncovered_card_id:
                top.is_face_up = True

        game.score += self._score_delta
        return True

    def undo(self, game: Any) -> bool:
        tab = game.get_pile_by_id(self.tableau_id)
        fnd = game.get_pile_by_id(self.foundation_id)
        if tab is None or fnd is None:
            return False

        game.score -= self._score_delta

        if self.uncovered_card_id is not None:
            idx = tab.find_card_index(self.uncovered_card_id)
            if idx is not None:
                tab[idx].is_face_up = False

        cards = fnd.remove_from(len(fnd) - len(self.card_ids))
        tab.push_many(cards)
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "SpiderClearRunCommand",
            "tableau_id": self.tableau_id,
            "foundation_id": self.foundation_id,
            "card_ids": self.card_ids,
            "uncovered_card_id": self.uncovered_card_id,
            "score_delta": self._score_delta,
            "moves_delta": 0,
        }


class SpiderCardMoveCommand(Command):
    """Encapsulates transferring a valid same-suit descending stack between
    tableau columns, handling auto-flipping exposed cards, secondary run clearances,
    and move scoring.
    """

    def __init__(
        self,
        source_pile_id: str,
        dest_pile_id: str,
        card_ids: List[int],
        uncovered_card_id: Optional[int] = None,
        score_delta: int = -1,
        moves_delta: int = 1,
        secondary_commands: Optional[List[Command]] = None,
    ) -> None:
        self.source_pile_id = str(source_pile_id)
        self.dest_pile_id = str(dest_pile_id)
        self.card_ids = list(card_ids)
        self.uncovered_card_id = uncovered_card_id
        self.nominal_score_delta = score_delta
        self.actual_score_delta: int = score_delta
        self._moves_delta = moves_delta
        self.secondary_commands: List[Command] = list(secondary_commands) if secondary_commands else []

    @property
    def score_delta(self) -> int:
        return self.actual_score_delta

    @property
    def moves_delta(self) -> int:
        return self._moves_delta

    def execute(self, game: Any) -> bool:
        src = game.get_pile_by_id(self.source_pile_id)
        dst = game.get_pile_by_id(self.dest_pile_id)
        if src is None or dst is None:
            return False

        start_idx = src.find_card_index(self.card_ids[0])
        if start_idx is None:
            return False

        moved_cards = src.remove_from(start_idx)
        dst.push_many(moved_cards)

        if self.uncovered_card_id is not None and not src.is_empty:
            top = src.peek()
            if top and top.card_id == self.uncovered_card_id:
                top.is_face_up = True

        for sub_cmd in self.secondary_commands:
            sub_cmd.execute(game)

        prev_score = game.score
        game.score = max(0, game.score + self.nominal_score_delta)
        self.actual_score_delta = game.score - prev_score
        game.moves_count += self._moves_delta
        return True

    def undo(self, game: Any) -> bool:
        src = game.get_pile_by_id(self.source_pile_id)
        dst = game.get_pile_by_id(self.dest_pile_id)
        if src is None or dst is None:
            return False

        for sub_cmd in reversed(self.secondary_commands):
            sub_cmd.undo(game)

        if self.uncovered_card_id is not None:
            idx = src.find_card_index(self.uncovered_card_id)
            if idx is not None:
                src[idx].is_face_up = False

        return_start_idx = len(dst) - len(self.card_ids)
        if return_start_idx < 0:
            return False
        returned_cards = dst.remove_from(return_start_idx)
        src.push_many(returned_cards)

        game.score -= self.actual_score_delta
        game.moves_count -= self._moves_delta
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "SpiderCardMoveCommand",
            "source_pile_id": self.source_pile_id,
            "dest_pile_id": self.dest_pile_id,
            "card_ids": self.card_ids,
            "uncovered_card_id": self.uncovered_card_id,
            "score_delta": self.actual_score_delta,
            "moves_delta": self._moves_delta,
            "secondary_commands": [cmd.to_dict() for cmd in self.secondary_commands],
        }


class SpiderDealCommand(Command):
    """Encapsulates dealing 10 cards from Stock across all 10 tableau columns,
    checking for completed runs triggered by the deal, and full reversibility.
    """

    def __init__(
        self,
        deal_targets: List[str],
        card_ids: Optional[List[int]] = None,
        score_delta: int = -1,
        moves_delta: int = 1,
        secondary_commands: Optional[List[Command]] = None,
    ) -> None:
        self.deal_targets = list(deal_targets)
        self.card_ids: List[int] = list(card_ids) if card_ids else []
        self.nominal_score_delta = score_delta
        self.actual_score_delta: int = score_delta
        self._moves_delta = moves_delta
        self.secondary_commands: List[Command] = list(secondary_commands) if secondary_commands else []

    @property
    def score_delta(self) -> int:
        return self.actual_score_delta

    @property
    def moves_delta(self) -> int:
        return self._moves_delta

    def execute(self, game: Any) -> bool:
        stock = game.get_pile_by_id("stock")
        if stock is None or len(stock) < len(self.deal_targets):
            return False

        if not self.card_ids:
            dealt_ids = []
            for target_id in self.deal_targets:
                target_pile = game.get_pile_by_id(target_id)
                card = stock.pop()
                card.is_face_up = True
                target_pile.push(card)
                dealt_ids.append(card.card_id)
            self.card_ids = dealt_ids
        else:
            for target_id in self.deal_targets:
                target_pile = game.get_pile_by_id(target_id)
                card = stock.pop()
                card.is_face_up = True
                target_pile.push(card)

        for sub_cmd in self.secondary_commands:
            sub_cmd.execute(game)

        prev_score = game.score
        game.score = max(0, game.score + self.nominal_score_delta)
        self.actual_score_delta = game.score - prev_score
        game.moves_count += self._moves_delta
        return True

    def undo(self, game: Any) -> bool:
        stock = game.get_pile_by_id("stock")
        if stock is None:
            return False

        for sub_cmd in reversed(self.secondary_commands):
            sub_cmd.undo(game)

        for target_id in reversed(self.deal_targets):
            target_pile = game.get_pile_by_id(target_id)
            card = target_pile.pop()
            card.is_face_up = False
            stock.push(card)

        game.score -= self.actual_score_delta
        game.moves_count -= self._moves_delta
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "SpiderDealCommand",
            "deal_targets": self.deal_targets,
            "card_ids": self.card_ids,
            "score_delta": self.actual_score_delta,
            "moves_delta": self._moves_delta,
            "secondary_commands": [cmd.to_dict() for cmd in self.secondary_commands],
        }


class SpiderGame(BaseGame):
    """Full implementation of Spider Solitaire game rules."""

    def __init__(
        self,
        difficulty: Union[int, str, SpiderDifficulty] = SpiderDifficulty.ONE_SUIT,
        seed: Optional[int] = None,
        num_suits: Optional[int] = None,
    ) -> None:
        self._game_status: GameStatus = GameStatus.IN_PROGRESS
        super().__init__(mode_name="spider")
        if num_suits is not None:
            self.difficulty: SpiderDifficulty = SpiderDifficulty.from_value(num_suits)
        else:
            self.difficulty = SpiderDifficulty.from_value(difficulty)
        self.num_suits: int = self.difficulty.value
        self.seed: Optional[int] = seed

        self.stock: Pile = Pile("stock", PileType.STOCK)
        self.foundations: List[Pile] = [
            Pile(f"foundation_{i}", PileType.FOUNDATION, index=i) for i in range(8)
        ]
        self.tableau: List[Pile] = [
            Pile(f"tableau_{i}", PileType.TABLEAU, index=i) for i in range(10)
        ]
        self.cascades = self.tableau

        self.piles: Dict[str, Pile] = {
            "stock": self.stock,
            **{f"foundation_{i}": self.foundations[i] for i in range(8)},
            **{f"tableau_{i}": self.tableau[i] for i in range(10)},
            **{f"cascade_{i}": self.tableau[i] for i in range(10)},
        }

        self._completed_runs: int = 0
        self._deals_remaining: int = 5
        self.initial_cards_order: List[Card] = []
        self.start_new_game(seed=seed)

    @property
    def game_status(self) -> GameStatus:
        if self._check_win_condition():
            return GameStatus.WON
        return self._game_status

    @game_status.setter
    def game_status(self, val: GameStatus) -> None:
        self._game_status = val

    @property
    def deals_remaining(self) -> int:
        return len(self.stock) // 10

    @deals_remaining.setter
    def deals_remaining(self, val: int) -> None:
        self._deals_remaining = val

    @property
    def completed_runs(self) -> int:
        runs_in_foundations = sum(1 for f in self.foundations if len(f) == 13)
        return max(self._completed_runs, runs_in_foundations)

    @completed_runs.setter
    def completed_runs(self, val: int) -> None:
        self._completed_runs = val

    # -------------------------------------------------------------------------
    # Game Initialization & Deal
    # -------------------------------------------------------------------------
    def start_new_game(self, seed: Optional[int] = None) -> None:
        """Deals a fresh 104-card Spider layout with optional seed."""
        if seed is not None:
            self.seed = seed

        cards = Deck.create_spider_deck(num_suits=self.num_suits)
        cards = Deck.shuffle_cards(cards, seed=self.seed)
        self.initial_cards_order = [c.clone() for c in cards]
        self._deal_cards(cards)

    def restart(self) -> None:
        """Restarts game with the exact same initial deck permutation."""
        cards = [c.clone() for c in self.initial_cards_order]
        self._deal_cards(cards)

    def _deal_cards(self, cards: List[Card]) -> None:
        """Distributes cards into 10 tableau columns and stock pile."""
        self.stock.clear()
        for f in self.foundations:
            f.clear()
        for t in self.tableau:
            t.clear()

        self.history.clear()
        self.moves_count = 0
        self.score = 500
        self._completed_runs = 0
        self.game_status = GameStatus.IN_PROGRESS

        card_idx = 0
        # Columns 0-3 receive 6 cards (5 face-down, 1 face-up)
        for col_idx in range(4):
            for k in range(6):
                card = cards[card_idx]
                card_idx += 1
                card.is_face_up = (k == 5)
                self.tableau[col_idx].push(card)

        # Columns 4-9 receive 5 cards (4 face-down, 1 face-up)
        for col_idx in range(4, 10):
            for k in range(5):
                card = cards[card_idx]
                card_idx += 1
                card.is_face_up = (k == 4)
                self.tableau[col_idx].push(card)

        # Remaining 50 cards to stock face-down
        while card_idx < len(cards):
            card = cards[card_idx]
            card_idx += 1
            card.is_face_up = False
            self.stock.push(card)

    def get_pile_by_id(self, pile_id: str) -> Pile:
        """Retrieves pile by string identifier."""
        if pile_id in self.piles:
            return self.piles[pile_id]
        raise ValueError(f"Unknown pile ID: {pile_id}")

    # -------------------------------------------------------------------------
    # Move Validation & Execution Pipeline
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

        if self.execute_command(cmd):
            if self._check_win_condition():
                self.game_status = GameStatus.WON
            return MoveResult.ok(cmd)
        return MoveResult.fail("Failed to execute move command")

    def deal_stock(self) -> MoveResult:
        """High-level action: deals 1 card to each of the 10 tableau columns."""
        move = Move(SpiderMoveType.DEAL_STOCK, "stock", "tableau_0")
        return self.make_move(move)

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
    # Internal Validation Logic
    # -------------------------------------------------------------------------
    def _infer_move_type(self, move: Move) -> Optional[SpiderMoveType]:
        if move.move_type is not None:
            if isinstance(move.move_type, SpiderMoveType):
                return move.move_type
            if isinstance(move.move_type, str):
                try:
                    return SpiderMoveType(move.move_type)
                except ValueError:
                    pass

        src = move.source_pile_id
        dst = move.dest_pile_id
        if src == "stock":
            return SpiderMoveType.DEAL_STOCK
        if (src.startswith("tableau") or src.startswith("cascade")) and (dst.startswith("tableau") or dst.startswith("cascade")):
            return SpiderMoveType.TABLEAU_TO_TABLEAU
        return None

    def _validate_move(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        mtype = self._infer_move_type(move)
        if mtype == SpiderMoveType.DEAL_STOCK:
            return self._validate_deal_stock(move)
        elif mtype == SpiderMoveType.TABLEAU_TO_TABLEAU:
            return self._validate_tableau_to_tableau(move)
        return False, f"Unsupported move type: {mtype}", None

    def _validate_deal_stock(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        src_pile = self.get_pile_by_id(move.source_pile_id)
        if src_pile.pile_type != PileType.STOCK:
            return False, "Deal stock move must originate from stock pile", None

        if self.stock.is_empty or len(self.stock) < 10:
            return False, "Stock is empty", None

        # Guard: Cannot deal if ANY tableau column is empty
        for i, col in enumerate(self.tableau):
            if col.is_empty:
                return False, "Cannot deal from stock while any tableau column is empty", None

        deal_targets = [f"tableau_{i}" for i in range(10)]

        # Simulate deal to discover secondary run clearances
        temp_col_cards: Dict[int, List[Card]] = {
            i: list(self.tableau[i].cards) + [self.stock.cards[-1 - i].clone(is_face_up=True)] for i in range(10)
        }

        secondary_cmds: List[Command] = []
        foundation_idx = self._get_next_foundation_index()

        for col_idx in range(10):
            sim_cards = temp_col_cards[col_idx]
            run = self._detect_run_in_card_list(sim_cards)
            if run is not None and foundation_idx < 8:
                run_card_ids = [c.card_id for c in run]
                # Check uncovered card underneath
                rem_len = len(sim_cards) - 13
                uncovered_id = None
                if rem_len > 0 and not sim_cards[rem_len - 1].is_face_up:
                    uncovered_id = sim_cards[rem_len - 1].card_id

                cmd = SpiderClearRunCommand(
                    tableau_id=f"tableau_{col_idx}",
                    foundation_id=f"foundation_{foundation_idx}",
                    card_ids=run_card_ids,
                    uncovered_card_id=uncovered_id,
                )
                secondary_cmds.append(cmd)
                foundation_idx += 1

        deal_cmd = SpiderDealCommand(
            deal_targets=deal_targets,
            secondary_commands=secondary_cmds,
        )
        return True, "", deal_cmd

    def _validate_tableau_to_tableau(self, move: Move) -> Tuple[bool, str, Optional[Command]]:
        if move.source_pile_id == move.dest_pile_id:
            return False, "Source and destination columns must be different", None

        src_pile = self.get_pile_by_id(move.source_pile_id)
        dst_pile = self.get_pile_by_id(move.dest_pile_id)
        if src_pile.pile_type != PileType.TABLEAU or dst_pile.pile_type != PileType.TABLEAU:
            return False, "Both source and destination must be tableau columns", None

        if src_pile.is_empty:
            return False, "Source tableau column is empty", None

        # Resolve card count k and moving cards
        k = move.card_count
        if move.card_id is not None:
            c_idx = src_pile.find_card_index(move.card_id)
            if c_idx is None:
                return False, f"Card ID {move.card_id} not found in source column", None
            k = len(src_pile) - c_idx

        if k < 1 or k > len(src_pile):
            return False, "Invalid card count", None

        start_idx = len(src_pile) - k
        moving_cards = src_pile.cards[start_idx:]

        # Check all face up
        if any(not c.is_face_up for c in moving_cards):
            return False, "Cannot move face-down cards", None

        # Check strictly descending AND SAME SUIT
        for i in range(len(moving_cards) - 1):
            c_curr = moving_cards[i]
            c_next = moving_cards[i + 1]
            if c_curr.rank.value != c_next.rank.value + 1 or c_curr.suit != c_next.suit:
                return False, "Cards do not form a single-suit descending sequence", None

        # Placement Check
        base_card = moving_cards[0]
        if not dst_pile.is_empty:
            dst_top = dst_pile.peek()
            if dst_top.rank.value != base_card.rank.value + 1:
                return False, f"Card {base_card} cannot be placed on {dst_top} (must be rank + 1)", None
        # Empty column accepts ANY card or valid same-suit sequence

        # Check auto-flip uncovered card in source
        rem_count = len(src_pile) - k
        uncovered_id = None
        if rem_count > 0 and not src_pile.cards[rem_count - 1].is_face_up:
            uncovered_id = src_pile.cards[rem_count - 1].card_id

        # Simulate destination column to check for completed run
        sim_dst_cards = list(dst_pile.cards) + list(moving_cards)
        secondary_cmds: List[Command] = []
        foundation_idx = self._get_next_foundation_index()

        dst_run = self._detect_run_in_card_list(sim_dst_cards)
        if dst_run is not None and foundation_idx < 8:
            dst_run_ids = [c.card_id for c in dst_run]
            rem_dst = len(sim_dst_cards) - 13
            dst_uncovered_id = None
            if rem_dst > 0 and not sim_dst_cards[rem_dst - 1].is_face_up:
                dst_uncovered_id = sim_dst_cards[rem_dst - 1].card_id

            secondary_cmds.append(
                SpiderClearRunCommand(
                    tableau_id=move.dest_pile_id,
                    foundation_id=f"foundation_{foundation_idx}",
                    card_ids=dst_run_ids,
                    uncovered_card_id=dst_uncovered_id,
                )
            )
            foundation_idx += 1

        # Check if source column now exposes a completed run underneath
        sim_src_cards = list(src_pile.cards[:start_idx])
        if uncovered_id is not None and len(sim_src_cards) > 0:
            sim_src_cards[-1] = sim_src_cards[-1].clone(is_face_up=True)

        src_run = self._detect_run_in_card_list(sim_src_cards)
        if src_run is not None and foundation_idx < 8:
            src_run_ids = [c.card_id for c in src_run]
            rem_src = len(sim_src_cards) - 13
            src_sub_uncovered = None
            if rem_src > 0 and not sim_src_cards[rem_src - 1].is_face_up:
                src_sub_uncovered = sim_src_cards[rem_src - 1].card_id

            secondary_cmds.append(
                SpiderClearRunCommand(
                    tableau_id=move.source_pile_id,
                    foundation_id=f"foundation_{foundation_idx}",
                    card_ids=src_run_ids,
                    uncovered_card_id=src_sub_uncovered,
                )
            )

        cmd = SpiderCardMoveCommand(
            source_pile_id=move.source_pile_id,
            dest_pile_id=move.dest_pile_id,
            card_ids=[c.card_id for c in moving_cards],
            uncovered_card_id=uncovered_id,
            secondary_commands=secondary_cmds,
        )
        return True, "", cmd

    # -------------------------------------------------------------------------
    # Foundation Run Detection
    # -------------------------------------------------------------------------
    def _detect_run_in_card_list(self, cards: List[Card]) -> Optional[List[Card]]:
        """Checks if the topmost 13 cards form a complete K->A same-suit run."""
        if len(cards) < 13:
            return None

        sub = cards[-13:]
        if any(not c.is_face_up for c in sub):
            return None

        # Check King down to Ace
        if sub[0].rank != Rank.KING or sub[-1].rank != Rank.ACE:
            return None

        target_suit = sub[0].suit
        if any(c.suit != target_suit for c in sub):
            return None
        for i in range(12):
            if sub[i].rank.value != sub[i + 1].rank.value + 1:
                return None

        return list(sub)

    def _get_next_foundation_index(self) -> int:
        """Returns index of the next empty foundation pile (0..7)."""
        for i, f in enumerate(self.foundations):
            if f.is_empty:
                return i
        return 8

    # -------------------------------------------------------------------------
    # Win Condition & Auto-Finish
    # -------------------------------------------------------------------------
    def _check_win_condition(self) -> bool:
        """Returns True if all 8 foundation piles contain completed runs (104 cards)."""
        return self.completed_runs >= 8 or sum(len(f) for f in self.foundations) == 104

    def is_won(self) -> bool:
        return self.game_status == GameStatus.WON or self._check_win_condition()

    def can_auto_finish(self) -> bool:
        """Returns True if all cards in all columns are face up and stock is empty."""
        if not self.stock.is_empty:
            return False
        for col in self.tableau:
            if any(not c.is_face_up for c in col.cards):
                return False
        return not self.is_won()

    def can_auto_complete(self) -> bool:
        """Alias for can_auto_finish()."""
        return self.can_auto_finish()

    def auto_finish_step(self) -> Optional[MoveResult]:
        """Greedily identifies and performs consolidating same-suit moves."""
        if not self.can_auto_finish():
            return None

        legal_moves = self.get_legal_moves()
        # Prefer moves that unite same-suit cards
        for m in legal_moves:
            if m.move_type == SpiderMoveType.TABLEAU_TO_TABLEAU:
                src = self.get_pile_by_id(m.source_pile_id)
                dst = self.get_pile_by_id(m.dest_pile_id)
                if not dst.is_empty:
                    base_c = src.cards[len(src) - m.card_count]
                    if base_c.suit == dst.peek().suit:
                        return self.make_move(m)

        if legal_moves:
            return self.make_move(legal_moves[0])
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

        # Stock deal
        if not self.stock.is_empty and all(not col.is_empty for col in self.tableau):
            moves.append(Move(SpiderMoveType.DEAL_STOCK, "stock", "tableau_0"))

        # Tableau moves
        for src_idx, src_col in enumerate(self.tableau):
            if src_col.is_empty:
                continue

            movable_starts = self._get_movable_sequence_starts(src_col)
            for start_idx in movable_starts:
                k = len(src_col) - start_idx
                base_card = src_col.cards[start_idx]

                for dst_idx, dst_col in enumerate(self.tableau):
                    if dst_idx == src_idx:
                        continue

                    # Placement check
                    if dst_col.is_empty:
                        # Moving entire column from an already exposed empty column to another empty is useless
                        if start_idx == 0 and all(c.is_face_up for c in src_col.cards):
                            continue
                        moves.append(
                            Move(
                                SpiderMoveType.TABLEAU_TO_TABLEAU,
                                f"tableau_{src_idx}",
                                f"tableau_{dst_idx}",
                                card_count=k,
                                card_id=base_card.card_id,
                            )
                        )
                    else:
                        dst_top = dst_col.peek()
                        if dst_top.rank.value == base_card.rank.value + 1:
                            moves.append(
                                Move(
                                    SpiderMoveType.TABLEAU_TO_TABLEAU,
                                    f"tableau_{src_idx}",
                                    f"tableau_{dst_idx}",
                                    card_count=k,
                                    card_id=base_card.card_id,
                                )
                            )

        return moves

    def _get_movable_sequence_starts(self, col: Pile) -> List[int]:
        """Returns 0-based indices in col from which a legal same-suit
        descending sequence extends to the top of the column.
        """
        if col.is_empty or not col.peek().is_face_up:
            return []

        valid_starts = [len(col) - 1]
        for i in range(len(col) - 2, -1, -1):
            curr = col.cards[i]
            nxt = col.cards[i + 1]
            if not curr.is_face_up:
                break
            if curr.rank.value == nxt.rank.value + 1 and curr.suit == nxt.suit:
                valid_starts.append(i)
            else:
                break
        return valid_starts

    def get_hint(self) -> Optional[Move]:
        legal_moves = self.get_legal_moves()
        if not legal_moves:
            return None

        # Priority 1: Move completing a 13-card same-suit run
        for m in legal_moves:
            if m.move_type == SpiderMoveType.TABLEAU_TO_TABLEAU:
                src = self.get_pile_by_id(m.source_pile_id)
                dst = self.get_pile_by_id(m.dest_pile_id)
                base_c = src.cards[len(src) - m.card_count]
                if not dst.is_empty and dst.peek().suit == base_c.suit:
                    if len(dst) + m.card_count >= 13:
                        return m

        # Priority 2: Same-suit extension uncovering face-down card
        for m in legal_moves:
            if m.move_type == SpiderMoveType.TABLEAU_TO_TABLEAU:
                src = self.get_pile_by_id(m.source_pile_id)
                dst = self.get_pile_by_id(m.dest_pile_id)
                rem = len(src) - m.card_count
                if rem > 0 and not src.cards[rem - 1].is_face_up:
                    if not dst.is_empty and dst.peek().suit == src.cards[rem].suit:
                        return m

        # Priority 3: Different-suit extension uncovering face-down card
        for m in legal_moves:
            if m.move_type == SpiderMoveType.TABLEAU_TO_TABLEAU:
                src = self.get_pile_by_id(m.source_pile_id)
                rem = len(src) - m.card_count
                if rem > 0 and not src.cards[rem - 1].is_face_up:
                    return m

        # Priority 4: Same-suit consolidation
        for m in legal_moves:
            if m.move_type == SpiderMoveType.TABLEAU_TO_TABLEAU:
                src = self.get_pile_by_id(m.source_pile_id)
                dst = self.get_pile_by_id(m.dest_pile_id)
                if not dst.is_empty:
                    base_c = src.cards[len(src) - m.card_count]
                    if base_c.suit == dst.peek().suit:
                        return m

        # Priority 5: Cascade liberation (empties a column)
        for m in legal_moves:
            if m.move_type == SpiderMoveType.TABLEAU_TO_TABLEAU:
                src = self.get_pile_by_id(m.source_pile_id)
                if len(src) == m.card_count:
                    return m

        # Priority 6: Stock deal
        for m in legal_moves:
            if m.move_type == SpiderMoveType.DEAL_STOCK:
                return m

        return legal_moves[0]

    def find_best_move_for_card(self, pile_id: str, card_index: int = -1) -> Optional[Move]:
        """Smart click auto-routing: finds best legal destination column for card."""
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

        # Verify cards from actual_idx to top form valid same-suit descending stack
        count = len(src_pile) - actual_idx
        for i in range(actual_idx, len(src_pile) - 1):
            c_curr = src_pile.cards[i]
            c_next = src_pile.cards[i + 1]
            if c_curr.rank.value != c_next.rank.value + 1 or c_curr.suit != c_next.suit:
                return None  # Cannot move mixed or broken sequence

        # 1. Prefer same-suit parent
        for dst_idx, dst_col in enumerate(self.tableau):
            if f"tableau_{dst_idx}" == pile_id:
                continue
            if not dst_col.is_empty:
                top = dst_col.peek()
                if top.rank.value == card.rank.value + 1 and top.suit == card.suit:
                    return Move(
                        SpiderMoveType.TABLEAU_TO_TABLEAU,
                        pile_id,
                        f"tableau_{dst_idx}",
                        card_count=count,
                        card_id=card.card_id,
                    )

        # 2. Next, different-suit parent
        for dst_idx, dst_col in enumerate(self.tableau):
            if f"tableau_{dst_idx}" == pile_id:
                continue
            if not dst_col.is_empty:
                top = dst_col.peek()
                if top.rank.value == card.rank.value + 1:
                    return Move(
                        SpiderMoveType.TABLEAU_TO_TABLEAU,
                        pile_id,
                        f"tableau_{dst_idx}",
                        card_count=count,
                        card_id=card.card_id,
                    )

        # 3. Next, empty column (if not already base of empty column)
        if actual_idx > 0 or not all(c.is_face_up for c in src_pile.cards):
            for dst_idx, dst_col in enumerate(self.tableau):
                if f"tableau_{dst_idx}" == pile_id:
                    continue
                if dst_col.is_empty:
                    return Move(
                        SpiderMoveType.TABLEAU_TO_TABLEAU,
                        pile_id,
                        f"tableau_{dst_idx}",
                        card_count=count,
                        card_id=card.card_id,
                    )

        return None
