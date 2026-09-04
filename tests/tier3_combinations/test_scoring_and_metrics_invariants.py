"""Tier 3 Combinatorial: Scoring Invariants, Zero Clamping, and Metric Tracking.

Verifies mathematical invariants of scores and move counters:
- Score zero-clamping: Score never drops below 0 in Standard scoring mode.
- Reversibility: score_after_undo == score_before_move.
- Monotonicity: moves_count strictly tracks player steps and reverts on rollback.
- Vegas wagering scoring invariants: -52 baseline, +5 per card, 0 recycle fee.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move
from solitaire.games.klondike import KlondikeGame, ScoringMode, MoveType


class TestScoringAndMetricsInvariants(unittest.TestCase):
    """Combinatorial: Zero-drift score tracking and metric invariance."""

    def test_score_zero_floor_clamping_on_penalty(self) -> None:
        """TC-COMB-SC-01: Penalty from foundation demotion cannot drop score below 0."""
        game = KlondikeGame(scoring_mode=ScoringMode.STANDARD, seed=42)
        game.score = 5  # Score starts at 5

        game.foundations[0].clear()
        game.tableau[0].clear()
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        two_s = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        three_h = Card(Suit.HEARTS, Rank.THREE, is_face_up=True, card_id=15)
        game.foundations[0].push_many([ace_s, two_s])
        game.tableau[0].push(three_h)

        # Demoting 2 of Spades to tableau carries -15 point penalty
        # Since score was 5, score clamps at 0 (5 - 15 = -10 -> clamped to 0)
        res = game.make_move(Move("foundation_0", "tableau_0", card_id=two_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.score, 0)

        # Reversing the demotion should add back the exact actual delta of 5 points!
        game.undo()
        self.assertEqual(game.score, 5)

    def test_score_reversibility_across_multiple_scored_actions(self) -> None:
        """TC-COMB-SC-02: Series of scored moves followed by undos restores initial score."""
        game = KlondikeGame(scoring_mode=ScoringMode.STANDARD, seed=42)
        game.score = 100
        initial_score = game.score

        # Move to foundation (+10 points)
        game.tableau[0].clear()
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[0].push(ace_s)
        game.make_move(Move("tableau_0", "foundation_0", card_id=ace_s.card_id))
        self.assertEqual(game.score, initial_score + 10)

        # Undo restores exact score
        game.undo()
        self.assertEqual(game.score, initial_score)

    def test_moves_counter_strict_reversibility(self) -> None:
        """TC-COMB-SC-03: Move counter increments on moves and decrements on undos."""
        game = KlondikeGame(seed=42)
        self.assertEqual(game.moves_count, 0)

        # Execute 3 moves
        game.deal_stock()
        game.deal_stock()
        game.deal_stock()
        self.assertEqual(game.moves_count, 3)

        # Undo 2 moves
        game.undo()
        self.assertEqual(game.moves_count, 2)
        game.undo()
        self.assertEqual(game.moves_count, 1)

        # Redo 1 move
        game.redo()
        self.assertEqual(game.moves_count, 2)

    def test_vegas_scoring_rules(self) -> None:
        """TC-COMB-SC-04: Vegas mode initializes at -52 and awards +5 per foundation card."""
        game = KlondikeGame(scoring_mode=ScoringMode.VEGAS, seed=42)
        self.assertEqual(game.score, -52)

        game.tableau[0].clear()
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[0].push(ace_s)

        # Move Ace to foundation -> +5 points (-52 + 5 = -47)
        res = game.make_move(Move("tableau_0", "foundation_0", card_id=ace_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.score, -47)

        # Undo -> restores -52
        game.undo()
        self.assertEqual(game.score, -52)


if __name__ == "__main__":
    unittest.main()
