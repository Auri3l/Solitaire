"""Tier 4 Scenarios: Deterministic Spider Gameplay and Full Victory Sequences.

Verifies end-to-end Spider scenarios:
- Complete victory playout assembling 8th run and winning game.
- Deterministic 5-deal complete board progression.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move, GameStatus
from solitaire.games.spider import SpiderGame


class TestSpiderScenarios(unittest.TestCase):
    """Tier 4: Real-world deterministic Spider scenarios."""

    def test_complete_spider_victory_playout(self) -> None:
        """TC-SCEN-SPID-01: Clearing 8th run triggers 100% Spider victory."""
        game = SpiderGame(num_suits=1, seed=42)
        for col in game.tableau:
            col.clear()
        game.stock.clear()

        # 7 runs (91 cards) already completed in foundations 0..6
        card_id = 0
        for f_idx in range(7):
            for rank in Rank:
                game.foundations[f_idx].push(Card(Suit.SPADES, rank, is_face_up=True, card_id=card_id))
                card_id += 1

        self.assertFalse(game.is_won())

        # Setup 8th run: K..2 on tableau 0, Ace on tableau 1
        for rank in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, rank, is_face_up=True, card_id=card_id))
            card_id += 1

        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=card_id)
        game.tableau[1].push(ace_s)
        card_id += 1

        self.assertEqual(card_id, 104)

        # Move Ace to complete 8th run
        res = game.make_move(Move("tableau_1", "tableau_0", card_id=ace_s.card_id))
        self.assertTrue(res.success)

        # All 8 runs cleared
        self.assertEqual(len(game.foundations[7]), 13)
        self.assertTrue(all(len(f) == 13 for f in game.foundations))
        self.assertTrue(game.is_won())
        self.assertEqual(game.game_status, GameStatus.WON)

    def test_full_stock_progression_five_deals(self) -> None:
        """TC-SCEN-SPID-02: Deal all 50 stock cards in 5 sequential rounds of 10."""
        game = SpiderGame(num_suits=1, seed=42)
        self.assertEqual(len(game.stock), 50)
        self.assertEqual(sum(len(c) for c in game.tableau), 54)

        for deal_round in range(5):
            # Ensure no column is empty
            self.assertTrue(all(len(col) > 0 for col in game.tableau))
            res = game.deal_stock()
            self.assertTrue(res.success)
            self.assertEqual(len(game.stock), 50 - (deal_round + 1) * 10)

        self.assertEqual(len(game.stock), 0)
        self.assertEqual(sum(len(c) for c in game.tableau), 104)


if __name__ == "__main__":
    unittest.main()
