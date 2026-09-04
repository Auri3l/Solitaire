"""Base Game Domain Abstractions.

Defines Move, MoveResult, GameStatus, and the BaseGame abstract base class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, unique
import time
from typing import Dict, List, Optional, Tuple, Any

from solitaire.core.card import Card
from solitaire.core.pile import Pile
from solitaire.core.commands import Command, CommandHistory, _CallableBool


@unique
class GameStatus(Enum):
    """Lifecycle status of a game match."""
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"

    def __str__(self) -> str:
        return self.value


class Move:
    """Represents a player action or move intent.

    Supports both keyword signatures and positional signatures:
    - Move(move_type, source_pile, dest_pile, card_count=1, card_id=None)
    - Move(source_pile_id, dest_pile_id, card_id=None, card_count=1)
    """

    def __init__(
        self,
        arg1: Any = None,
        arg2: Any = None,
        arg3: Any = None,
        arg4: Optional[int] = None,
        arg5: Optional[int] = None,
        source_pile_id: Optional[str] = None,
        dest_pile_id: Optional[str] = None,
        source_pile: Optional[str] = None,
        dest_pile: Optional[str] = None,
        card_id: Optional[int] = None,
        card_count: Optional[int] = None,
        move_type: Any = None,
    ) -> None:
        self._source_pile: str = ""
        self._dest_pile: str = ""
        self._card_id: Optional[int] = card_id
        self._card_count: int = card_count if card_count is not None else 1
        self._move_type: Any = move_type

        # Parse positionals
        if arg1 is not None:
            if isinstance(arg1, Enum) or hasattr(arg1, "value"):
                self._move_type = arg1
                if arg2 is not None:
                    self._source_pile = str(arg2)
                if arg3 is not None:
                    self._dest_pile = str(arg3)
                if arg4 is not None:
                    self._card_count = int(arg4)
                if arg5 is not None:
                    self._card_id = int(arg5)
            elif isinstance(arg1, str):
                self._source_pile = arg1
                if arg2 is not None:
                    self._dest_pile = str(arg2)
                if arg3 is not None:
                    self._card_id = int(arg3)
                if arg4 is not None:
                    self._card_count = int(arg4)

        # Keyword overrides (explicit keywords have highest priority)
        if source_pile_id is not None:
            self._source_pile = str(source_pile_id)
        elif source_pile is not None:
            self._source_pile = str(source_pile)

        if dest_pile_id is not None:
            self._dest_pile = str(dest_pile_id)
        elif dest_pile is not None:
            self._dest_pile = str(dest_pile)

        if card_count is not None:
            self._card_count = int(card_count)

        if card_id is not None:
            self._card_id = int(card_id)

        if move_type is not None:
            self._move_type = move_type

    @property
    def source_pile_id(self) -> str:
        return self._source_pile

    @property
    def source_pile(self) -> str:
        return self._source_pile

    @property
    def dest_pile_id(self) -> str:
        return self._dest_pile

    @property
    def dest_pile(self) -> str:
        return self._dest_pile

    @property
    def card_id(self) -> Optional[int]:
        return self._card_id

    @property
    def card_count(self) -> int:
        return self._card_count

    @property
    def move_type(self) -> Any:
        return self._move_type

    def __repr__(self) -> str:
        return (
            f"Move(type={self._move_type}, from={self._source_pile!r}, "
            f"to={self._dest_pile!r}, count={self._card_count}, card_id={self._card_id})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Move):
            return NotImplemented
        return (
            self._source_pile == other._source_pile and
            self._dest_pile == other._dest_pile and
            self._card_count == other._card_count and
            self._card_id == other._card_id and
            self._move_type == other._move_type
        )

    def __hash__(self) -> int:
        return hash((
            self._source_pile,
            self._dest_pile,
            self._card_count,
            self._card_id,
            getattr(self._move_type, "value", self._move_type)
        ))


@dataclass
class MoveResult:
    """Outcome of attempting a move."""
    success: bool
    command: Optional[Command] = None
    error_message: str = ""

    @classmethod
    def ok(cls, command: Optional[Command] = None) -> "MoveResult":
        return cls(success=True, command=command, error_message="")

    @classmethod
    def fail(cls, reason: str = "") -> "MoveResult":
        return cls(success=False, command=None, error_message=reason)

    def __bool__(self) -> bool:
        return self.success


class BaseGame(ABC):
    """Abstract base class establishing standard lifecycle, state queries,
    and command evaluation across all Solitaire variants.
    """

    def __init__(self, mode_name: str = "solitaire") -> None:
        self.mode_name: str = mode_name
        self.piles: Dict[str, Pile] = {}
        self.history: CommandHistory = CommandHistory()
        self.score: int = 0
        self.moves_count: int = 0
        self.recycles_count: int = 0
        self.passes_through_stock: int = 1
        self.seed: Optional[int] = None
        self.start_time: float = time.time()
        self.elapsed_time: float = 0.0
        self.game_status: GameStatus = GameStatus.IN_PROGRESS

    # -------------------------------------------------------------------------
    # Lifecycle & Game Initialization
    # -------------------------------------------------------------------------
    @abstractmethod
    def start_new_game(self, seed: Optional[int] = None) -> None:
        """Deals a fresh game layout with optional deterministic seed."""
        pass

    @abstractmethod
    def restart(self) -> None:
        """Restarts the game with the exact same initial deck layout."""
        pass

    # -------------------------------------------------------------------------
    # Core Rule & Move Evaluation
    # -------------------------------------------------------------------------
    @abstractmethod
    def get_legal_moves(self) -> List[Move]:
        """Returns all legal moves currently available from the active board state."""
        pass

    @abstractmethod
    def is_legal_move(self, move: Move) -> bool:
        """Validates if the specified move is legal according to game rules."""
        pass

    @abstractmethod
    def make_move(self, move: Move) -> MoveResult:
        """Validates, constructs, and executes a MoveCommand. Pushes to history on success."""
        pass

    @abstractmethod
    def is_won(self) -> bool:
        """Evaluates whether victory condition has been fulfilled."""
        pass

    @abstractmethod
    def can_auto_finish(self) -> bool:
        """Checks whether board meets invariant criteria for deterministic auto-finish."""
        pass

    @abstractmethod
    def auto_finish_step(self) -> Optional[MoveResult]:
        """Executes a single step of the auto-finish sequence."""
        pass

    @abstractmethod
    def get_hint(self) -> Optional[Move]:
        """Returns the highest-priority legal move, or None if no moves exist."""
        pass

    # -------------------------------------------------------------------------
    # State Inspection & Common Operations
    # -------------------------------------------------------------------------
    def get_pile(self, pile_id: str) -> Optional[Pile]:
        """Retrieves pile by its string identifier."""
        return self.piles.get(pile_id)

    def get_pile_by_id(self, pile_id: str) -> Optional[Pile]:
        """Alias for get_pile(pile_id)."""
        return self.get_pile(pile_id)

    def find_card(self, card_id: int) -> Optional[Tuple[Pile, int, Card]]:
        """Locates card across all piles. Returns (pile, index, card) or None."""
        for pile in self.piles.values():
            idx = pile.find_card_index(card_id)
            if idx is not None:
                return (pile, idx, pile[idx])
        return None

    # -------------------------------------------------------------------------
    # Reversible History Operations
    # -------------------------------------------------------------------------
    def execute_command(self, command: Command) -> bool:
        """Executes a command and records it in history on success."""
        if command.execute(self):
            self.history.push(command)
            return True
        return False

    def undo(self) -> bool:
        """Rolls back the most recent command."""
        return self.history.undo(self)

    def undo_move(self) -> bool:
        """Alias for undo()."""
        return self.undo()

    def redo(self) -> bool:
        """Re-applies the most recently undone command."""
        return self.history.redo(self)

    def redo_move(self) -> bool:
        """Alias for redo()."""
        return self.redo()

    @property
    def can_undo(self) -> _CallableBool:
        """Returns callable boolean supporting both can_undo and can_undo()."""
        return self.history.can_undo

    @property
    def can_redo(self) -> _CallableBool:
        """Returns callable boolean supporting both can_redo and can_redo()."""
        return self.history.can_redo

    # -------------------------------------------------------------------------
    # Serialization & State Snapshots
    # -------------------------------------------------------------------------
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Returns complete serializable dictionary representation of active game."""
        return {
            "mode_name": self.mode_name,
            "seed": self.seed,
            "score": self.score,
            "moves_count": self.moves_count,
            "recycles_count": self.recycles_count,
            "passes_through_stock": self.passes_through_stock,
            "elapsed_time": self.elapsed_time,
            "is_won": self.is_won(),
            "piles": {pid: pile.to_dict() for pid, pile in self.piles.items()}
        }


# Canonical alias conforming to PROJECT.md interface contract
GameState = BaseGame

