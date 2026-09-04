"""Tier 3 Combinatorial: Spider Multi-Suit Stack Interactions.

Verifies complex multi-suit interactions in 2-suit and 4-suit Spider Solitaire:
- Peeling off same-suit sub-sequences from heterogeneous stacks.
- Valid multi-suit building vs restricted same-suit moving.
- Clearing multiple 13-card runs across different suits in the same match.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move
from solitaire.games.spider import SpiderGame


class TestSpiderMultiSuitInteractions(unittest.TestCase):
    """Combinatorial: Multi-suit Spider stacking and peeling dynamics."""

    def test_2suit_peel_homogenous_tail_from_heterogenous_head(self) -> None:
        """TC-COMB-MS-01: In 2-suit Spider, peel same-suit [9♥, 8♥, 7♥] off 10♠."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        game.tableau[2].clear()

        # Destination column 0: 10 of Hearts
        ten_h = Card(Suit.HEARTS, Rank.TEN, is_face_up=True, card_id=22)
        game.tableau[0].push(ten_h)

        # Source column 1: 10♠ (black) -> 9♥ (red) -> 8♥ (red) -> 7♥ (red)
        ten_s = Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9)
        nine_h = Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21)
        eight_h = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        seven_h = Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19)
        game.tableau[1].push_many([ten_s, nine_h, eight_h, seven_h])

        # Destination column 2: Jack of Spades (can receive 10♠)
        j_s = Card(Suit.SPADES, Rank.JACK, is_face_up=True, card_id=10)
        game.tableau[2].push(j_s)

        # 1. Moving 4-card stack [10♠, 9♥, 8♥, 7♥] onto Jack of Spades must FAIL (mixed suits)
        res_fail = game.make_move(Move("tableau_1", "tableau_2", card_id=ten_s.card_id, card_count=4))
        self.assertFalse(res_fail.success)

        # 2. Peeling 3-card stack [9♥, 8♥, 7♥] onto 10 of Hearts must SUCCEED (pure Hearts)
        res_ok = game.make_move(Move("tableau_1", "tableau_0", card_id=nine_h.card_id, card_count=3))
        self.assertTrue(res_ok.success)
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.tableau[1].peek(), ten_s)
        self.assertEqual(len(game.tableau[0]), 4)
        self.assertEqual(game.tableau[0][-1], seven_h)

    def test_4suit_interleaved_stack_moving_subsequence(self) -> None:
        """TC-COMB-MS-02: In 4-suit Spider, moving a pure Diamond sequence off Clubs."""
        game = SpiderGame(num_suits=4, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Destination: 6 of Diamonds
        six_d = Card(Suit.DIAMONDS, Rank.SIX, is_face_up=True, card_id=31)
        game.tableau[0].push(six_d)

        # Source: Queen of Clubs -> 5 of Diamonds -> 4 of Diamonds
        q_c = Card(Suit.CLUBS, Rank.QUEEN, is_face_up=True, card_id=50)
        five_d = Card(Suit.DIAMONDS, Rank.FIVE, is_face_up=True, card_id=30)
        four_d = Card(Suit.DIAMONDS, Rank.FOUR, is_face_up=True, card_id=29)
        game.tableau[1].push_many([q_c, five_d, four_d])

        # Move 5♦-4♦ onto 6♦
        res = game.make_move(Move("tableau_1", "tableau_0", card_id=five_d.card_id, card_count=2))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.tableau[1].peek(), q_c)
        self.assertEqual(len(game.tableau[0]), 3)

    def test_clearing_two_runs_different_suits_in_same_game(self) -> None:
        """TC-COMB-MS-03: Assemble and clear both a Spades run and a Hearts run."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        game.tableau[2].clear()
        game.tableau[3].clear()

        # Setup Spades run: 12 cards on col 0, Ace on col 1
        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, r, is_face_up=True, card_id=r - 1))
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(ace_s)

        # Setup Hearts run: 12 cards on col 2, Ace on col 3
        for r in range(13, 1, -1):
            game.tableau[2].push(Card(Suit.HEARTS, r, is_face_up=True, card_id=r + 12))
        ace_h = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.tableau[3].push(ace_h)

        # Clear Spades run
        res_s = game.make_move(Move("tableau_1", "tableau_0", card_id=ace_s.card_id))
        self.assertTrue(res_s.success)
        self.assertEqual(len(game.foundations[0]), 13)

        # Clear Hearts run
        res_h = game.make_move(Move("tableau_3", "tableau_2", card_id=ace_h.card_id))
        self.assertTrue(res_h.success)
        self.assertEqual(len(game.foundations[1]), 13)

        # Both columns emptied, both foundations filled with 13 cards each
        self.assertTrue(game.tableau[0].is_empty)
        self.assertTrue(game.tableau[2].is_empty)


if __name__ == "__main__":
    unittest.main()
