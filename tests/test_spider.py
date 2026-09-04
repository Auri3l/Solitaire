"""Comprehensive Unit and Invariant Test Suite for Spider Solitaire.

Target Module: solitaire.games.spider
Author: teamwork_preview_explorer_m2_3
"""

import unittest
import random
from typing import List, Dict, Any, Tuple, Optional

from solitaire.core.card import Color, Suit, Rank, Card
from solitaire.core.pile import PileType, Pile, Deck
from solitaire.core.commands import Command, CardMoveCommand, StockDealCommand, CommandHistory
from solitaire.core.base_game import BaseGame, GameStatus, Move, MoveResult
from solitaire.games.spider import SpiderGame, MoveType


class TestSpiderDeckAndDeal(unittest.TestCase):
    """TC-SP-001 through TC-SP-008: Deck generation and deal invariants."""

    def test_1_suit_deck_composition(self):
        """TC-SP-001: 1-suit deck has 104 cards, all Spades, exactly 8 sets of 13."""
        game = SpiderGame(num_suits=1, seed=42)
        deck_cards = Deck.create_spider_deck(num_suits=1)
        self.assertEqual(len(deck_cards), 104)
        self.assertTrue(all(c.suit == Suit.SPADES for c in deck_cards))
        for r in Rank:
            count = sum(1 for c in deck_cards if c.rank == r)
            self.assertEqual(count, 8, f"Rank {r} must appear exactly 8 times")

    def test_2_suit_deck_composition(self):
        """TC-SP-002: 2-suit deck has 52 Spades, 52 Hearts, exactly 4 sets each."""
        game = SpiderGame(num_suits=2, seed=42)
        deck_cards = Deck.create_spider_deck(num_suits=2)
        self.assertEqual(len(deck_cards), 104)
        spades = [c for c in deck_cards if c.suit == Suit.SPADES]
        hearts = [c for c in deck_cards if c.suit == Suit.HEARTS]
        self.assertEqual(len(spades), 52)
        self.assertEqual(len(hearts), 52)
        for r in Rank:
            self.assertEqual(sum(1 for c in spades if c.rank == r), 4)
            self.assertEqual(sum(1 for c in hearts if c.rank == r), 4)

    def test_4_suit_deck_composition(self):
        """TC-SP-003: 4-suit deck has 26 cards of each of the 4 suits (2 full decks)."""
        game = SpiderGame(num_suits=4, seed=42)
        deck_cards = Deck.create_spider_deck(num_suits=4)
        self.assertEqual(len(deck_cards), 104)
        for s in (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS):
            suit_cards = [c for c in deck_cards if c.suit == s]
            self.assertEqual(len(suit_cards), 26)
            for r in Rank:
                self.assertEqual(sum(1 for c in suit_cards if c.rank == r), 2)

    def test_initial_tableau_deal_distribution(self):
        """TC-SP-004: 10 columns: cols 0-3 have 6 cards, cols 4-9 have 5 cards = 54 total."""
        game = SpiderGame(num_suits=1, seed=42)
        self.assertEqual(len(game.tableau), 10)
        for i in range(4):
            self.assertEqual(len(game.tableau[i]), 6, f"Col {i} must have 6 cards")
        for i in range(4, 10):
            self.assertEqual(len(game.tableau[i]), 5, f"Col {i} must have 5 cards")
        total_tableau = sum(len(col) for col in game.tableau)
        self.assertEqual(total_tableau, 54)

    def test_initial_face_up_and_face_down_counts(self):
        """TC-SP-005: Exactly 44 face-down cards and 10 face-up cards (top card of each column)."""
        game = SpiderGame(num_suits=1, seed=42)
        face_down_count = sum(col.face_down_count for col in game.tableau)
        face_up_count = sum(col.face_up_count for col in game.tableau)
        self.assertEqual(face_down_count, 44)
        self.assertEqual(face_up_count, 10)
        for i, col in enumerate(game.tableau):
            self.assertTrue(col.peek().is_face_up, f"Top card of col {i} must be face-up")
            for card in col.cards[:-1]:
                self.assertFalse(card.is_face_up, f"Lower card in col {i} must be face-down")

    def test_initial_stock_deal_packs(self):
        """TC-SP-006: Stock contains remaining 50 cards face-down in 5 deals of 10."""
        game = SpiderGame(num_suits=1, seed=42)
        self.assertEqual(len(game.stock), 50)
        self.assertTrue(all(not c.is_face_up for c in game.stock))
        self.assertEqual(game.deals_remaining, 5)

    def test_unique_card_ids_across_all_104_cards(self):
        """TC-SP-007: All 104 cards in play have distinct IDs in range 0..103."""
        game = SpiderGame(num_suits=4, seed=42)
        all_cards = list(game.stock.cards)
        for col in game.tableau:
            all_cards.extend(list(col.cards))
        self.assertEqual(len(all_cards), 104)
        ids = [c.card_id for c in all_cards]
        self.assertEqual(len(set(ids)), 104)
        self.assertEqual(set(ids), set(range(104)))

    def test_restart_preserves_initial_permutation(self):
        """TC-SP-008: Restart resets the board to the identical initial deal."""
        game = SpiderGame(num_suits=1, seed=999)
        snap_initial = game.get_state_snapshot()

        # Perform legal deal from stock
        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertNotEqual(game.get_state_snapshot(), snap_initial)

        game.restart()
        self.assertEqual(game.get_state_snapshot(), snap_initial)


class TestSpiderStockDealing(unittest.TestCase):
    """TC-SP-010 through TC-SP-015: Stock dealing rules and empty column guards."""

    def test_stock_deal_empty_column_guard_strictly_blocks_deal(self):
        """TC-SP-010: Stock deal is rejected if ANY of the 10 columns is empty."""
        game = SpiderGame(num_suits=1, seed=42)
        # Empty column 0
        game.tableau[0].clear()
        self.assertTrue(game.tableau[0].is_empty)

        initial_stock_len = len(game.stock)
        res = game.deal_stock()
        self.assertFalse(res.success)
        self.assertIn("empty", res.error_message.lower())
        self.assertEqual(len(game.stock), initial_stock_len)
        self.assertEqual(game.deals_remaining, 5)

    def test_stock_deal_success_when_all_columns_populated(self):
        """TC-SP-011: When all 10 columns have >= 1 card, deal succeeds."""
        game = SpiderGame(num_suits=1, seed=42)
        self.assertTrue(all(len(col) > 0 for col in game.tableau))

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.stock), 40)
        self.assertEqual(game.deals_remaining, 4)

    def test_stock_deal_distributes_exactly_one_card_per_column(self):
        """TC-SP-012: Dealing delivers exactly 1 face-up card to each of cols 0..9."""
        game = SpiderGame(num_suits=1, seed=42)
        col_lens_before = [len(c) for c in game.tableau]

        game.deal_stock()
        for i in range(10):
            self.assertEqual(len(game.tableau[i]), col_lens_before[i] + 1)
            self.assertTrue(game.tableau[i].peek().is_face_up)

    def test_stock_deal_decrements_deals_remaining_and_stock_size(self):
        """TC-SP-013: Each deal decrements deals_remaining by 1 and stock size by 10."""
        game = SpiderGame(num_suits=1, seed=42)
        for expected_remaining in range(4, -1, -1):
            res = game.deal_stock()
            self.assertTrue(res.success)
            self.assertEqual(game.deals_remaining, expected_remaining)
            self.assertEqual(len(game.stock), expected_remaining * 10)

    def test_stock_deal_exhaustion_disallows_6th_deal(self):
        """TC-SP-014: Attempting to deal when stock is empty is rejected."""
        game = SpiderGame(num_suits=1, seed=42)
        for deal_i in range(5):
            res = game.deal_stock()
            self.assertTrue(res.success)

        self.assertEqual(len(game.stock), 0)
        self.assertEqual(game.deals_remaining, 0)

        # 6th attempt
        res6 = game.deal_stock()
        self.assertFalse(res6.success)
        self.assertIn("empty", res6.error_message.lower())

    def test_stock_deal_unconditional_rejection_with_informative_error(self):
        """TC-SP-015: When deal fails, returns informative error message."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        res = game.deal_stock()
        self.assertFalse(res.success)
        self.assertTrue(len(res.error_message) > 0)
        self.assertIn("empty", res.error_message.lower())


class TestSpiderTableauBuilding(unittest.TestCase):
    """TC-SP-020 through TC-SP-025: Permissive tableau placement rules."""

    def test_permissive_building_same_suit(self):
        """TC-SP-020: Moving 5♠ onto 6♠ is legal."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c6 = Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5)
        c5 = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        game.tableau[0].push(c6)
        game.tableau[1].push(c5)

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c5.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 2)
        self.assertEqual(game.tableau[0].peek(), c5)

    def test_permissive_building_different_suit(self):
        """TC-SP-021: Moving 5♥ onto 6♠ is legal."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c6_spades = Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5)
        c5_hearts = Card(Suit.HEARTS, Rank.FIVE, is_face_up=True, card_id=17)
        game.tableau[0].push(c6_spades)
        game.tableau[1].push(c5_hearts)

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c5_hearts.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 2)
        self.assertEqual(game.tableau[0].peek(), c5_hearts)

    def test_permissive_building_different_color(self):
        """TC-SP-022: Moving 5♦ onto 6♣ is legal."""
        game = SpiderGame(num_suits=4, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c6_clubs = Card(Suit.CLUBS, Rank.SIX, is_face_up=True, card_id=44)
        c5_diamonds = Card(Suit.DIAMONDS, Rank.FIVE, is_face_up=True, card_id=30)
        game.tableau[0].push(c6_clubs)
        game.tableau[1].push(c5_diamonds)

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c5_diamonds.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 2)

    def test_reject_wrong_rank_gap(self):
        """TC-SP-023: Moving 5♠ onto 7♠ is rejected (rank difference != 1)."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c7 = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)
        c5 = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        game.tableau[0].push(c7)
        game.tableau[1].push(c5)

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c5.card_id))
        self.assertFalse(res.success)

    def test_reject_ascending_rank(self):
        """TC-SP-024: Moving 6♠ onto 5♠ is rejected."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c5 = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        c6 = Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5)
        game.tableau[0].push(c5)
        game.tableau[1].push(c6)

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c6.card_id))
        self.assertFalse(res.success)

    def test_empty_column_accepts_any_single_card(self):
        """TC-SP-025: Any single card (Ace, 7, King, etc.) can move to an empty column."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c3 = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        game.tableau[1].push(c3)

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c3.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.tableau[0].peek(), c3)


class TestSpiderSequenceMoving(unittest.TestCase):
    """TC-SP-030 through TC-SP-037: Restrictive same-suit sequence moving."""

    def test_legal_move_same_suit_descending_stack(self):
        """TC-SP-030: Multi-card stack of same suit (4♠-3♠) moves legally onto 5♠."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c5 = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        c4 = Card(Suit.SPADES, Rank.FOUR, is_face_up=True, card_id=3)
        c3 = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)

        game.tableau[0].push(c5)
        game.tableau[1].push_many([c4, c3])

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_count=2, card_id=c4.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 3)
        self.assertEqual(game.tableau[0][-1], c3)
        self.assertTrue(game.tableau[1].is_empty)

    def test_legal_move_same_suit_stack_onto_different_suit_target(self):
        """TC-SP-031: Same-suit stack (4♠-3♠) can land on different-suit card (5♥)."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c5_hearts = Card(Suit.HEARTS, Rank.FIVE, is_face_up=True, card_id=17)
        c4_spades = Card(Suit.SPADES, Rank.FOUR, is_face_up=True, card_id=3)
        c3_spades = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)

        game.tableau[0].push(c5_hearts)
        game.tableau[1].push_many([c4_spades, c3_spades])

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_count=2, card_id=c4_spades.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 3)

    def test_STRICT_REJECTION_mixed_suit_stack(self):
        """TC-SP-032: Moving mixed-suit stack (4♥-3♠) onto 5♠ is STRICTLY REJECTED."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c5_spades = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        c4_hearts = Card(Suit.HEARTS, Rank.FOUR, is_face_up=True, card_id=16)
        c3_spades = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)

        game.tableau[0].push(c5_spades)
        game.tableau[1].push_many([c4_hearts, c3_spades])

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_count=2, card_id=c4_hearts.card_id))
        self.assertFalse(res.success)
        self.assertIn("suit", res.error_message.lower())
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertEqual(len(game.tableau[1]), 2)

    def test_STRICT_REJECTION_mixed_suit_stack_same_color(self):
        """TC-SP-033: Moving mixed-suit stack of same color (4♠-3♣) onto 5♠ is REJECTED."""
        game = SpiderGame(num_suits=4, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c5_spades = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        c4_spades = Card(Suit.SPADES, Rank.FOUR, is_face_up=True, card_id=3)
        c3_clubs = Card(Suit.CLUBS, Rank.THREE, is_face_up=True, card_id=41)

        game.tableau[0].push(c5_spades)
        game.tableau[1].push_many([c4_spades, c3_clubs])

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_count=2, card_id=c4_spades.card_id))
        self.assertFalse(res.success)

    def test_partial_column_pick_up_same_suit_bottom_subsequence(self):
        """TC-SP-034: Col has [7♠, 6♥, 5♥]. Dragging [6♥, 5♥] succeeds; dragging [7♠, 6♥, 5♥] fails."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Destination has 7♥
        game.tableau[0].push(Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19))

        c7_spades = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)
        c6_hearts = Card(Suit.HEARTS, Rank.SIX, is_face_up=True, card_id=18)
        c5_hearts = Card(Suit.HEARTS, Rank.FIVE, is_face_up=True, card_id=17)
        game.tableau[1].push_many([c7_spades, c6_hearts, c5_hearts])

        # Drag 3 cards -> fails because 7♠ != 6♥ suit
        res_fail = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_count=3, card_id=c7_spades.card_id))
        self.assertFalse(res_fail.success)

        # Drag 2 cards [6♥, 5♥] -> succeeds!
        res_ok = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_count=2, card_id=c6_hearts.card_id))
        self.assertTrue(res_ok.success)
        self.assertEqual(len(game.tableau[0]), 3)
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.tableau[1].peek(), c7_spades)

    def test_reject_drag_starting_at_suit_break_index(self):
        """TC-SP-035: Dragging stack starting above a suit break is rejected."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        game.tableau[0].push(Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7))

        c7 = Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19)
        c6 = Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5)
        c5 = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        game.tableau[1].push_many([c7, c6, c5])

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_count=3, card_id=c7.card_id))
        self.assertFalse(res.success)

    def test_legal_move_same_suit_stack_to_empty_column(self):
        """TC-SP-036: Same-suit descending stack can move to an empty column."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        c4 = Card(Suit.SPADES, Rank.FOUR, is_face_up=True, card_id=3)
        c3 = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        game.tableau[1].push_many([c4, c3])

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_count=2, card_id=c4.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 2)

    def test_stack_departure_auto_flips_new_top_card(self):
        """TC-SP-037: Moving stack exposes face-down card, which auto-flips face-up."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c_down = Card(Suit.SPADES, Rank.KING, is_face_up=False, card_id=12)
        c_up4 = Card(Suit.SPADES, Rank.FOUR, is_face_up=True, card_id=3)
        c_up3 = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        game.tableau[1].push_many([c_down, c_up4, c_up3])

        game.tableau[0].push(Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4))

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_count=2, card_id=c_up4.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertTrue(c_down.is_face_up, "Newly exposed card must auto-flip face-up")


class TestSpiderFoundationClearing(unittest.TestCase):
    """TC-SP-040 through TC-SP-045: 13-card King-to-Ace atomic run clearing."""

    def test_13_card_same_suit_run_atomic_clearing_to_foundation(self):
        """TC-SP-040: Assembling full 13-card K-to-A run of same suit clears immediately to foundation (+100 pts)."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Col 0 has K through 2 of Spades (12 cards)
        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))

        # Col 1 has Ace of Spades
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(c_ace)

        score_before = game.score
        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c_ace.card_id))
        self.assertTrue(res.success)

        # Invariant: Run is atomically removed from tableau_0
        self.assertTrue(game.tableau[0].is_empty, "Column 0 should be empty after run clears")
        self.assertEqual(game.completed_runs, 1)
        self.assertEqual(len(game.foundations[0]), 13)
        # Score increases by +100 (-1 for move, +100 for run = net +99)
        self.assertEqual(game.score, score_before - 1 + 100)

    def test_STRICT_NEGATIVE_mixed_suit_13_card_sequence_NOT_cleared(self):
        """TC-SP-041: 13-card K-to-A sequence with mixed suits is NOT cleared."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Col 0 has K through 2 of Spades
        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))

        # Col 1 has Ace of Hearts!
        c_ace_hearts = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.tableau[1].push(c_ace_hearts)

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c_ace_hearts.card_id))
        self.assertTrue(res.success)

        # Invariant: The 13 cards remain on tableau_0, NOT cleared!
        self.assertEqual(len(game.tableau[0]), 13)
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)

    def test_run_clearing_awards_plus_100_points(self):
        """TC-SP-042: Clearing a 13-card run adds 100 points."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(c_ace)
        score_before = game.score
        game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c_ace.card_id))
        self.assertEqual(game.score, score_before - 1 + 100)

    def test_run_clearing_auto_flips_underlying_face_down_card(self):
        """TC-SP-043: If column had cards under the 13-card run, the exposed card flips face-up."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c_down = Card(Suit.SPADES, Rank.FIVE, is_face_up=False, card_id=100)
        game.tableau[0].push(c_down)

        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))

        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(c_ace)

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c_ace.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertTrue(c_down.is_face_up, "Exposed card under cleared run must be flipped face-up")

    def test_stock_deal_completing_run_triggers_immediate_clearing(self):
        """TC-SP-044: Dealing from stock that delivers the 13th card clears the run."""
        game = SpiderGame(num_suits=1, seed=42)
        for col in game.tableau:
            if col.is_empty:
                col.push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=99))
        game.tableau[0].clear()
        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))

        stock_cards = list(game.stock.cards)
        stock_cards[-1] = Card(Suit.SPADES, Rank.ACE, is_face_up=False, card_id=0)
        game.stock.clear()
        game.stock.push_many(stock_cards)

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(game.completed_runs, 1)
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertTrue(game.tableau[0].is_empty)

    def test_multiple_simultaneous_run_clearings(self):
        """TC-SP-045: Dealing from stock completing runs in two columns clears both."""
        game = SpiderGame(num_suits=1, seed=42)
        for col in game.tableau:
            if col.is_empty:
                col.push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=99))
        game.tableau[0].clear()
        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))
        game.tableau[1].clear()
        for r in range(13, 1, -1):
            game.tableau[1].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=13 + r - 1))

        stock_cards = list(game.stock.cards)
        stock_cards[-1] = Card(Suit.SPADES, Rank.ACE, is_face_up=False, card_id=0)
        stock_cards[-2] = Card(Suit.SPADES, Rank.ACE, is_face_up=False, card_id=13)
        game.stock.clear()
        game.stock.push_many(stock_cards)

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(game.completed_runs, 2)
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertEqual(len(game.foundations[1]), 13)


class TestSpiderScoring(unittest.TestCase):
    """TC-SP-050 through TC-SP-053: Score arithmetic and zero-drift invariants."""

    def test_initial_score_500(self):
        """TC-SP-050: Initial score is 500."""
        game = SpiderGame(num_suits=1, seed=42)
        self.assertEqual(game.score, 500)
        self.assertEqual(game.moves_count, 0)

    def test_tableau_move_decrements_score_by_1(self):
        """TC-SP-051: Legal tableau move costs 1 point."""
        game = SpiderGame(num_suits=1, seed=42)
        legal = game.get_legal_moves()
        res = game.make_move(legal[0])
        self.assertTrue(res.success)
        self.assertEqual(game.score, 499)
        self.assertEqual(game.moves_count, 1)

    def test_stock_deal_decrements_score_by_1(self):
        """TC-SP-052: Stock deal costs 1 point."""
        game = SpiderGame(num_suits=1, seed=42)
        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(game.score, 499)
        self.assertEqual(game.moves_count, 1)

    def test_scoring_invariant_formula(self):
        """TC-SP-053: Invariant Score = 500 - moves_count + 100 * completed_runs."""
        game = SpiderGame(num_suits=1, seed=42)
        expected = 500 - game.moves_count + 100 * game.completed_runs
        self.assertEqual(game.score, expected)


class TestSpiderUndoRedoInvariance(unittest.TestCase):
    """TC-SP-060 through TC-SP-065: Exact reversible rollback across runs, deals, and fog-of-war."""

    def test_undo_redo_restores_cleared_13_card_run_to_tableau(self):
        """TC-SP-060: Undoing a run clearance restores 13 cards from foundation back to tableau."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(c_ace)

        initial_snap = game.get_state_snapshot()

        # Complete run
        game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c_ace.card_id))
        self.assertEqual(game.completed_runs, 1)
        self.assertTrue(game.tableau[0].is_empty)

        # Undo
        self.assertTrue(game.undo())
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(game.get_state_snapshot(), initial_snap)

        # Redo
        self.assertTrue(game.redo())
        self.assertEqual(game.completed_runs, 1)
        self.assertTrue(game.tableau[0].is_empty)

    def test_undo_run_clear_re_hides_auto_flipped_underlying_card(self):
        """TC-SP-061: FOG-OF-WAR: Undoing a run clearance strictly re-hides the exposed card."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c_down = Card(Suit.SPADES, Rank.FIVE, is_face_up=False, card_id=100)
        game.tableau[0].push(c_down)
        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(c_ace)

        # Run clears, c_down auto-flips
        game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c_ace.card_id))
        self.assertTrue(c_down.is_face_up)

        # Undo strictly re-hides c_down
        self.assertTrue(game.undo())
        self.assertFalse(c_down.is_face_up, "Underlying card must be re-hidden to face-down on undo")

    def test_undo_stock_deal_restores_10_cards_face_down_to_stock(self):
        """TC-SP-062: Undoing stock deal removes 10 dealt cards and restores them to stock face-down."""
        game = SpiderGame(num_suits=1, seed=42)
        initial_snap = game.get_state_snapshot()

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.stock), 40)

        self.assertTrue(game.undo())
        self.assertEqual(len(game.stock), 50)
        self.assertEqual(game.deals_remaining, 5)
        self.assertEqual(game.get_state_snapshot(), initial_snap)

    def test_undo_stock_deal_that_triggered_run_clearing(self):
        """TC-SP-063: Undoing a stock deal that triggered a run clearance restores run to tableau and cards to stock."""
        game = SpiderGame(num_suits=1, seed=42)
        for col in game.tableau:
            if col.is_empty:
                col.push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=99))
        game.tableau[0].clear()
        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))
        stock_cards = list(game.stock.cards)
        stock_cards[-1] = Card(Suit.SPADES, Rank.ACE, is_face_up=False, card_id=0)
        game.stock.clear()
        game.stock.push_many(stock_cards)

        initial_snap = game.get_state_snapshot()

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(game.completed_runs, 1)

        self.assertTrue(game.undo())
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(len(game.stock), 50)
        self.assertEqual(game.get_state_snapshot(), initial_snap)

    def test_undo_redo_single_tableau_move_with_auto_flip(self):
        """TC-SP-064: Move uncovering face-down card properly re-hides on undo and flips on redo."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        c_down = Card(Suit.SPADES, Rank.KING, is_face_up=False, card_id=100)
        c_up = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        game.tableau[1].push_many([c_down, c_up])
        game.tableau[0].push(Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5))

        initial_snap = game.get_state_snapshot()

        res = game.make_move(Move(source_pile_id="tableau_1", dest_pile_id="tableau_0", card_id=c_up.card_id))
        self.assertTrue(res.success)
        self.assertTrue(c_down.is_face_up)
        snap_after = game.get_state_snapshot()

        self.assertTrue(game.undo())
        self.assertFalse(c_down.is_face_up)
        self.assertEqual(game.get_state_snapshot(), initial_snap)

        self.assertTrue(game.redo())
        self.assertTrue(c_down.is_face_up)
        self.assertEqual(game.get_state_snapshot(), snap_after)

    def test_random_walk_100_step_undo_invariance_1_2_4_suits(self):
        """TC-SP-065: 100 random moves + 100 undos produces identical state across all suit variants."""
        for num_suits in (1, 2, 4):
            game = SpiderGame(num_suits=num_suits, seed=100 + num_suits)
            initial_snap = game.get_state_snapshot()
            rng = random.Random(100 + num_suits)

            steps_taken = 0
            for _ in range(100):
                legal = game.get_legal_moves()
                if not legal:
                    break
                move = rng.choice(legal)
                res = game.make_move(move)
                if res.success:
                    steps_taken += 1

            for _ in range(steps_taken):
                self.assertTrue(game.undo())

            self.assertFalse(game.can_undo())
            self.assertEqual(game.moves_count, 0)
            self.assertEqual(game.score, 500)
            self.assertEqual(game.get_state_snapshot(), initial_snap)


class TestSpiderWinCondition(unittest.TestCase):
    """TC-SP-070 through TC-SP-072: Victory detection."""

    def test_win_condition_all_8_runs_cleared(self):
        """TC-SP-070: Win condition met when all 8 runs (104 cards) are in foundations."""
        game = SpiderGame(num_suits=1, seed=42)
        game.completed_runs = 8
        game.stock.clear()
        for col in game.tableau:
            col.clear()

        self.assertTrue(game.is_won())
        self.assertEqual(game.game_status, GameStatus.WON)

    def test_game_not_won_when_7_runs_cleared(self):
        """TC-SP-071: 7 runs cleared is not won."""
        game = SpiderGame(num_suits=1, seed=42)
        game.completed_runs = 7
        self.assertFalse(game.is_won())
        self.assertEqual(game.game_status, GameStatus.IN_PROGRESS)

    def test_legal_moves_empty_when_won(self):
        """TC-SP-072: get_legal_moves() returns empty list when game is won."""
        game = SpiderGame(num_suits=1, seed=42)
        game.completed_runs = 8
        self.assertTrue(game.is_won())
        self.assertEqual(game.get_legal_moves(), [])


if __name__ == "__main__":
    unittest.main()
