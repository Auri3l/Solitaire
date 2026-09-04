"""Empirical reproduction of adversarial challenge findings in Milestone 1.

These tests assert specification compliance:
1. Exception safety: make_move, is_legal_move, and find_best_move_for_card must NEVER
   raise unhandled ValueError or AttributeError on invalid inputs, but gracefully return failure.
2. Intent integrity: specifying a card_id that is not in the source pile must be rejected,
   not silently execute against an unintended card.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move, MoveResult
from solitaire.games.klondike import KlondikeGame, MoveType


class AdversarialChallengeReproductions(unittest.TestCase):
    """Reproduces bugs and vulnerabilities identified during adversarial review."""

    def test_bug1_make_move_invalid_pile_id_unhandled_value_error(self):
        """BUG 1: make_move raises unhandled ValueError instead of MoveResult.fail()
        when source_pile_id or dest_pile_id does not exist in game.piles.
        """
        game = KlondikeGame(seed=42)
        
        # Test unknown source pile
        m_bad_src = Move(source_pile_id="nonexistent_pile", dest_pile_id="tableau_0")
        try:
            res = game.make_move(m_bad_src)
            self.assertFalse(res.success)
        except ValueError as e:
            self.fail(f"make_move raised unhandled ValueError on invalid source pile: {e}")

    def test_bug1b_make_move_invalid_dest_pile_id_unhandled_value_error(self):
        """BUG 1b: make_move raises unhandled ValueError when dest_pile_id is invalid."""
        game = KlondikeGame(seed=42)
        
        m_bad_dst = Move(source_pile_id="tableau_0", dest_pile_id="tableau_99")
        try:
            res = game.make_move(m_bad_dst)
            self.assertFalse(res.success)
        except ValueError as e:
            self.fail(f"make_move raised unhandled ValueError on invalid dest pile: {e}")

    def test_bug2_is_legal_move_invalid_pile_id_unhandled_value_error(self):
        """BUG 2: is_legal_move raises unhandled ValueError on invalid pile ID."""
        game = KlondikeGame(seed=42)
        
        m = Move(source_pile_id="garbage_pile", dest_pile_id="tableau_0")
        try:
            legal = game.is_legal_move(m)
            self.assertFalse(legal)
        except ValueError as e:
            self.fail(f"is_legal_move raised unhandled ValueError on invalid pile: {e}")

    def test_bug3_make_move_none_unhandled_attribute_error(self):
        """BUG 3: make_move(None) raises unhandled AttributeError."""
        game = KlondikeGame(seed=42)
        
        try:
            res = game.make_move(None)
            self.assertFalse(res.success)
        except AttributeError as e:
            self.fail(f"make_move(None) raised unhandled AttributeError: {e}")

    def test_bug4_find_best_move_invalid_pile_unhandled_value_error(self):
        """BUG 4: find_best_move_for_card raises unhandled ValueError on invalid pile ID."""
        game = KlondikeGame(seed=42)
        
        try:
            best = game.find_best_move_for_card("invalid_pile_id")
            self.assertIsNone(best)
        except ValueError as e:
            self.fail(f"find_best_move_for_card raised unhandled ValueError: {e}")

    def test_bug5_card_id_mismatch_silent_wrong_card_execution(self):
        """BUG 5: Passing a card_id that is NOT in source_pile ignores card_id
        and silently executes a move on a different card if legal.
        """
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        
        # Tableau 1 has 2♠ (black 2)
        c_two = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.tableau[1].push(c_two)
        
        # Tableau 0 has A♥ (red Ace)
        c_ace = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.tableau[0].push(c_ace)
        
        # Caller requests to move card 999 (which does not exist in tableau_0 or anywhere)
        # from tableau_0 to tableau_1.
        # EXPECTATION: The move MUST be rejected because card 999 is NOT in tableau_0.
        m = Move(source_pile_id="tableau_0", dest_pile_id="tableau_1", card_id=999)
        res = game.make_move(m)
        
        # If bug exists, res.success is True and A♥ was moved!
        self.assertFalse(
            res.success,
            f"Expected move with nonexistent card_id=999 to be rejected, but it succeeded! "
            f"Tableau 1 now has {len(game.tableau[1])} cards: {game.tableau[1].cards}"
        )


if __name__ == "__main__":
    unittest.main()
