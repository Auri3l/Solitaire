"""Comprehensive Unit and Invariant Test Suite for FreeCell Solitaire.

Target Module: solitaire.games.freecell
Author: teamwork_preview_explorer_m2_3
"""

import unittest
import random
from typing import List, Dict, Any, Tuple, Optional

from solitaire.core.card import Color, Suit, Rank, Card
from solitaire.core.pile import PileType, Pile, Deck
from solitaire.core.commands import Command, CardMoveCommand, CommandHistory
from solitaire.core.base_game import BaseGame, GameStatus, Move, MoveResult
from solitaire.games.freecell import FreeCellGame, MoveType


class TestFreeCellInitialLayout(unittest.TestCase):
    """TC-FC-001 through TC-FC-006: Layout and deal distribution invariants."""

    def test_initial_deal_card_counts(self):
        """TC-FC-001: First 4 cascades have 7 cards, last 4 have 6 cards, totaling 52."""
        game = FreeCellGame(seed=42)
        self.assertEqual(len(game.cascades), 8)
        for i in range(4):
            self.assertEqual(len(game.cascades[i]), 7, f"Cascade {i} must have 7 cards")
        for i in range(4, 8):
            self.assertEqual(len(game.cascades[i]), 6, f"Cascade {i} must have 6 cards")

        total_cards = sum(len(c) for c in game.cascades)
        self.assertEqual(total_cards, 52)

        # Ensure all 52 card IDs are unique (0..51)
        all_ids = [card.card_id for c in game.cascades for card in c]
        self.assertEqual(len(set(all_ids)), 52)
        self.assertEqual(set(all_ids), set(range(52)))

    def test_initial_all_cards_face_up(self):
        """TC-FC-002: In FreeCell, all 52 cards are face-up."""
        game = FreeCellGame(seed=42)
        for i, cascade in enumerate(game.cascades):
            for j, card in enumerate(cascade):
                self.assertTrue(card.is_face_up, f"Card at cascade {i}, pos {j} must be face-up")

    def test_initial_freecells_empty(self):
        """TC-FC-003: All 4 free cells must be empty."""
        game = FreeCellGame(seed=42)
        self.assertEqual(len(game.free_cells), 4)
        for i, cell in enumerate(game.free_cells):
            self.assertTrue(cell.is_empty, f"Free cell {i} must be initially empty")
            self.assertEqual(cell.pile_type, PileType.FREECELL)

    def test_initial_foundations_empty(self):
        """TC-FC-004: All 4 foundations must be empty."""
        game = FreeCellGame(seed=42)
        self.assertEqual(len(game.foundations), 4)
        for i, f in enumerate(game.foundations):
            self.assertTrue(f.is_empty, f"Foundation {i} must be initially empty")
            self.assertEqual(f.pile_type, PileType.FOUNDATION)

    def test_deterministic_seeded_deal(self):
        """TC-FC-005: Identical seed produces identical deal; distinct seeds differ."""
        g1 = FreeCellGame(seed=101)
        g2 = FreeCellGame(seed=101)
        g3 = FreeCellGame(seed=202)

        snap1 = g1.get_state_snapshot()
        snap2 = g2.get_state_snapshot()
        snap3 = g3.get_state_snapshot()

        self.assertEqual(snap1["piles"], snap2["piles"])
        self.assertNotEqual(snap1["piles"], snap3["piles"])

    def test_restart_preserves_initial_deal(self):
        """TC-FC-006: Restart resets board to exact initial permutation."""
        game = FreeCellGame(seed=777)
        initial_snap = game.get_state_snapshot()

        # Perform a legal move to free cell
        top_card = game.cascades[0].peek()
        res = game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="freecell_0", card_id=top_card.card_id))
        self.assertTrue(res.success)
        self.assertNotEqual(game.get_state_snapshot(), initial_snap)

        game.restart()
        self.assertEqual(game.get_state_snapshot(), initial_snap)


class TestFreeCellCells(unittest.TestCase):
    """TC-FC-010 through TC-FC-016: Free cell capacity, stashing, and evacuation."""

    def test_stash_single_card_to_empty_cell(self):
        """TC-FC-010: Moving top card from cascade to empty cell succeeds."""
        game = FreeCellGame(seed=42)
        card = game.cascades[0].peek()
        res = game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="freecell_0", card_id=card.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.free_cells[0].peek(), card)
        self.assertEqual(len(game.free_cells[0]), 1)
        self.assertEqual(len(game.cascades[0]), 6)

    def test_reject_move_to_occupied_cell(self):
        """TC-FC-011: Destination free cell already holding 1 card strictly rejects 2nd card."""
        game = FreeCellGame(seed=42)
        card1 = game.cascades[0].peek()
        game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="freecell_0", card_id=card1.card_id))

        card2 = game.cascades[1].peek()
        res = game.make_move(Move(source_pile_id="cascade_1", dest_pile_id="freecell_0", card_id=card2.card_id))
        self.assertFalse(res.success)
        self.assertIn("occupied", res.error_message.lower())
        self.assertEqual(len(game.free_cells[0]), 1)
        self.assertEqual(game.free_cells[0].peek(), card1)

    def test_reject_5th_card_when_all_cells_full(self):
        """TC-FC-012: When N=0 (all 4 cells full), any move to freecell is rejected."""
        game = FreeCellGame(seed=42)
        for i in range(4):
            c = game.cascades[i].peek()
            res = game.make_move(Move(source_pile_id=f"cascade_{i}", dest_pile_id=f"freecell_{i}", card_id=c.card_id))
            self.assertTrue(res.success)

        # 5th move attempt to any free cell
        c5 = game.cascades[4].peek()
        for cell_idx in range(4):
            res5 = game.make_move(Move(source_pile_id="cascade_4", dest_pile_id=f"freecell_{cell_idx}", card_id=c5.card_id))
            self.assertFalse(res5.success)

    def test_evacuate_cell_to_legal_cascade(self):
        """TC-FC-013: Card in freecell moves onto cascade with descending rank & alternating color."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.free_cells[0].clear()

        c_target = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)  # Black 8
        c_moving = Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19) # Red 7

        game.cascades[0].push(c_target)
        game.free_cells[0].push(c_moving)

        res = game.make_move(Move(source_pile_id="freecell_0", dest_pile_id="cascade_0", card_id=c_moving.card_id))
        self.assertTrue(res.success)
        self.assertTrue(game.free_cells[0].is_empty)
        self.assertEqual(len(game.cascades[0]), 2)
        self.assertEqual(game.cascades[0][-1], c_moving)

    def test_evacuate_cell_to_empty_cascade(self):
        """TC-FC-014: Any card in freecell can move to an empty cascade (no King requirement)."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.free_cells[0].clear()

        c_three = Card(Suit.DIAMONDS, Rank.THREE, is_face_up=True, card_id=28)
        game.free_cells[0].push(c_three)

        res = game.make_move(Move(source_pile_id="freecell_0", dest_pile_id="cascade_0", card_id=c_three.card_id))
        self.assertTrue(res.success)
        self.assertTrue(game.free_cells[0].is_empty)
        self.assertEqual(game.cascades[0].peek(), c_three)

    def test_evacuate_cell_to_foundation(self):
        """TC-FC-015: Ace in freecell can move to empty foundation."""
        game = FreeCellGame(seed=42)
        game.free_cells[0].clear()
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.free_cells[0].push(c_ace)

        res = game.make_move(Move(source_pile_id="freecell_0", dest_pile_id="foundation_0", card_id=c_ace.card_id))
        self.assertTrue(res.success)
        self.assertTrue(game.free_cells[0].is_empty)
        self.assertEqual(game.foundations[0].peek(), c_ace)

    def test_reject_multi_card_move_to_cell(self):
        """TC-FC-016: Cannot move card_count > 1 to a free cell."""
        game = FreeCellGame(seed=42)
        top = game.cascades[0].peek()
        res = game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="freecell_0", card_count=2, card_id=top.card_id))
        self.assertFalse(res.success)


class TestFreeCellSupermoveFormula(unittest.TestCase):
    """TC-FC-020 through TC-FC-022: Parameterized mathematical formula verification.
    
    Tests all 70 combinations of N in [0..4] and K in [0..7]:
    - To non-empty cascade: (1 + N) * 2^K
    - To empty cascade: (1 + N) * 2^(K - 1) for K >= 1
    """

    def test_supermove_formula_non_empty_cascade(self):
        """TC-FC-020: Verify (1 + N) * 2^K for all 40 combinations of N (0..4) and K (0..7)."""
        game = FreeCellGame(seed=42)
        for n in range(5):        # 0..4 empty cells
            for k in range(8):    # 0..7 empty cascades
                with self.subTest(N=n, K=k, target="non_empty"):
                    expected = (1 + n) * (2 ** k)
                    actual = game.calculate_max_supermove(dest_is_empty=False, empty_cells=n, empty_cascades=k)
                    self.assertEqual(actual, expected, f"Failed for N={n}, K={k} moving to non-empty cascade")

    def test_supermove_formula_empty_cascade(self):
        """TC-FC-021: Verify (1 + N) * 2^(K - 1) for all 35 combinations of N (0..4) and K (1..7)."""
        game = FreeCellGame(seed=42)
        for n in range(5):        # 0..4 empty cells
            for k in range(1, 8): # 1..7 empty cascades
                with self.subTest(N=n, K=k, target="empty"):
                    expected = (1 + n) * (2 ** (k - 1))
                    actual = game.calculate_max_supermove(dest_is_empty=True, empty_cells=n, empty_cascades=k)
                    self.assertEqual(actual, expected, f"Failed for N={n}, K={k} moving to empty cascade")

    def test_supermove_formula_zero_empty_cascades_empty_target(self):
        """TC-FC-022: If K=0, moving to an empty cascade is impossible (returns 0)."""
        game = FreeCellGame(seed=42)
        for n in range(5):
            actual = game.calculate_max_supermove(dest_is_empty=True, empty_cells=n, empty_cascades=0)
            self.assertEqual(actual, 0)


class TestFreeCellSupermoveValidation(unittest.TestCase):
    """TC-FC-030 through TC-FC-036: Rejections on sequence size and validity."""

    def _setup_custom_board(self, game: FreeCellGame, empty_cells_count: int, empty_cascades_count: int):
        """Configures board state with exactly empty_cells_count and empty_cascades_count."""
        for cell in game.free_cells:
            cell.clear()
        # Fill (4 - empty_cells_count) cells with dummy cards
        for i in range(4 - empty_cells_count):
            game.free_cells[i].push(Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=100 + i))

        for cascade in game.cascades:
            cascade.clear()

    def test_supermove_exact_boundary_accept_at_max(self):
        """TC-FC-030: Sequence of exact length == max_cards is accepted."""
        game = FreeCellGame(seed=42)
        # N=1 empty cell, K=1 empty cascade -> max_cards to non-empty = (1+1)*2^1 = 4
        self._setup_custom_board(game, empty_cells_count=1, empty_cascades_count=1)

        # Setup destination cascade_0 with Black 10
        game.cascades[0].push(Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9))

        # Setup source cascade_1 with alternating sequence of length 4: 9♥, 8♠, 7♥, 6♠
        c9 = Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21)
        c8 = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)
        c7 = Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19)
        c6 = Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5)
        game.cascades[1].push_many([c9, c8, c7, c6])

        # Cascade 2 is empty (K=1)
        # Cascade 3..7 have non-empty dummy cards
        for i in range(3, 8):
            game.cascades[i].push(Card(Suit.DIAMONDS, Rank.KING, is_face_up=True, card_id=200 + i))

        # Move 4 cards from cascade_1 to cascade_0
        m = Move(source_pile_id="cascade_1", dest_pile_id="cascade_0", card_count=4, card_id=c9.card_id)
        res = game.make_move(m)
        self.assertTrue(res.success, f"Move of 4 cards should succeed: {res.error_message}")
        self.assertEqual(len(game.cascades[0]), 5)
        self.assertEqual(game.cascades[0][-1], c6)
        self.assertTrue(game.cascades[1].is_empty)

    def test_supermove_boundary_reject_at_max_plus_one(self):
        """TC-FC-031: Sequence of length == max_cards + 1 is strictly rejected."""
        game = FreeCellGame(seed=42)
        # N=0, K=0 -> max_cards to non-empty = (1+0)*2^0 = 1
        self._setup_custom_board(game, empty_cells_count=0, empty_cascades_count=0)

        # Destination cascade_0 has 9♠
        game.cascades[0].push(Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8))

        # Source cascade_1 has 8♥, 7♠ (length 2 > max 1)
        c8 = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        c7 = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)
        game.cascades[1].push_many([c8, c7])

        # All cascades 2..7 non-empty (K=0)
        for i in range(2, 8):
            game.cascades[i].push(Card(Suit.DIAMONDS, Rank.KING, is_face_up=True, card_id=200 + i))

        m = Move(source_pile_id="cascade_1", dest_pile_id="cascade_0", card_count=2, card_id=c8.card_id)
        res = game.make_move(m)
        self.assertFalse(res.success)
        self.assertIn("supermove", res.error_message.lower())

    def test_supermove_reject_same_color_sequence(self):
        """TC-FC-032: Reject multi-card move if any adjacent pair has same color."""
        game = FreeCellGame(seed=42)
        # N=4, K=2 (large capacity)
        self._setup_custom_board(game, empty_cells_count=4, empty_cascades_count=2)

        game.cascades[0].push(Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9))

        # Source has 9♥ (red) and 8♦ (also red!)
        c9 = Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21)
        c8 = Card(Suit.DIAMONDS, Rank.EIGHT, is_face_up=True, card_id=33)
        game.cascades[1].push_many([c9, c8])

        m = Move(source_pile_id="cascade_1", dest_pile_id="cascade_0", card_count=2, card_id=c9.card_id)
        res = game.make_move(m)
        self.assertFalse(res.success)
        self.assertIn("alternat", res.error_message.lower())

    def test_supermove_reject_non_consecutive_rank_gap(self):
        """TC-FC-033: Reject move if sequence has rank gap > 1."""
        game = FreeCellGame(seed=42)
        self._setup_custom_board(game, empty_cells_count=4, empty_cascades_count=2)

        game.cascades[0].push(Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9))
        c9 = Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21)
        c7 = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)  # Gap of 2!
        game.cascades[1].push_many([c9, c7])

        m = Move(source_pile_id="cascade_1", dest_pile_id="cascade_0", card_count=2, card_id=c9.card_id)
        res = game.make_move(m)
        self.assertFalse(res.success)

    def test_supermove_reject_ascending_rank_sequence(self):
        """TC-FC-034: Reject move if sequence is ascending."""
        game = FreeCellGame(seed=42)
        self._setup_custom_board(game, empty_cells_count=4, empty_cascades_count=2)

        c7 = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)
        c8 = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        game.cascades[1].push_many([c7, c8])

        m = Move(source_pile_id="cascade_1", dest_pile_id="cascade_0", card_count=2, card_id=c7.card_id)
        res = game.make_move(m)
        self.assertFalse(res.success)

    def test_supermove_reject_target_card_rank_or_color_mismatch(self):
        """TC-FC-035: Base of sequence must match target cascade top (rank - 1, alternate color)."""
        game = FreeCellGame(seed=42)
        self._setup_custom_board(game, empty_cells_count=4, empty_cascades_count=2)

        # Target is 10♠ (black)
        game.cascades[0].push(Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9))

        # Base card is 9♣ (black 9, same color!)
        c9 = Card(Suit.CLUBS, Rank.NINE, is_face_up=True, card_id=47)
        c8 = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        game.cascades[1].push_many([c9, c8])

        res = game.make_move(Move(source_pile_id="cascade_1", dest_pile_id="cascade_0", card_count=2, card_id=c9.card_id))
        self.assertFalse(res.success)

    def test_supermove_to_empty_cascade_accepts_any_base_card(self):
        """TC-FC-036: Moving valid sequence to empty cascade accepts any rank (e.g. 7, 3, King)."""
        game = FreeCellGame(seed=42)
        # N=1, K=2 -> max to empty = (1+1)*2^(2-1) = 4
        self._setup_custom_board(game, empty_cells_count=1, empty_cascades_count=2)

        # Target cascade_0 is empty
        self.assertTrue(game.cascades[0].is_empty)

        # Source cascade_1 has 6♥, 5♠ (rank 6, not King)
        c6 = Card(Suit.HEARTS, Rank.SIX, is_face_up=True, card_id=18)
        c5 = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        game.cascades[1].push_many([c6, c5])

        # Fill cascades 2..7 such that exactly 1 other cascade is empty (total K=2)
        # cascade_2 empty
        for i in range(3, 8):
            game.cascades[i].push(Card(Suit.DIAMONDS, Rank.KING, is_face_up=True, card_id=200 + i))

        res = game.make_move(Move(source_pile_id="cascade_1", dest_pile_id="cascade_0", card_count=2, card_id=c6.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.cascades[0]), 2)
        self.assertEqual(game.cascades[0][0], c6)
        self.assertEqual(game.cascades[0][1], c5)


class TestFreeCellFoundations(unittest.TestCase):
    """TC-FC-040 through TC-FC-046: Foundation stacking and safe autoplay."""

    def test_foundation_accepts_ace_on_empty(self):
        """TC-FC-040: Any Ace can be placed on an empty foundation."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        c_ace = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.cascades[0].push(c_ace)

        res = game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="foundation_0", card_id=c_ace.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.foundations[0].peek(), c_ace)

    def test_foundation_rejects_non_ace_on_empty(self):
        """TC-FC-041: Placing Two, King, or any non-Ace on empty foundation is rejected."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        c_two = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.cascades[0].push(c_two)

        res = game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="foundation_0", card_id=c_two.card_id))
        self.assertFalse(res.success)
        self.assertIn("ace", res.error_message.lower())

    def test_foundation_ascending_same_suit_progression(self):
        """TC-FC-042: Foundation builds strictly rank + 1 of the same suit."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.foundations[0].clear()

        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        c_two = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.foundations[0].push(c_ace)
        game.cascades[0].push(c_two)

        res = game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="foundation_0", card_id=c_two.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.foundations[0].peek(), c_two)

    def test_foundation_rejects_wrong_suit(self):
        """TC-FC-043: 2♥ cannot be placed on A♠."""
        game = FreeCellGame(seed=42)
        game.foundations[0].clear()
        game.cascades[0].clear()

        c_ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        c_two_hearts = Card(Suit.HEARTS, Rank.TWO, is_face_up=True, card_id=14)
        game.foundations[0].push(c_ace_spades)
        game.cascades[0].push(c_two_hearts)

        res = game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="foundation_0", card_id=c_two_hearts.card_id))
        self.assertFalse(res.success)
        self.assertIn("suit", res.error_message.lower())

    def test_foundation_rejects_wrong_rank_jump(self):
        """TC-FC-044: 3♠ cannot be placed on A♠ (jump of 2)."""
        game = FreeCellGame(seed=42)
        game.foundations[0].clear()
        game.cascades[0].clear()

        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        c_three = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        game.foundations[0].push(c_ace)
        game.cascades[0].push(c_three)

        res = game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="foundation_0", card_id=c_three.card_id))
        self.assertFalse(res.success)

    def test_foundation_rejects_multi_card_move(self):
        """TC-FC-045: Moving multiple cards to foundation at once is disallowed."""
        game = FreeCellGame(seed=42)
        game.foundations[0].clear()
        game.cascades[0].clear()

        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        c_two = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.cascades[0].push_many([c_ace, c_two])

        res = game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="foundation_0", card_count=2, card_id=c_ace.card_id))
        self.assertFalse(res.success)

    def test_safe_foundation_autoplay_invariant(self):
        """TC-FC-046: Card rank r >= 3 is safe only when both opposite color foundations >= r - 1."""
        game = FreeCellGame(seed=42)
        # Aces and 2s are always safe
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        c_two = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        c_three_spades = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)

        self.assertTrue(game.is_safe_to_autoplay(c_ace))
        self.assertTrue(game.is_safe_to_autoplay(c_two))

        # 3♠ is unsafe if opposite red foundations (♥, ♦) have not reached rank 2
        self.assertFalse(game.is_safe_to_autoplay(c_three_spades))


class TestFreeCellUndoRedoInvariance(unittest.TestCase):
    """TC-FC-050 through TC-FC-055: Exact reversibility on all move types."""

    def test_undo_redo_single_step_cascade_to_cell(self):
        """TC-FC-050: Undo and redo cascade to cell restores exact board snapshot."""
        game = FreeCellGame(seed=42)
        initial_snap = game.get_state_snapshot()

        card = game.cascades[0].peek()
        game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="freecell_0", card_id=card.card_id))
        snap_after = game.get_state_snapshot()

        self.assertTrue(game.undo())
        self.assertEqual(game.get_state_snapshot(), initial_snap)

        self.assertTrue(game.redo())
        self.assertEqual(game.get_state_snapshot(), snap_after)

    def test_undo_redo_cell_to_cascade(self):
        """TC-FC-051: Undo and redo moving card from free cell to cascade."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.free_cells[0].clear()

        c_target = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)  # Black 8
        c_moving = Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19) # Red 7

        game.cascades[0].push(c_target)
        game.free_cells[0].push(c_moving)
        initial_snap = game.get_state_snapshot()

        res = game.make_move(Move(source_pile_id="freecell_0", dest_pile_id="cascade_0", card_id=c_moving.card_id))
        self.assertTrue(res.success)
        snap_after = game.get_state_snapshot()

        self.assertTrue(game.undo())
        self.assertEqual(game.get_state_snapshot(), initial_snap)
        self.assertEqual(game.free_cells[0].peek(), c_moving)

        self.assertTrue(game.redo())
        self.assertEqual(game.get_state_snapshot(), snap_after)

    def test_undo_redo_cascade_to_foundation(self):
        """TC-FC-052: Undo and redo moving card to foundation restores score and board."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        c_ace = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.cascades[0].push(c_ace)
        initial_snap = game.get_state_snapshot()

        res = game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="foundation_0", card_id=c_ace.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.score, 10)
        snap_after = game.get_state_snapshot()

        self.assertTrue(game.undo())
        self.assertEqual(game.score, 0)
        self.assertEqual(game.get_state_snapshot(), initial_snap)

        self.assertTrue(game.redo())
        self.assertEqual(game.score, 10)
        self.assertEqual(game.get_state_snapshot(), snap_after)

    def test_undo_redo_supermove_preserves_stack_order(self):
        """TC-FC-053: Moving 4-card supermove and undoing restores exact card positions and order."""
        game = FreeCellGame(seed=42)
        for c in game.cascades:
            c.clear()
        for f in game.free_cells:
            f.clear()

        # Destination cascade_0: 10♠
        game.cascades[0].push(Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9))

        # Source cascade_1: 9♥, 8♠, 7♥, 6♠
        stack = [
            Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21),
            Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7),
            Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19),
            Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5),
        ]
        game.cascades[1].push_many(stack)

        initial_snap = game.get_state_snapshot()

        # Execute 4-card supermove
        res = game.make_move(Move(source_pile_id="cascade_1", dest_pile_id="cascade_0", card_count=4, card_id=stack[0].card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.cascades[0]), 5)
        self.assertEqual(list(game.cascades[0].cards[1:]), stack)

        # Undo
        self.assertTrue(game.undo())
        self.assertEqual(game.get_state_snapshot(), initial_snap)
        self.assertEqual(list(game.cascades[1].cards), stack)

    def test_branch_divergence_clears_redo_stack(self):
        """TC-FC-054: Undoing then making a new move purges the redo stack."""
        game = FreeCellGame(seed=42)
        top0 = game.cascades[0].peek()
        game.make_move(Move(source_pile_id="cascade_0", dest_pile_id="freecell_0", card_id=top0.card_id))
        self.assertTrue(game.undo())
        self.assertTrue(game.can_redo())

        top1 = game.cascades[1].peek()
        game.make_move(Move(source_pile_id="cascade_1", dest_pile_id="freecell_1", card_id=top1.card_id))
        self.assertFalse(game.can_redo())

    def test_random_walk_100_step_undo_invariance_10_seeds(self):
        """TC-FC-055: 100 legal forward moves followed by 100 undos produces identical initial state across 10 seeds."""
        seeds = [11, 22, 33, 44, 55, 66, 77, 88, 99, 110]
        for seed in seeds:
            game = FreeCellGame(seed=seed)
            initial_snap = game.get_state_snapshot()
            rng = random.Random(seed)

            # 100 forward steps
            steps_taken = 0
            for _ in range(100):
                legal = game.get_legal_moves()
                if not legal:
                    break
                move = rng.choice(legal)
                res = game.make_move(move)
                if res.success:
                    steps_taken += 1

            self.assertEqual(game.moves_count, steps_taken)

            # Rollback all steps
            for _ in range(steps_taken):
                self.assertTrue(game.undo())

            self.assertFalse(game.can_undo())
            self.assertEqual(game.moves_count, 0)
            self.assertEqual(game.get_state_snapshot(), initial_snap)


class TestFreeCellWinCondition(unittest.TestCase):
    """TC-FC-060 through TC-FC-062: Victory detection."""

    def test_win_condition_all_52_cards_in_foundations(self):
        """TC-FC-060: Game is won when all 4 foundations contain 13 cards each."""
        game = FreeCellGame(seed=42)
        for c in game.cascades:
            c.clear()
        for f in game.free_cells:
            f.clear()

        # Fill all 4 foundations with full Ace to King runs
        for suit_idx, suit in enumerate((Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS)):
            for rank in Rank:
                c = Card(suit=suit, rank=rank, is_face_up=True, card_id=suit_idx * 13 + (rank - 1))
                game.foundations[suit_idx].push(c)

        self.assertTrue(game.is_won())
        self.assertEqual(game.game_status, GameStatus.WON)

    def test_game_not_won_when_51_cards_in_foundations(self):
        """TC-FC-061: 51 cards in foundations is NOT a win."""
        game = FreeCellGame(seed=42)
        for c in game.cascades:
            c.clear()
        for suit_idx, suit in enumerate((Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS)):
            max_r = 12 if suit_idx == 3 else 13
            for r in range(1, max_r + 1):
                c = Card(suit=suit, rank=Rank(r), is_face_up=True, card_id=suit_idx * 13 + (r - 1))
                game.foundations[suit_idx].push(c)

        self.assertFalse(game.is_won())
        self.assertEqual(game.game_status, GameStatus.IN_PROGRESS)

    def test_legal_moves_empty_when_won(self):
        """TC-FC-062: Legal moves list is empty when game is won."""
        game = FreeCellGame(seed=42)
        for c in game.cascades:
            c.clear()
        for f in game.free_cells:
            f.clear()
        for suit_idx, suit in enumerate((Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS)):
            for rank in Rank:
                c = Card(suit=suit, rank=rank, is_face_up=True, card_id=suit_idx * 13 + (rank - 1))
                game.foundations[suit_idx].push(c)

        self.assertTrue(game.is_won())
        self.assertEqual(game.get_legal_moves(), [])


if __name__ == "__main__":
    unittest.main()
