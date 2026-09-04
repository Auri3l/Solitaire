"""Tier 3 Combinatorial: Stock Dealing, Recycling Passes, and Tableau Building Interactions.

Verifies cross-feature interactions between stock lifecycle and board state:
- Dealing from stock, playing waste to tableau, dealing again.
- Full stock cycle, playing cards to foundation, recycling remaining waste.
- Multi-pass Turn-3 dealing and sequential waste card access.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move
from solitaire.games.klondike import KlondikeGame, MoveType


class TestStockTableauInteractions(unittest.TestCase):
    """Combinatorial: Stock dealing interleaved with tableau and foundation building."""

    def test_deal_waste_to_tableau_and_deal_again(self) -> None:
        """TC-COMB-ST-01: Deal from stock, play waste card onto tableau, then deal again."""
        game = KlondikeGame(turn_mode=1, seed=42)
        game.deal_stock()
        self.assertEqual(len(game.waste), 1)
        first_waste = game.waste.peek()

        # Stage tableau 0 to accept first_waste
        game.tableau[0].clear()
        target_rank = first_waste.rank.value + 1
        if target_rank <= 13:
            target_suit = Suit.HEARTS if first_waste.is_black else Suit.SPADES
            receiver = Card(target_suit, target_rank, is_face_up=True, card_id=90)
            game.tableau[0].push(receiver)

            res = game.make_move(Move("waste", "tableau_0", card_id=first_waste.card_id))
            self.assertTrue(res.success)
            self.assertTrue(game.waste.is_empty)
            self.assertEqual(game.tableau[0].peek(), first_waste)

        # Deal next card from stock
        res2 = game.deal_stock()
        self.assertTrue(res2.success)
        self.assertEqual(len(game.waste), 1)

    def test_stock_recycle_with_reduced_waste_count(self) -> None:
        """TC-COMB-ST-02: Moving cards from waste reduces card count on subsequent recycle pass."""
        game = KlondikeGame(turn_mode=1, seed=42)
        # Deal all 24 cards
        for _ in range(24):
            game.deal_stock()
        self.assertEqual(len(game.waste), 24)

        # Move 1 card from waste to foundation
        game.foundations[0].clear()
        top_waste = game.waste.peek()
        # Stage foundation with top_waste's preceding rank
        ace_card = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.waste.pop()
        game.waste.push(ace_card)  # Replace top with Ace

        res = game.make_move(Move("waste", "foundation_0", card_id=ace_card.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.waste), 23)

        # Now recycle waste -> stock should have exactly 23 cards!
        game.make_move(Move(MoveType.RECYCLE_STOCK, "waste", "stock"))
        self.assertEqual(len(game.stock), 23)
        self.assertEqual(len(game.waste), 0)
        self.assertEqual(len(game.foundations[0]), 1)

    def test_turn3_nested_waste_uncovering(self) -> None:
        """TC-COMB-ST-03: In Turn-3, playing the top waste card reveals the 2nd waste card."""
        game = KlondikeGame(turn_mode=3, seed=42)
        game.deal_stock()
        self.assertEqual(len(game.waste), 3)

        top_waste = game.waste.peek()
        second_waste = game.waste[-2]

        # Stage tableau to accept top_waste
        game.tableau[0].clear()
        target_rank = top_waste.rank.value + 1
        if target_rank <= 13:
            target_suit = Suit.HEARTS if top_waste.is_black else Suit.SPADES
            game.tableau[0].push(Card(target_suit, target_rank, is_face_up=True, card_id=95))

            res = game.make_move(Move("waste", "tableau_0", card_id=top_waste.card_id))
            self.assertTrue(res.success)
            self.assertEqual(len(game.waste), 2)
            # The new top of waste must be the second_waste
            self.assertEqual(game.waste.peek(), second_waste)


if __name__ == "__main__":
    unittest.main()
