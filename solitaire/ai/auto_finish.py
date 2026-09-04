"""Auto-finish assistance solver for Solitaire.

Detects when a game is in a deterministic winning state (e.g. all cards face-up
in Klondike, or safe foundation transitions in FreeCell) and provides
stepped or batch auto-completion to victory.
"""

from typing import Optional, List, Tuple
from solitaire.core.base_game import BaseGame, MoveResult


class AutoFinishController:
    """Manages fast-forward completion of games in deterministic win states."""

    @staticmethod
    def can_auto_finish(game: BaseGame) -> bool:
        """Determines if the board meets invariant criteria for auto-finish."""
        return game.can_auto_finish()

    @staticmethod
    def step(game: BaseGame) -> Optional[MoveResult]:
        """Executes a single auto-finish progression step."""
        if not game.can_auto_finish():
            return None
        return game.auto_finish_step()

    @classmethod
    def run_to_completion(cls, game: BaseGame, max_steps: int = 150) -> Tuple[int, bool]:
        """Runs auto-finish steps repeatedly until win or no steps remain.

        Returns:
            Tuple of (steps_taken, is_won).
        """
        steps = 0
        while steps < max_steps and not game.is_won() and game.can_auto_finish():
            res = game.auto_finish_step()
            if res is None or not res.success:
                break
            steps += 1
        return steps, game.is_won()
