"""Tier 1 Feature Coverage: FreeCell Solitaire Rules Engine.

Verifies Features 11, 12, 13, 14, and 21:
- Feature 11: FreeCell Initial Deal (>= 5 tests)
- Feature 12: FreeCell Cell Management (>= 5 tests)
- Feature 13: FreeCell Foundation Stacking (>= 5 tests)
- Feature 14: FreeCell Supermove Formula (>= 5 tests)
- Feature 21: Move Validation & Rejection (>= 5 tests)
"""

import unittest
from solitaire.core.card import Card, Suit, Rank, Color
from solitaire.core.base_game import Move, MoveResult
from solitaire.games.freecell import FreeCellGame, FreeCellMoveType


class TestFreeCellInitialDeal(unittest.TestCase):
    """Feature 11: FreeCell Initial Deal."""

    def test_deal_52_cards_all_face_up(self) -> None:
        """TC-FC-F11-01: All 52 cards are face-up in initial deal."""
        game = FreeCellGame(seed=42)
        total_cards = sum(len(c) for c in game.cascades)
        self.assertEqual(total_cards, 52)
        for c in game.cascades:
            self.assertTrue(all(card.is_face_up for card in c))

    def test_deal_cascade_lengths_distribution(self) -> None:
        """TC-FC-F11-02: Cascades 0-3 have 7 cards, Cascades 4-7 have 6 cards."""
        game = FreeCellGame(seed=42)
        for i in range(4):
            self.assertEqual(len(game.cascades[i]), 7, f"Cascade {i} should have 7 cards")
        for i in range(4, 8):
            self.assertEqual(len(game.cascades[i]), 6, f"Cascade {i} should have 6 cards")

    def test_initial_freecells_and_foundations_empty(self) -> None:
        """TC-FC-F11-03: Free cells and foundations are initially empty."""
        game = FreeCellGame(seed=42)
        self.assertEqual(len(game.free_cells), 4)
        self.assertTrue(all(fc.is_empty for fc in game.free_cells))
        self.assertEqual(len(game.foundations), 4)
        self.assertTrue(all(f.is_empty for f in game.foundations))

    def test_ms_game_number_deal_determinism(self) -> None:
        """TC-FC-F11-04: Microsoft deal numbers generate consistent distributions."""
        g1 = FreeCellGame(ms_game_number=11982)
        g2 = FreeCellGame(ms_game_number=11982)
        self.assertEqual(
            [c.card_id for c in g1.cascades[0]],
            [c.card_id for c in g2.cascades[0]]
        )

    def test_restart_preserves_initial_board(self) -> None:
        """TC-FC-F11-05: restart() resets the exact initial deal layout."""
        game = FreeCellGame(seed=99)
        initial_order = [c.card_id for c in game.cascades[0]]
        # Move top card to cell
        top_card = game.cascades[0].peek()
        game.make_move(Move("cascade_0", "freecell_0", card_id=top_card.card_id))
        self.assertEqual(len(game.cascades[0]), 6)
        game.restart()
        self.assertEqual(len(game.cascades[0]), 7)
        self.assertEqual([c.card_id for c in game.cascades[0]], initial_order)
        self.assertTrue(game.free_cells[0].is_empty)


class TestFreeCellCellManagement(unittest.TestCase):
    """Feature 12: FreeCell Cell Management."""

    def test_move_card_to_free_cell(self) -> None:
        """TC-FC-F12-01: Card can move from cascade to open free cell."""
        game = FreeCellGame(seed=42)
        top_card = game.cascades[0].peek()
        res = game.make_move(Move("cascade_0", "freecell_0", card_id=top_card.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.free_cells[0]), 1)
        self.assertEqual(game.free_cells[0].peek(), top_card)

    def test_free_cell_capacity_limit(self) -> None:
        """TC-FC-F12-02: Occupied free cell cannot accept another card."""
        game = FreeCellGame(seed=42)
        top0 = game.cascades[0].peek()
        top1 = game.cascades[1].peek()
        game.make_move(Move("cascade_0", "freecell_0", card_id=top0.card_id))
        # Second move to same cell must fail
        res = game.make_move(Move("cascade_1", "freecell_0", card_id=top1.card_id))
        self.assertFalse(res.success)
        self.assertEqual(len(game.free_cells[0]), 1)

    def test_move_card_from_free_cell_to_cascade(self) -> None:
        """TC-FC-F12-03: Card can move from free cell back to valid cascade."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.cascades[1].clear()
        game.free_cells[0].clear()

        # Destination cascade: 9 of Spades (black)
        nine_spades = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        game.cascades[0].push(nine_spades)

        # Freecell card: 8 of Hearts (red)
        eight_hearts = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        game.free_cells[0].push(eight_hearts)

        res = game.make_move(Move("freecell_0", "cascade_0", card_id=eight_hearts.card_id))
        self.assertTrue(res.success)
        self.assertTrue(game.free_cells[0].is_empty)
        self.assertEqual(game.cascades[0].peek(), eight_hearts)

    def test_move_card_from_free_cell_to_foundation(self) -> None:
        """TC-FC-F12-04: Card can move directly from free cell to foundation."""
        game = FreeCellGame(seed=42)
        game.free_cells[0].clear()
        game.foundations[0].clear()

        ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.free_cells[0].push(ace_spades)

        res = game.make_move(Move("freecell_0", "foundation_0", card_id=ace_spades.card_id))
        self.assertTrue(res.success)
        self.assertTrue(game.free_cells[0].is_empty)
        self.assertEqual(game.foundations[0].peek(), ace_spades)

    def test_free_cell_move_undo_restores_state(self) -> None:
        """TC-FC-F12-05: Undoing free cell move restores card to original position."""
        game = FreeCellGame(seed=42)
        top_card = game.cascades[0].peek()
        game.make_move(Move("cascade_0", "freecell_0", card_id=top_card.card_id))
        self.assertEqual(len(game.cascades[0]), 6)
        game.undo()
        self.assertEqual(len(game.cascades[0]), 7)
        self.assertTrue(game.free_cells[0].is_empty)


class TestFreeCellFoundationStacking(unittest.TestCase):
    """Feature 13: FreeCell Foundation Stacking."""

    def test_ace_to_empty_foundation(self) -> None:
        """TC-FC-F13-01: Ace can move to empty foundation."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.foundations[0].clear()
        ace_hearts = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.cascades[0].push(ace_hearts)

        res = game.make_move(Move("cascade_0", "foundation_0", card_id=ace_hearts.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.foundations[0].peek(), ace_hearts)

    def test_sequential_rank_same_suit_on_foundation(self) -> None:
        """TC-FC-F13-02: 2 of Hearts on Ace of Hearts in foundation."""
        game = FreeCellGame(seed=42)
        game.foundations[0].clear()
        game.cascades[0].clear()
        ace_hearts = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        two_hearts = Card(Suit.HEARTS, Rank.TWO, is_face_up=True, card_id=14)
        game.foundations[0].push(ace_hearts)
        game.cascades[0].push(two_hearts)

        res = game.make_move(Move("cascade_0", "foundation_0", card_id=two_hearts.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.foundations[0]), 2)
        self.assertEqual(game.foundations[0].peek(), two_hearts)

    def test_reject_wrong_suit_on_foundation(self) -> None:
        """TC-FC-F13-03: 2 of Spades cannot be placed on Ace of Hearts."""
        game = FreeCellGame(seed=42)
        game.foundations[0].clear()
        game.cascades[0].clear()
        ace_hearts = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        two_spades = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.foundations[0].push(ace_hearts)
        game.cascades[0].push(two_spades)

        res = game.make_move(Move("cascade_0", "foundation_0", card_id=two_spades.card_id))
        self.assertFalse(res.success)

    def test_reject_gap_rank_on_foundation(self) -> None:
        """TC-FC-F13-04: 3 of Hearts cannot be placed directly on Ace of Hearts."""
        game = FreeCellGame(seed=42)
        game.foundations[0].clear()
        game.cascades[0].clear()
        ace_hearts = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        three_hearts = Card(Suit.HEARTS, Rank.THREE, is_face_up=True, card_id=15)
        game.foundations[0].push(ace_hearts)
        game.cascades[0].push(three_hearts)

        res = game.make_move(Move("cascade_0", "foundation_0", card_id=three_hearts.card_id))
        self.assertFalse(res.success)

    def test_foundation_undo_reverses_state(self) -> None:
        """TC-FC-F13-05: Undoing move to foundation returns card to cascade."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.foundations[0].clear()
        ace_hearts = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.cascades[0].push(ace_hearts)

        game.make_move(Move("cascade_0", "foundation_0", card_id=ace_hearts.card_id))
        game.undo()
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(game.cascades[0].peek(), ace_hearts)


class TestFreeCellSupermoveFormula(unittest.TestCase):
    """Feature 14: FreeCell Supermove Formula."""

    def test_supermove_formula_to_cascade(self) -> None:
        """TC-FC-F14-01: Evaluates (1 + N) * 2^K for non-empty target cascade."""
        game = FreeCellGame(seed=42)
        # N=4 empty freecells, K=0 empty cascades -> (1+4)*2^0 = 5
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=False, empty_cells=4, empty_cascades=0), 5)
        # N=2, K=1 -> (1+2)*2^1 = 6
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=False, empty_cells=2, empty_cascades=1), 6)
        # N=0, K=0 -> (1+0)*2^0 = 1
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=False, empty_cells=0, empty_cascades=0), 1)

    def test_supermove_formula_to_empty_column(self) -> None:
        """TC-FC-F14-02: Evaluates (1 + N) * 2^(K - 1) for empty target cascade."""
        game = FreeCellGame(seed=42)
        # N=4, K=1 (the empty target column itself is K=1) -> (1+4)*2^0 = 5
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=True, empty_cells=4, empty_cascades=1), 5)
        # N=2, K=2 -> (1+2)*2^1 = 6
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=True, empty_cells=2, empty_cascades=2), 6)
        # N=0, K=1 -> (1+0)*2^0 = 1
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=True, empty_cells=0, empty_cascades=1), 1)

    def test_supermove_execution_within_limit(self) -> None:
        """TC-FC-F14-03: Moving 3-card valid sequence when max is 5 succeeds."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.cascades[1].clear()
        # Ensure all 4 freecells empty -> max supermove >= 5
        for fc in game.free_cells:
            fc.clear()

        # Destination: King of Spades
        k_spades = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        game.cascades[0].push(k_spades)

        # Source: Queen of Hearts, Jack of Clubs, 10 of Diamonds
        q_hearts = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        j_clubs = Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        ten_diamonds = Card(Suit.DIAMONDS, Rank.TEN, is_face_up=True, card_id=35)
        game.cascades[1].push_many([q_hearts, j_clubs, ten_diamonds])

        res = game.make_move(Move("cascade_1", "cascade_0", card_id=q_hearts.card_id, card_count=3))
        self.assertTrue(res.success)
        self.assertEqual(len(game.cascades[0]), 4)
        self.assertEqual(len(game.cascades[1]), 0)

    def test_supermove_rejected_when_exceeding_capacity(self) -> None:
        """TC-FC-F14-04: Moving 3 cards when max is 1 (all cells full, 0 empty cascades) fails."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.cascades[1].clear()
        # Fill all 4 free cells with dummy cards
        for i, fc in enumerate(game.free_cells):
            fc.clear()
            fc.push(Card(Suit.CLUBS, i + 1, is_face_up=True, card_id=40 + i))

        # Destination: King of Spades
        k_spades = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        game.cascades[0].push(k_spades)

        # Source: 3 cards
        q_hearts = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        j_clubs = Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        ten_diamonds = Card(Suit.DIAMONDS, Rank.TEN, is_face_up=True, card_id=35)
        game.cascades[1].push_many([q_hearts, j_clubs, ten_diamonds])

        # All freecells are full and 0 empty cascades remain (cascades 2-7 non-empty)
        res = game.make_move(Move("cascade_1", "cascade_0", card_id=q_hearts.card_id, card_count=3))
        self.assertFalse(res.success)

    def test_supermove_undo_reversibility(self) -> None:
        """TC-FC-F14-05: Undoing supermove completely restores source cascade."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.cascades[1].clear()
        for fc in game.free_cells:
            fc.clear()

        k_spades = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        game.cascades[0].push(k_spades)

        q_hearts = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        j_clubs = Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        game.cascades[1].push_many([q_hearts, j_clubs])

        game.make_move(Move("cascade_1", "cascade_0", card_id=q_hearts.card_id, card_count=2))
        game.undo()
        self.assertEqual(len(game.cascades[0]), 1)
        self.assertEqual(len(game.cascades[1]), 2)
        self.assertEqual(game.cascades[1][0], q_hearts)
        self.assertEqual(game.cascades[1][1], j_clubs)


class TestFreeCellMoveValidationAndRejection(unittest.TestCase):
    """Feature 21: Move Validation & Rejection (FreeCell focus)."""

    def test_reject_invalid_move_parameters(self) -> None:
        """TC-FC-F21-01: Null moves and nonexistent piles fail cleanly."""
        game = FreeCellGame(seed=42)
        self.assertFalse(game.make_move(None).success)
        self.assertFalse(game.make_move(Move("invalid_src", "cascade_0")).success)
        self.assertFalse(game.make_move(Move("cascade_0", "invalid_dst")).success)

    def test_reject_non_alternating_cascade_move(self) -> None:
        """TC-FC-F21-02: Moving black card onto black card in cascade fails."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.cascades[1].clear()
        k_spades = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        q_clubs = Card(Suit.CLUBS, Rank.QUEEN, is_face_up=True, card_id=50)
        game.cascades[0].push(k_spades)
        game.cascades[1].push(q_clubs)

        res = game.make_move(Move("cascade_1", "cascade_0", card_id=q_clubs.card_id))
        self.assertFalse(res.success)

    def test_reject_moving_internal_card_alone(self) -> None:
        """TC-FC-F21-03: Cannot move single card that is buried in middle of cascade."""
        game = FreeCellGame(seed=42)
        buried_card = game.cascades[0][0]
        res = game.make_move(Move("cascade_0", "freecell_0", card_id=buried_card.card_id, card_count=1))
        self.assertFalse(res.success)

    def test_reject_foundation_demotion_when_disabled(self) -> None:
        """TC-FC-F21-04: Demoting from foundation to cascade is rejected by default."""
        game = FreeCellGame(seed=42, allow_foundation_demotion=False)
        game.foundations[0].clear()
        game.cascades[0].clear()
        ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.foundations[0].push(ace_spades)
        two_hearts = Card(Suit.HEARTS, Rank.TWO, is_face_up=True, card_id=14)
        game.cascades[0].push(two_hearts)

        res = game.make_move(Move("foundation_0", "cascade_0", card_id=ace_spades.card_id))
        self.assertFalse(res.success)

    def test_state_integrity_preserved_on_rejected_move(self) -> None:
        """TC-FC-F21-05: Illegal moves do not alter move counter or pile state."""
        game = FreeCellGame(seed=42)
        snap_before = game.get_state_snapshot()
        game.make_move(Move("cascade_0", "freecell_0", card_id=9999))
        snap_after = game.get_state_snapshot()
        self.assertEqual(snap_before["moves_count"], snap_after["moves_count"])
        self.assertEqual(snap_before["piles"], snap_after["piles"])


if __name__ == "__main__":
    unittest.main()
