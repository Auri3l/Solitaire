"""Tier 2 Boundary Value Analysis: Spider 13-Card Run Clearance Extremes.

Verifies boundary conditions for Spider atomic run clearances:
- Upper boundary missing: Q down to A (12 cards) does not clear.
- Lower boundary missing: K down to 2 (12 cards) does not clear.
- Suit purity boundary: 13-card run with single suit mismatch at start, middle, or end.
- Run clearance boundary when underlying cards exist.
- Run clearance boundary when column becomes completely empty.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move
from solitaire.games.spider import SpiderGame


class TestSpiderRunBoundaries(unittest.TestCase):
    """BVA: Boundary conditions for completed Spider runs."""

    def test_twelve_card_run_missing_king_does_not_clear(self) -> None:
        """TC-BVA-SR-01: Run of 12 cards (Queen down to Ace) does not trigger clearance."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Tableau 0 has Queen down to 2
        for rank in range(12, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, rank, is_face_up=True, card_id=rank - 1))

        # Tableau 1 has Ace
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(ace_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=ace_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 12)  # Not cleared because King is missing!
        self.assertEqual(len(game.foundations[0]), 0)

    def test_twelve_card_run_missing_ace_does_not_clear(self) -> None:
        """TC-BVA-SR-02: Run of 12 cards (King down to 2) does not trigger clearance."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        for rank in range(13, 2, -1):  # 13 down to 3
            game.tableau[0].push(Card(Suit.SPADES, rank, is_face_up=True, card_id=rank - 1))

        two_s = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.tableau[1].push(two_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=two_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 12)
        self.assertEqual(len(game.foundations[0]), 0)

    def test_run_with_king_suit_mismatch_does_not_clear(self) -> None:
        """TC-BVA-SR-03: 13 cards where King is Hearts and Q..A are Spades does not clear."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # King of Hearts at head
        game.tableau[0].push(Card(Suit.HEARTS, Rank.KING, is_face_up=True, card_id=25))
        # Q down to 2 of Spades
        for rank in range(12, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, rank, is_face_up=True, card_id=rank - 1))

        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(ace_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=ace_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 13)
        self.assertEqual(len(game.foundations[0]), 0)

    def test_run_with_ace_suit_mismatch_does_not_clear(self) -> None:
        """TC-BVA-SR-04: 13 cards where K..2 are Spades but Ace is Hearts does not clear."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        for rank in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, rank, is_face_up=True, card_id=rank - 1))

        ace_h = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.tableau[1].push(ace_h)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=ace_h.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 13)
        self.assertEqual(len(game.foundations[0]), 0)

    def test_clearance_leaves_column_completely_empty(self) -> None:
        """TC-BVA-SR-05: Clearing run built directly on empty column leaves column empty."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # 12 cards on tableau 0
        for rank in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, rank, is_face_up=True, card_id=rank - 1))
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(ace_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=ace_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 0)
        self.assertTrue(game.tableau[0].is_empty)
        self.assertEqual(len(game.foundations[0]), 13)


if __name__ == "__main__":
    unittest.main()
