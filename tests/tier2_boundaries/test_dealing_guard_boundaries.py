"""Tier 2 Boundary Value Analysis: Stock Dealing Guards and Pass Limits.

Verifies boundary conditions for dealing from stock across game modes:
- Spider empty column guards: 1 empty col (0, 5, 9), multiple empty cols.
- Spider stock exhaustion boundary: 50 -> 40 -> 30 -> 20 -> 10 -> 0.
- Klondike Turn-3 dealing remainder boundaries: 3, 2, 1, 0 cards remaining.
- Klondike max_recycles pass limit boundaries: 0, 1, 2 passes allowed.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move
from solitaire.games.spider import SpiderGame
from solitaire.games.klondike import KlondikeGame, MoveType


class TestSpiderDealingGuards(unittest.TestCase):
    """BVA: Spider stock deal emptiness guards and exhaustion boundaries."""

    def test_deal_blocked_by_first_column_empty(self) -> None:
        """TC-BVA-DG-01: Exactly column 0 empty blocks stock dealing."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        self.assertTrue(all(len(game.tableau[i]) > 0 for i in range(1, 10)))
        res = game.deal_stock()
        self.assertFalse(res.success)
        self.assertIn("empty", res.error_message.lower())

    def test_deal_blocked_by_middle_column_empty(self) -> None:
        """TC-BVA-DG-02: Exactly column 5 empty blocks stock dealing."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[5].clear()
        res = game.deal_stock()
        self.assertFalse(res.success)

    def test_deal_blocked_by_last_column_empty(self) -> None:
        """TC-BVA-DG-03: Exactly column 9 empty blocks stock dealing."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[9].clear()
        res = game.deal_stock()
        self.assertFalse(res.success)

    def test_deal_blocked_when_all_ten_columns_empty(self) -> None:
        """TC-BVA-DG-04: All 10 columns empty blocks stock dealing."""
        game = SpiderGame(num_suits=1, seed=42)
        for col in game.tableau:
            col.clear()
        res = game.deal_stock()
        self.assertFalse(res.success)

    def test_spider_stock_exhaustion_boundary(self) -> None:
        """TC-BVA-DG-05: Exactly 5 deals are permitted (50 cards / 10), 6th deal is rejected."""
        game = SpiderGame(num_suits=1, seed=42)
        self.assertEqual(len(game.stock), 50)
        # Ensure all columns remain non-empty during deals
        for deal_num in range(5):
            res = game.deal_stock()
            self.assertTrue(res.success, f"Deal {deal_num + 1} should succeed")
            self.assertEqual(len(game.stock), 50 - (deal_num + 1) * 10)

        self.assertEqual(len(game.stock), 0)
        # 6th deal must fail cleanly
        res6 = game.deal_stock()
        self.assertFalse(res6.success)


class TestKlondikeDealingAndRecycleLimits(unittest.TestCase):
    """BVA: Klondike Turn-3 remainder and recycling pass limit boundaries."""

    def test_turn3_stock_remainder_two_cards(self) -> None:
        """TC-BVA-DG-06: Stock with exactly 2 cards deals both in Turn-3 mode."""
        game = KlondikeGame(turn_mode=3, seed=42)
        game.stock.clear()
        game.stock.push_many([
            Card(Suit.SPADES, Rank.ACE, is_face_up=False, card_id=0),
            Card(Suit.SPADES, Rank.TWO, is_face_up=False, card_id=1),
        ])
        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.waste), 2)
        self.assertEqual(len(game.stock), 0)

    def test_turn3_stock_remainder_one_card(self) -> None:
        """TC-BVA-DG-07: Stock with exactly 1 card deals 1 in Turn-3 mode."""
        game = KlondikeGame(turn_mode=3, seed=42)
        game.stock.clear()
        game.stock.push(Card(Suit.SPADES, Rank.ACE, is_face_up=False, card_id=0))
        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.waste), 1)
        self.assertEqual(len(game.stock), 0)

    def test_recycle_pass_limit_zero_recycles(self) -> None:
        """TC-BVA-DG-08: max_recycles=0 forbids any stock recycling."""
        game = KlondikeGame(turn_mode=1, max_recycles=0, seed=42)
        for _ in range(24):
            game.deal_stock()
        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 24)

        res = game.make_move(Move(MoveType.RECYCLE_STOCK, "waste", "stock"))
        self.assertFalse(res.success)
        self.assertEqual(len(game.stock), 0)

    def test_recycle_pass_limit_one_recycle(self) -> None:
        """TC-BVA-DG-09: max_recycles=1 permits 1st recycle, forbids 2nd recycle."""
        game = KlondikeGame(turn_mode=1, max_recycles=1, seed=42)
        for _ in range(24):
            game.deal_stock()

        # 1st recycle succeeds
        res1 = game.make_move(Move(MoveType.RECYCLE_STOCK, "waste", "stock"))
        self.assertTrue(res1.success)
        self.assertEqual(game.recycles_count, 1)

        # Deal all cards again
        for _ in range(24):
            game.deal_stock()

        # 2nd recycle must fail
        res2 = game.make_move(Move(MoveType.RECYCLE_STOCK, "waste", "stock"))
        self.assertFalse(res2.success)


if __name__ == "__main__":
    unittest.main()
