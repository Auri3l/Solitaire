"""Tier 3 Combinatorial: Cross-Pile Migration and Multi-Hop Journeys.

Verifies complex multi-hop card migrations across different pile domains:
- FreeCell: Cascade -> FreeCell -> Cascade -> Foundation.
- FreeCell: Clearing a cascade via free cells to create empty cascade for supermove.
- Klondike: Foundation demotion back to tableau to enable alternate sequencing.
- Spider: Shifting sequences across three distinct tableau columns.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move
from solitaire.games.freecell import FreeCellGame
from solitaire.games.klondike import KlondikeGame
from solitaire.games.spider import SpiderGame


class TestCrossPileCombinations(unittest.TestCase):
    """Combinatorial: Multi-hop transitions across heterogeneous pile types."""

    def test_freecell_four_hop_journey(self) -> None:
        """TC-COMB-XP-01: Card travels Cascade 0 -> FreeCell 0 -> Cascade 1 -> Foundation 0."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.cascades[1].clear()
        game.foundations[0].clear()
        game.free_cells[0].clear()

        # Cascade 0: Ace of Hearts (our traveler)
        ace_h = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.cascades[0].push(ace_h)

        # Cascade 1: 2 of Spades (intermediate receiver)
        two_s = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.cascades[1].push(two_s)

        # Hop 1: Cascade 0 -> FreeCell 0
        res1 = game.make_move(Move("cascade_0", "freecell_0", card_id=ace_h.card_id))
        self.assertTrue(res1.success)
        self.assertEqual(game.free_cells[0].peek(), ace_h)

        # Hop 2: FreeCell 0 -> Cascade 1 (on top of 2 of Spades)
        res2 = game.make_move(Move("freecell_0", "cascade_1", card_id=ace_h.card_id))
        self.assertTrue(res2.success)
        self.assertEqual(game.cascades[1].peek(), ace_h)

        # Hop 3: Cascade 1 -> Foundation 0 (Ace starts foundation)
        res3 = game.make_move(Move("cascade_1", "foundation_0", card_id=ace_h.card_id))
        self.assertTrue(res3.success)
        self.assertEqual(game.foundations[0].peek(), ace_h)
        self.assertEqual(game.cascades[1].peek(), two_s)

    def test_freecell_clear_cascade_to_enable_supermove(self) -> None:
        """TC-COMB-XP-02: Moving single cards to free cells creates empty column, expanding supermove capacity."""
        game = FreeCellGame(seed=42)
        for i in range(4):
            game.free_cells[i].clear()

        # Stage cascade 0 with 1 card: move it to free cell to make Cascade 0 empty (K increases)
        game.cascades[0].clear()
        solo_card = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.cascades[0].push(solo_card)

        res = game.make_move(Move("cascade_0", "freecell_0", card_id=solo_card.card_id))
        self.assertTrue(res.success)
        # Now cascade 0 is empty -> empty_cascades_count increases
        self.assertGreaterEqual(game.get_empty_cascade_count(), 1)
        # Supermove capacity expands: (1 + 3) * 2^1 = 8
        self.assertGreaterEqual(game.calculate_max_supermove(dest_is_empty=False), 8)

    def test_klondike_foundation_demotion_to_tableau(self) -> None:
        """TC-COMB-XP-03: Demote foundation card to tableau to unblock alternate sequence."""
        game = KlondikeGame(seed=42)
        game.foundations[0].clear()
        game.tableau[0].clear()
        game.tableau[1].clear()

        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        two_s = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        three_h = Card(Suit.HEARTS, Rank.THREE, is_face_up=True, card_id=15)

        game.foundations[0].push_many([ace_s, two_s])
        game.tableau[0].push(three_h)

        # Demote 2 of Spades from foundation onto 3 of Hearts in tableau
        res = game.make_move(Move("foundation_0", "tableau_0", card_id=two_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.foundations[0]), 1)
        self.assertEqual(game.tableau[0].peek(), two_s)

    def test_spider_multi_column_relay(self) -> None:
        """TC-COMB-XP-04: Card relays across Column 0 -> Column 1 -> Column 2 in Spider."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        game.tableau[2].clear()

        six_s = Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5)
        seven_s = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)
        eight_s = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)

        game.tableau[0].push(six_s)
        game.tableau[1].push(seven_s)
        game.tableau[2].push(eight_s)

        # Move 6 onto 7 (col 0 -> col 1)
        res1 = game.make_move(Move("tableau_0", "tableau_1", card_id=six_s.card_id))
        self.assertTrue(res1.success)

        # Move [7, 6] onto 8 (col 1 -> col 2)
        res2 = game.make_move(Move("tableau_1", "tableau_2", card_id=seven_s.card_id, card_count=2))
        self.assertTrue(res2.success)
        self.assertEqual(len(game.tableau[2]), 3)
        self.assertEqual(game.tableau[2][-1], six_s)


if __name__ == "__main__":
    unittest.main()
