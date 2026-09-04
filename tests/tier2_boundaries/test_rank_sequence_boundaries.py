"""Tier 2 Boundary Value Analysis: Rank Bounds and Sequence Extremes.

Verifies rank boundaries and non-wrapping invariant enforcement:
- Lower rank bound: Ace (1) cannot receive cards in tableau.
- Upper rank bound: King (13) cannot be placed on tableau cards.
- Non-wrapping: No circular wrapping between Ace and King (A on K or K on A).
- Foundation boundaries: Ace starts foundation, King terminates foundation (max 13 cards).
- Empty column rank boundaries: Only King allowed on empty Klondike tableau.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move
from solitaire.games.klondike import KlondikeGame
from solitaire.games.freecell import FreeCellGame


class TestRankSequenceBoundaries(unittest.TestCase):
    """BVA: Extremal card ranks and non-wrapping validation."""

    def test_ace_cannot_receive_cards_in_tableau(self) -> None:
        """TC-BVA-RNK-01: Ace cannot receive any card in tableau (no rank 0 exists)."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        ace_black = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        two_red = Card(Suit.HEARTS, Rank.TWO, is_face_up=True, card_id=14)
        game.tableau[0].push(ace_black)
        game.tableau[1].push(two_red)

        # In tableau, cards build descending, so nothing can go on an Ace
        res = game.make_move(Move("tableau_1", "tableau_0", card_id=two_red.card_id))
        self.assertFalse(res.success)

    def test_king_cannot_be_placed_on_tableau_card(self) -> None:
        """TC-BVA-RNK-02: King cannot be placed on any existing card in tableau."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        k_red = Card(Suit.HEARTS, Rank.KING, is_face_up=True, card_id=25)
        game.tableau[1].push(k_red)

        # Try placing King on every rank from Ace (1) through King (13)
        for rank_val in range(1, 14):
            game.tableau[0].clear()
            target_card = Card(Suit.SPADES, rank_val, is_face_up=True, card_id=rank_val - 1)
            game.tableau[0].push(target_card)
            res = game.make_move(Move("tableau_1", "tableau_0", card_id=k_red.card_id))
            self.assertFalse(res.success, f"King should not be placeable on rank {rank_val}")

    def test_circular_wrapping_rejected(self) -> None:
        """TC-BVA-RNK-03: No wrap-around: Ace on King and King on Ace are rejected in tableau."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.cascades[1].clear()

        k_black = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        ace_red = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.cascades[0].push(k_black)
        game.cascades[1].push(ace_red)

        # Ace on King is rejected
        res_a_on_k = game.make_move(Move("cascade_1", "cascade_0", card_id=ace_red.card_id))
        self.assertFalse(res_a_on_k.success)

        # King on Ace is rejected
        game.cascades[0].clear()
        game.cascades[1].clear()
        game.cascades[0].push(ace_red)
        game.cascades[1].push(k_black)
        res_k_on_a = game.make_move(Move("cascade_1", "cascade_0", card_id=k_black.card_id))
        self.assertFalse(res_k_on_a.success)

    def test_foundation_requires_ace_to_start(self) -> None:
        """TC-BVA-RNK-04: Non-Ace cards (2 through King) cannot start empty foundation."""
        game = KlondikeGame(seed=42)
        game.foundations[0].clear()
        game.tableau[0].clear()

        for rank_val in range(2, 14):
            game.tableau[0].clear()
            card = Card(Suit.SPADES, rank_val, is_face_up=True, card_id=rank_val - 1)
            game.tableau[0].push(card)
            res = game.make_move(Move("tableau_0", "foundation_0", card_id=card.card_id))
            self.assertFalse(res.success, f"Rank {rank_val} should not be accepted on empty foundation")
            self.assertTrue(game.foundations[0].is_empty)

    def test_foundation_terminates_at_king(self) -> None:
        """TC-BVA-RNK-05: Foundation terminates at King; no card can be placed on a completed King."""
        game = KlondikeGame(seed=42)
        game.foundations[0].clear()
        # Fill foundation with A through K of Spades
        for rank in Rank:
            game.foundations[0].push(Card(Suit.SPADES, rank, is_face_up=True, card_id=rank.value - 1))
        self.assertEqual(len(game.foundations[0]), 13)

        # Try placing another card on completed foundation
        game.tableau[0].clear()
        another_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[0].push(another_ace)

        res = game.make_move(Move("tableau_0", "foundation_0", card_id=another_ace.card_id))
        self.assertFalse(res.success)
        self.assertEqual(len(game.foundations[0]), 13)

    def test_klondike_empty_tableau_strictly_forbids_non_king(self) -> None:
        """TC-BVA-RNK-06: Non-King ranks (Queen down to Ace) are strictly rejected on empty column."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Test Queen, Jack, Ten, Ace
        for test_rank in (Rank.QUEEN, Rank.JACK, Rank.TEN, Rank.ACE):
            game.tableau[1].clear()
            c = Card(Suit.SPADES, test_rank, is_face_up=True, card_id=test_rank.value - 1)
            game.tableau[1].push(c)
            res = game.make_move(Move("tableau_1", "tableau_0", card_id=c.card_id))
            self.assertFalse(res.success, f"Non-King rank {test_rank.name} must be rejected on empty tableau")
            self.assertTrue(game.tableau[0].is_empty)


if __name__ == "__main__":
    unittest.main()
