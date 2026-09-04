"""Reversible Command Delta Architecture.

Implements Command ABC, CardMoveCommand, StockDealCommand, RecycleCommand,
and CommandHistory ensuring Apply(Delta^-1, Apply(Delta, S)) == S.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class _CallableBool(int):
    """Integer subclass that is callable and acts as a bool in both contexts:
    can_undo and can_undo() both work!
    """
    def __call__(self) -> bool:
        return bool(self)

    def __bool__(self) -> bool:
        return int(self) != 0

    def __eq__(self, other: Any) -> bool:
        return bool(self) == bool(other)


class Command(ABC):
    """Abstract base class for all reversible state-modifying actions."""

    @abstractmethod
    def execute(self, game: Any) -> bool:
        """Executes the forward state transition Delta."""
        pass

    @abstractmethod
    def undo(self, game: Any) -> bool:
        """Executes the exact inverse state transition Delta^-1."""
        pass

    @property
    @abstractmethod
    def score_delta(self) -> int:
        """Points awarded or penalized by this command."""
        pass

    @property
    @abstractmethod
    def moves_delta(self) -> int:
        """Move counter increment (usually 1)."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialization of the command."""
        pass


class CardMoveCommand(Command):
    """Represents transfer of one or more cards between two piles.

    Handles auto-flipping uncovered face-down cards in the source pile,
    and reversible re-covering on rollback.
    """

    def __init__(
        self,
        source_pile_id: str,
        dest_pile_id: str,
        card_ids: List[int],
        uncovered_card_id: Optional[int] = None,
        nominal_score_delta: int = 0,
        moves_delta: int = 1,
        secondary_commands: Optional[List[Command]] = None,
        score_delta: Optional[int] = None
    ) -> None:
        self.source_pile_id = str(source_pile_id)
        self.dest_pile_id = str(dest_pile_id)
        self.card_ids = list(card_ids)
        self.uncovered_card_id = uncovered_card_id
        if score_delta is not None:
            self.nominal_score_delta = score_delta
        else:
            self.nominal_score_delta = nominal_score_delta
        self.actual_score_delta: int = self.nominal_score_delta
        self._moves_delta = moves_delta
        self.secondary_commands = list(secondary_commands) if secondary_commands else []

    @property
    def score_delta(self) -> int:
        return self.actual_score_delta

    @property
    def moves_delta(self) -> int:
        return self._moves_delta

    def _get_pile(self, game: Any, pile_id: str) -> Any:
        if hasattr(game, "get_pile_by_id"):
            try:
                p = game.get_pile_by_id(pile_id)
                if p is not None:
                    return p
            except Exception:
                pass
        if hasattr(game, "get_pile"):
            p = game.get_pile(pile_id)
            if p is not None:
                return p
        if hasattr(game, "piles") and pile_id in game.piles:
            return game.piles[pile_id]
        return None

    def execute(self, game: Any) -> bool:
        src = self._get_pile(game, self.source_pile_id)
        dst = self._get_pile(game, self.dest_pile_id)
        if src is None or dst is None:
            return False

        # Find starting index in source pile
        start_idx = src.find_card_index(self.card_ids[0])
        if start_idx is None:
            return False

        moved_cards = src.remove_from(start_idx)
        dst.push_many(moved_cards)

        # Handle auto-flipping exposed face-down card in source
        if self.uncovered_card_id is not None:
            uncovered_card = src.peek()
            if uncovered_card and uncovered_card.card_id == self.uncovered_card_id:
                uncovered_card.is_face_up = True

        # Execute secondary commands
        for sub_cmd in self.secondary_commands:
            sub_cmd.execute(game)

        # Update metrics with zero-drift score clamping if applicable
        prev_score = game.score
        scoring_mode_val = getattr(getattr(game, "scoring_mode", None), "value", "standard")
        if scoring_mode_val == "standard":
            game.score = max(0, game.score + self.nominal_score_delta)
        else:
            game.score = game.score + self.nominal_score_delta
        self.actual_score_delta = game.score - prev_score
        game.moves_count += self._moves_delta
        return True

    def undo(self, game: Any) -> bool:
        src = self._get_pile(game, self.source_pile_id)
        dst = self._get_pile(game, self.dest_pile_id)
        if src is None or dst is None:
            return False

        # 1. Reverse secondary actions in reverse order
        for sub_cmd in reversed(self.secondary_commands):
            sub_cmd.undo(game)

        # 2. Reverse auto-flip: re-hide the uncovered card
        if self.uncovered_card_id is not None:
            idx = src.find_card_index(self.uncovered_card_id)
            if idx is not None:
                src[idx].is_face_up = False

        # 3. Return moved cards from destination back to source
        return_start_idx = len(dst) - len(self.card_ids)
        if return_start_idx < 0:
            return False
        returned_cards = dst.remove_from(return_start_idx)
        src.push_many(returned_cards)

        # 4. Reverse metrics
        game.score -= self.actual_score_delta
        game.moves_count -= self._moves_delta
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "CardMoveCommand",
            "source_pile_id": self.source_pile_id,
            "dest_pile_id": self.dest_pile_id,
            "card_ids": self.card_ids,
            "uncovered_card_id": self.uncovered_card_id,
            "score_delta": self.actual_score_delta,
            "moves_delta": self._moves_delta,
            "secondary_commands": [cmd.to_dict() for cmd in self.secondary_commands]
        }


# Alias for compatibility with core architecture plan
MoveCommand = CardMoveCommand


class StockDealCommand(Command):
    """Deals cards from Stock to Waste (Turn 1/3) or across cascades."""

    def __init__(
        self,
        card_ids: Optional[List[int]] = None,
        count: Optional[int] = None,
        source_pile_id: str = "stock",
        dest_pile_id: str = "waste",
        deal_targets: Optional[List[str]] = None,
        score_delta: int = 0,
        moves_delta: int = 1
    ) -> None:
        self.card_ids = list(card_ids) if card_ids is not None else []
        self.count = count if count is not None else len(self.card_ids)
        self.source_pile_id = source_pile_id
        self.dest_pile_id = dest_pile_id
        self.deal_targets = list(deal_targets) if deal_targets else []
        self._score_delta = score_delta
        self._moves_delta = moves_delta

    @property
    def score_delta(self) -> int:
        return self._score_delta

    @property
    def moves_delta(self) -> int:
        return self._moves_delta

    def _get_pile(self, game: Any, pile_id: str) -> Any:
        if hasattr(game, "get_pile_by_id"):
            try:
                p = game.get_pile_by_id(pile_id)
                if p is not None:
                    return p
            except Exception:
                pass
        if hasattr(game, "get_pile"):
            p = game.get_pile(pile_id)
            if p is not None:
                return p
        if hasattr(game, "piles") and pile_id in game.piles:
            return game.piles[pile_id]
        return None

    def execute(self, game: Any) -> bool:
        stock = self._get_pile(game, self.source_pile_id)
        if stock is None:
            return False

        if not self.deal_targets:
            waste = self._get_pile(game, self.dest_pile_id)
            if waste is None:
                return False
            k = len(self.card_ids) if self.card_ids else self.count
            k = min(k, len(stock))
            dealt = []
            for _ in range(k):
                card = stock.pop()
                card.is_face_up = True
                waste.push(card)
                dealt.append(card)
            self.card_ids = [c.card_id for c in dealt]
        else:
            dealt = []
            for target_id in self.deal_targets:
                target_pile = self._get_pile(game, target_id)
                card = stock.pop()
                card.is_face_up = True
                target_pile.push(card)
                dealt.append(card)
            self.card_ids = [c.card_id for c in dealt]

        game.score += self._score_delta
        game.moves_count += self._moves_delta
        return True

    def undo(self, game: Any) -> bool:
        stock = self._get_pile(game, self.source_pile_id)
        if stock is None:
            return False

        if not self.deal_targets:
            waste = self._get_pile(game, self.dest_pile_id)
            if waste is None:
                return False
            k = len(self.card_ids)
            if len(waste) < k:
                return False
            for _ in range(k):
                card = waste.pop()
                card.is_face_up = False
                stock.push(card)
        else:
            for target_id in reversed(self.deal_targets):
                target_pile = self._get_pile(game, target_id)
                card = target_pile.pop()
                card.is_face_up = False
                stock.push(card)

        game.score -= self._score_delta
        game.moves_count -= self._moves_delta
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "StockDealCommand",
            "card_ids": self.card_ids,
            "source_pile_id": self.source_pile_id,
            "dest_pile_id": self.dest_pile_id,
            "deal_targets": self.deal_targets,
            "score_delta": self._score_delta,
            "moves_delta": self._moves_delta
        }


class RecycleCommand(Command):
    """Recycles all Waste cards back into the Stock pile face-down."""

    def __init__(
        self,
        card_ids: Optional[List[int]] = None,
        source_pile_id: str = "waste",
        dest_pile_id: str = "stock",
        previous_recycles_count: int = 0,
        previous_passes_through_stock: int = 1,
        nominal_score_delta: int = 0,
        moves_delta: int = 1,
        recycles_delta: int = 1,
        score_delta: Optional[int] = None
    ) -> None:
        self.card_ids = list(card_ids) if card_ids is not None else []
        self.source_pile_id = source_pile_id
        self.dest_pile_id = dest_pile_id
        self.previous_recycles_count = previous_recycles_count
        self.previous_passes_through_stock = previous_passes_through_stock
        if score_delta is not None:
            self.nominal_score_delta = score_delta
        else:
            self.nominal_score_delta = nominal_score_delta
        self.actual_score_delta: int = self.nominal_score_delta
        self._moves_delta = moves_delta
        self.recycles_delta = recycles_delta

    @property
    def score_delta(self) -> int:
        return self.actual_score_delta

    @property
    def moves_delta(self) -> int:
        return self._moves_delta

    def _get_pile(self, game: Any, pile_id: str) -> Any:
        if hasattr(game, "get_pile_by_id"):
            try:
                p = game.get_pile_by_id(pile_id)
                if p is not None:
                    return p
            except Exception:
                pass
        if hasattr(game, "get_pile"):
            p = game.get_pile(pile_id)
            if p is not None:
                return p
        if hasattr(game, "piles") and pile_id in game.piles:
            return game.piles[pile_id]
        return None

    def execute(self, game: Any) -> bool:
        waste = self._get_pile(game, self.source_pile_id)
        stock = self._get_pile(game, self.dest_pile_id)
        if waste is None or stock is None:
            return False

        self.previous_recycles_count = getattr(game, "recycles_count", 0)
        self.previous_passes_through_stock = getattr(game, "passes_through_stock", 1)

        all_waste = waste.remove_from(0)
        self.card_ids = [c.card_id for c in all_waste]
        for card in reversed(all_waste):
            card.is_face_up = False
            stock.push(card)

        if hasattr(game, "recycles_count"):
            game.recycles_count += self.recycles_delta
        if hasattr(game, "passes_through_stock"):
            game.passes_through_stock += self.recycles_delta

        prev_score = game.score
        scoring_mode_val = getattr(getattr(game, "scoring_mode", None), "value", "standard")
        if scoring_mode_val == "standard":
            game.score = max(0, game.score + self.nominal_score_delta)
        else:
            game.score = game.score + self.nominal_score_delta
        self.actual_score_delta = game.score - prev_score

        game.moves_count += self._moves_delta
        return True

    def undo(self, game: Any) -> bool:
        waste = self._get_pile(game, self.source_pile_id)
        stock = self._get_pile(game, self.dest_pile_id)
        if waste is None or stock is None:
            return False

        game.moves_count -= self._moves_delta
        game.score -= self.actual_score_delta
        if hasattr(game, "recycles_count"):
            game.recycles_count = self.previous_recycles_count
        if hasattr(game, "passes_through_stock"):
            game.passes_through_stock = self.previous_passes_through_stock

        all_stock = stock.remove_from(0)
        for card in reversed(all_stock):
            card.is_face_up = True
            waste.push(card)

        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "RecycleCommand",
            "card_ids": self.card_ids,
            "source_pile_id": self.source_pile_id,
            "dest_pile_id": self.dest_pile_id,
            "score_delta": self.actual_score_delta,
            "moves_delta": self._moves_delta,
            "recycles_delta": self.recycles_delta
        }


# Aliases for plan compatibility
KlondikeCardMoveCommand = CardMoveCommand
KlondikeStockDealCommand = StockDealCommand
KlondikeRecycleCommand = RecycleCommand


class CommandHistory:
    """Maintains reversible undo and redo command stacks with zero drift."""

    def __init__(self) -> None:
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []

    @property
    def can_undo(self) -> _CallableBool:
        """Returns callable boolean supporting both can_undo and can_undo()."""
        return _CallableBool(1 if len(self._undo_stack) > 0 else 0)

    @property
    def can_redo(self) -> _CallableBool:
        """Returns callable boolean supporting both can_redo and can_redo()."""
        return _CallableBool(1 if len(self._redo_stack) > 0 else 0)

    @property
    def undo_count(self) -> int:
        return len(self._undo_stack)

    @property
    def redo_count(self) -> int:
        return len(self._redo_stack)

    def push(self, command: Command) -> None:
        """Pushes an executed command to the undo stack and clears redo stack."""
        self._undo_stack.append(command)
        self._redo_stack.clear()

    def undo(self, game: Any) -> bool:
        """Rolls back the most recent command."""
        if not self._undo_stack:
            return False
        command = self._undo_stack.pop()
        success = command.undo(game)
        if success:
            self._redo_stack.append(command)
            return True
        self._undo_stack.append(command)
        return False

    def redo(self, game: Any) -> bool:
        """Re-executes the most recently undone command."""
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        success = command.execute(game)
        if success:
            self._undo_stack.append(command)
            return True
        self._redo_stack.append(command)
        return False

    def clear(self) -> None:
        """Purges all undo and redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    def clear_redo(self) -> None:
        """Purges redo history."""
        self._redo_stack.clear()
