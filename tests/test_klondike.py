"""Unit tests for solitaire.games.klondike.

Covers Turn 1 & 3 dealing, stock recycling, tableau alternating build rules,
King-to-empty rules, foundation building and demotion, auto-flip fog-of-war tracking,
scoring drift invariance, and the 50-step random walk undo invariance test.
"""

import unittest
import random

from solitaire.core.card import Color, Suit, Rank, Card
from solitaire.core.pile import PileType, Pile, Deck
from solitaire.core.commands import (
    CardMoveCommand,
    StockDealCommand,
    RecycleCommand,
)
from solitaire.core.base_game import Move, MoveResult, GameStatus
from solitaire.games.klondike import KlondikeGame, MoveType, ScoringMode


class TestKlondikeInitialLayout(unittest.TestCase):
    """TC-KLON-001 through TC-KLON-003: Initial deal card distribution."""

    def test_initial_deal_card_counts(self):
        game = KlondikeGame(seed=42)
        self.assertEqual(len(game.stock), 24)
        self.assertEqual(len(game.waste), 0)
        self.assertEqual(sum(len(f) for f in game.foundations), 0)

        for i in range(7):
            self.assertEqual(len(game.tableau[i]), i + 1)

        total_cards = (
            len(game.stock) +
            len(game.waste) +
            sum(len(f) for f in game.foundations) +
            sum(len(t) for t in game.tableau)
        )
        self.assertEqual(total_cards, 52)

        # 52 unique card IDs
        all_cards = list(game.stock) + list(game.waste)
        for f in game.foundations:
            all_cards.extend(list(f))
        for t in game.tableau:
            all_cards.extend(list(t))
        self.assertEqual(len(set(c.card_id for c in all_cards)), 52)

    def test_initial_tableau_face_up_invariants(self):
        game = KlondikeGame(seed=42)
        total_face_down = 0
        total_face_up = 0

        for col_idx in range(7):
            col = game.tableau[col_idx]
            for card_idx in range(col_idx):
                self.assertFalse(col[card_idx].is_face_up, f"Col {col_idx} card {card_idx} should be face-down")
                total_face_down += 1
            self.assertTrue(col[col_idx].is_face_up, f"Col {col_idx} top card should be face-up")
            total_face_up += 1

        self.assertEqual(total_face_down, 21)
        self.assertEqual(total_face_up, 7)

    def test_initial_stock_and_waste_invariants(self):
        game = KlondikeGame(seed=42)
        self.assertTrue(all(not c.is_face_up for c in game.stock))
        self.assertTrue(game.waste.is_empty)

    def test_initial_foundations_empty(self):
        game = KlondikeGame(seed=42)
        self.assertEqual(len(game.foundations), 4)
        self.assertTrue(all(f.is_empty for f in game.foundations))

    def test_deterministic_seeded_deal(self):
        g1 = KlondikeGame(seed=123)
        g2 = KlondikeGame(seed=123)
        g3 = KlondikeGame(seed=456)

        snap1 = g1.get_state_snapshot()
        snap2 = g2.get_state_snapshot()
        snap3 = g3.get_state_snapshot()

        self.assertEqual(snap1, snap2)
        self.assertNotEqual(snap1["piles"], snap3["piles"])


class TestKlondikeTurn1Stock(unittest.TestCase):
    """TC-KLON-004 through TC-KLON-008: Turn 1 stock deal and recycling."""

    def test_turn1_single_deal_to_waste(self):
        game = KlondikeGame(turn_mode=1, seed=10)
        top_stock = game.stock[-1]

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.stock), 23)
        self.assertEqual(len(game.waste), 1)
        self.assertEqual(game.waste.peek(), top_stock)
        self.assertTrue(game.waste.peek().is_face_up)
        self.assertEqual(game.moves_count, 1)

    def test_turn1_cycle_through_full_stock(self):
        game = KlondikeGame(turn_mode=1, seed=10)
        for i in range(24):
            res = game.deal_stock()
            self.assertTrue(res.success)

        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 24)
        self.assertTrue(all(c.is_face_up for c in game.waste))

    def test_turn1_recycle_waste_to_stock(self):
        game = KlondikeGame(turn_mode=1, seed=10)
        # Capture deal order
        stock_cards = list(game.stock.cards)  # bottom to top
        first_dealt = stock_cards[-1]

        for _ in range(24):
            game.deal_stock()

        # Stock is empty, clicking deals/recycles
        recycle_res = game.deal_stock()
        self.assertTrue(recycle_res.success)
        self.assertEqual(len(game.stock), 24)
        self.assertEqual(len(game.waste), 0)
        self.assertTrue(all(not c.is_face_up for c in game.stock))
        self.assertEqual(game.recycles_count, 1)

        # The next card dealt in pass 2 must be the same first card dealt in pass 1
        res2 = game.deal_stock()
        self.assertTrue(res2.success)
        self.assertEqual(game.waste.peek(), first_dealt)

    def test_turn1_deal_empty_stock_and_waste_noop(self):
        game = KlondikeGame(turn_mode=1, seed=10)
        game.stock.clear()
        game.waste.clear()

        res = game.deal_stock()
        self.assertFalse(res.success)
        self.assertEqual(game.moves_count, 0)

    def test_turn1_undo_deal_and_recycle(self):
        game = KlondikeGame(turn_mode=1, seed=10)
        initial_snap = game.get_state_snapshot()

        game.deal_stock()
        self.assertEqual(len(game.stock), 23)
        self.assertEqual(len(game.waste), 1)

        self.assertTrue(game.undo())
        self.assertEqual(len(game.stock), 24)
        self.assertEqual(len(game.waste), 0)
        self.assertFalse(game.stock[-1].is_face_up)
        self.assertEqual(game.get_state_snapshot(), initial_snap)

        # Exhaust and recycle, then undo recycle
        for _ in range(24):
            game.deal_stock()

        game.deal_stock()  # Recycle
        self.assertEqual(len(game.stock), 24)
        self.assertEqual(len(game.waste), 0)

        self.assertTrue(game.undo())
        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 24)
        self.assertTrue(all(c.is_face_up for c in game.waste))


class TestKlondikeTurn3Stock(unittest.TestCase):
    """TC-KLON-009 through TC-KLON-013: Turn 3 stock dealing and remainders."""

    def test_turn3_three_card_batches(self):
        game = KlondikeGame(turn_mode=3, seed=20)
        top3_stock = list(game.stock.cards[-3:])

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.stock), 21)
        self.assertEqual(len(game.waste), 3)
        # Top of waste is the last card popped from stock (top3_stock[-3])
        self.assertEqual(game.waste[-1], top3_stock[-3])
        self.assertTrue(all(c.is_face_up for c in game.waste))

    def test_turn3_remainder_batch_size_2(self):
        game = KlondikeGame(turn_mode=3, seed=20)
        game.stock.remove_from(2)
        self.assertEqual(len(game.stock), 2)
        top2 = list(game.stock.cards)

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 2)
        self.assertEqual(game.waste[-1], top2[0])

    def test_turn3_remainder_batch_size_1(self):
        game = KlondikeGame(turn_mode=3, seed=20)
        game.stock.remove_from(1)
        self.assertEqual(len(game.stock), 1)
        top1 = list(game.stock.cards)

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 1)
        self.assertEqual(game.waste[-1], top1[0])

    def test_turn3_order_preservation_across_recycles(self):
        game = KlondikeGame(turn_mode=3, seed=20)
        # 8 deals of 3 = 24 cards
        first_pass_waste = []
        for _ in range(8):
            game.deal_stock()
            first_pass_waste.append(game.waste[-1].card_id)

        # Recycle
        game.deal_stock()
        self.assertEqual(len(game.stock), 24)
        self.assertEqual(len(game.waste), 0)

        # Deal pass 2
        second_pass_waste = []
        for _ in range(8):
            game.deal_stock()
            second_pass_waste.append(game.waste[-1].card_id)

        self.assertEqual(first_pass_waste, second_pass_waste)

    def test_turn3_undo_remainder_deals(self):
        game = KlondikeGame(turn_mode=3, seed=20)
        game.stock.remove_from(2)
        initial_snap = game.get_state_snapshot()

        game.deal_stock()
        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 2)

        self.assertTrue(game.undo())
        self.assertEqual(game.get_state_snapshot(), initial_snap)


class TestKlondikeTableauRules(unittest.TestCase):
    """TC-KLON-014 through TC-KLON-017: Tableau alternating color and descending build rules."""

    def test_tableau_legal_alternating_descending_moves(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c_black_8 = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)
        c_red_7 = Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19)

        game.tableau[0].push(c_black_8)
        game.tableau[1].push(c_red_7)

        # Move 7♥ onto 8♠
        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 2)
        self.assertEqual(game.tableau[0][-1], c_red_7)
        self.assertTrue(game.tableau[1].is_empty)

    def test_tableau_reject_same_color(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c_red_8 = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        c_red_7 = Card(Suit.DIAMONDS, Rank.SEVEN, is_face_up=True, card_id=32)

        game.tableau[0].push(c_red_8)
        game.tableau[1].push(c_red_7)

        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertFalse(res.success)
        self.assertIn("alternat", res.error_message.lower())
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertEqual(len(game.tableau[1]), 1)

    def test_tableau_reject_non_descending_rank(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c_black_8 = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)
        c_red_6 = Card(Suit.HEARTS, Rank.SIX, is_face_up=True, card_id=18)

        game.tableau[0].push(c_black_8)
        game.tableau[1].push(c_red_6)

        # Gap of 2
        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertFalse(res.success)
        self.assertIn("descending", res.error_message.lower())

        # Ascending: attempt 8♠ onto 6♥
        move_asc = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_1", card_count=1)
        res_asc = game.make_move(move_asc)
        self.assertFalse(res_asc.success)

    def test_tableau_reject_face_down_source_or_dest(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c_down = Card(Suit.SPADES, Rank.EIGHT, is_face_up=False, card_id=7)
        c_up = Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19)

        game.tableau[0].push(c_down)
        game.tableau[1].push(c_up)

        # Cannot place onto face-down card
        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertFalse(res.success)

        # Cannot move face-down card
        move_down = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_1", card_count=1)
        res_down = game.make_move(move_down)
        self.assertFalse(res_down.success)

    def test_tableau_partial_subsequence_move(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c_base = Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9)
        game.tableau[0].push(c_base)

        seq = [
            Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21),
            Card(Suit.CLUBS, Rank.EIGHT, is_face_up=True, card_id=46),
            Card(Suit.DIAMONDS, Rank.SEVEN, is_face_up=True, card_id=32)
        ]
        game.tableau[1].push_many(seq)

        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_0", card_count=3)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 4)
        self.assertEqual(game.tableau[0].cards, (c_base, seq[0], seq[1], seq[2]))
        self.assertTrue(game.tableau[1].is_empty)


class TestKlondikeKingToEmpty(unittest.TestCase):
    """TC-KLON-018 through TC-KLON-020: King-to-empty tableau rules."""

    def test_king_to_empty_column_succeeds(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        king = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        game.tableau[1].push(king)

        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertEqual(game.tableau[0].peek(), king)

    def test_king_sequence_to_empty_column_succeeds(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        king_seq = [
            Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12),
            Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24),
            Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        ]
        game.tableau[1].push_many(king_seq)

        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_0", card_count=3)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 3)
        self.assertEqual(game.tableau[0].cards, tuple(king_seq))

    def test_queen_to_empty_column_rejected(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        queen = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        game.tableau[1].push(queen)

        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertFalse(res.success)
        self.assertIn("king", res.error_message.lower())
        self.assertTrue(game.tableau[0].is_empty)

    def test_jack_to_empty_column_rejected(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        jack = Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        game.tableau[1].push(jack)

        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertFalse(res.success)

    def test_ace_to_empty_column_rejected(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(ace)

        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertFalse(res.success)


class TestKlondikeFoundationRules(unittest.TestCase):
    """TC-KLON-024 through TC-KLON-028: Foundation stacking and demotion."""

    def test_ace_on_empty_foundation_succeeds(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()

        ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[0].push(ace)

        move = Move(MoveType.TABLEAU_TO_FOUNDATION, "tableau_0", "foundation_0", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertEqual(len(game.foundations[0]), 1)
        self.assertEqual(game.foundations[0].peek(), ace)

    def test_non_ace_on_empty_foundation_rejected(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()

        two = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.tableau[0].push(two)

        move = Move(MoveType.TABLEAU_TO_FOUNDATION, "tableau_0", "foundation_0", card_count=1)
        res = game.make_move(move)
        self.assertFalse(res.success)
        self.assertTrue(game.foundations[0].is_empty)

    def test_sequential_same_suit_build_succeeds(self):
        game = KlondikeGame(seed=42)
        ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        two = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.foundations[0].push(ace)

        game.tableau[0].clear()
        game.tableau[0].push(two)

        move = Move(MoveType.TABLEAU_TO_FOUNDATION, "tableau_0", "foundation_0", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertEqual(len(game.foundations[0]), 2)
        self.assertEqual(game.foundations[0].peek(), two)

    def test_wrong_suit_foundation_rejected(self):
        game = KlondikeGame(seed=42)
        ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        two_hearts = Card(Suit.HEARTS, Rank.TWO, is_face_up=True, card_id=14)
        game.foundations[0].push(ace_spades)

        game.tableau[0].clear()
        game.tableau[0].push(two_hearts)

        move = Move(MoveType.TABLEAU_TO_FOUNDATION, "tableau_0", "foundation_0", card_count=1)
        res = game.make_move(move)
        self.assertFalse(res.success)
        self.assertEqual(len(game.foundations[0]), 1)

    def test_wrong_rank_foundation_rejected(self):
        game = KlondikeGame(seed=42)
        ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        three_spades = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        game.foundations[0].push(ace_spades)

        game.tableau[0].clear()
        game.tableau[0].push(three_spades)

        move = Move(MoveType.TABLEAU_TO_FOUNDATION, "tableau_0", "foundation_0", card_count=1)
        res = game.make_move(move)
        self.assertFalse(res.success)

    def test_multi_card_foundation_rejected(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        c1 = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        c2 = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.tableau[0].push_many([c1, c2])

        move = Move(MoveType.TABLEAU_TO_FOUNDATION, "tableau_0", "foundation_0", card_count=2)
        res = game.make_move(move)
        self.assertFalse(res.success)
        self.assertIn("one card", res.error_message.lower())

    def test_foundation_to_tableau_demotion(self):
        game = KlondikeGame(seed=42)
        c_ace = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        c_two = Card(Suit.HEARTS, Rank.TWO, is_face_up=True, card_id=14)
        game.foundations[0].push_many([c_ace, c_two])

        game.tableau[0].clear()
        c_three_spades = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        game.tableau[0].push(c_three_spades)

        game.score = 20
        move = Move(MoveType.FOUNDATION_TO_TABLEAU, "foundation_0", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertEqual(len(game.foundations[0]), 1)
        self.assertEqual(game.tableau[0].peek(), c_two)
        self.assertEqual(game.score, 5)  # -15 penalty

        # Undo restores foundation card and score
        self.assertTrue(game.undo())
        self.assertEqual(len(game.foundations[0]), 2)
        self.assertEqual(game.score, 20)

    def test_foundation_demote_to_empty_tableau_king_only(self):
        game = KlondikeGame(seed=42)
        c_ace = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.foundations[0].push(c_ace)
        game.tableau[0].clear()

        move = Move(MoveType.FOUNDATION_TO_TABLEAU, "foundation_0", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertFalse(res.success)


class TestKlondikeAutoFlipAndFogOfWar(unittest.TestCase):
    """TC-KLON-029 through TC-KLON-033: Auto-flipping exposed cards and fog-of-war restoration."""

    def test_auto_flip_when_top_card_moved(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c_down = Card(Suit.SPADES, Rank.TEN, is_face_up=False, card_id=9)
        c_top = Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21)
        game.tableau[0].push_many([c_down, c_top])

        c_target = Card(Suit.CLUBS, Rank.TEN, is_face_up=True, card_id=48)
        game.tableau[1].push(c_target)

        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_1", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)

        # c_down must be auto-flipped to face-up
        self.assertTrue(c_down.is_face_up)
        # Score increases by +5 for auto-flip
        self.assertEqual(game.score, 5)

        # Undo must re-hide c_down
        self.assertTrue(game.undo())
        self.assertFalse(c_down.is_face_up)
        self.assertEqual(game.score, 0)

        # Redo must re-flip c_down to face-up
        self.assertTrue(game.redo())
        self.assertTrue(c_down.is_face_up)
        self.assertEqual(game.score, 5)

    def test_no_flip_when_underlying_card_already_face_up(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c1 = Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9)
        c2 = Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21)
        game.tableau[0].push_many([c1, c2])

        c_target = Card(Suit.CLUBS, Rank.TEN, is_face_up=True, card_id=48)
        game.tableau[1].push(c_target)

        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_1", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertTrue(c1.is_face_up)
        self.assertEqual(game.score, 0)  # No flip score

    def test_no_flip_when_column_emptied(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c_top = Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21)
        game.tableau[0].push(c_top)

        c_target = Card(Suit.CLUBS, Rank.TEN, is_face_up=True, card_id=48)
        game.tableau[1].push(c_target)

        move = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_1", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertTrue(game.tableau[0].is_empty)
        self.assertEqual(game.score, 0)


class TestKlondikeScoringAndDrift(unittest.TestCase):
    """TC-KLON-034 through TC-KLON-035: Scoring deltas and zero drift on rollback."""

    def test_score_waste_to_tableau(self):
        game = KlondikeGame(seed=42)
        game.waste.clear()
        game.tableau[0].clear()

        c_t = Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5)
        c_w = Card(Suit.HEARTS, Rank.FIVE, is_face_up=True, card_id=17)
        game.tableau[0].push(c_t)
        game.waste.push(c_w)

        move = Move(MoveType.WASTE_TO_TABLEAU, "waste", "tableau_0", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertEqual(game.score, 5)

        game.undo()
        self.assertEqual(game.score, 0)

    def test_score_waste_to_foundation(self):
        game = KlondikeGame(seed=42)
        game.waste.clear()
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.waste.push(c_ace)

        move = Move(MoveType.WASTE_TO_FOUNDATION, "waste", "foundation_0", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertEqual(game.score, 10)

        game.undo()
        self.assertEqual(game.score, 0)

    def test_score_tableau_to_foundation(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[0].push(c_ace)

        move = Move(MoveType.TABLEAU_TO_FOUNDATION, "tableau_0", "foundation_0", card_count=1)
        res = game.make_move(move)
        self.assertTrue(res.success)
        self.assertEqual(game.score, 10)

        game.undo()
        self.assertEqual(game.score, 0)


class TestKlondikeRandomWalkUndoInvariance(unittest.TestCase):
    """TC-KLON-036 through TC-KLON-038: 50-step random walk and win condition."""

    def test_50_step_random_walk_with_exact_undo_invariance(self):
        """Invariant: Apply(Delta^-1, Apply(Delta, S)) == S."""
        game = KlondikeGame(turn_mode=1, seed=999)
        initial_snap = game.get_state_snapshot()

        rng = random.Random(42)
        executed_moves = 0

        for step in range(50):
            legal_moves = game.get_legal_moves()
            if not legal_moves:
                break

            chosen_move = rng.choice(legal_moves)
            res = game.make_move(chosen_move)
            self.assertTrue(res.success, f"Move {chosen_move} failed at step {step}")
            executed_moves += 1

        self.assertGreater(executed_moves, 0)
        self.assertEqual(game.moves_count, executed_moves)

        # Roll back all executed moves
        for step in range(executed_moves):
            self.assertTrue(game.can_undo(), f"can_undo returned False at rollback step {step}")
            undo_res = game.undo()
            self.assertTrue(undo_res, f"Undo failed at rollback step {step}")

        self.assertFalse(game.can_undo())
        self.assertEqual(game.moves_count, 0)
        self.assertEqual(game.score, 0)

        final_snap = game.get_state_snapshot()
        self.assertEqual(final_snap, initial_snap)

    def test_interleaved_undo_redo_consistency(self):
        game = KlondikeGame(turn_mode=1, seed=888)
        initial_snap = game.get_state_snapshot()

        # Step 1: deal
        game.deal_stock()
        snap_after_1 = game.get_state_snapshot()

        # Step 2: deal
        game.deal_stock()

        # Undo 1 step
        game.undo()
        self.assertEqual(game.get_state_snapshot(), snap_after_1)

        # Redo 1 step
        game.redo()
        self.assertEqual(game.moves_count, 2)

        # Full rollback
        game.undo()
        game.undo()
        self.assertEqual(game.get_state_snapshot(), initial_snap)

    def test_win_condition_detection(self):
        game = KlondikeGame(seed=42)
        self.assertFalse(game.is_won())

        # Populate all 4 foundations with 13 cards each (Ace to King)
        deck = Deck.create_standard()
        for f_idx, suit in enumerate(Suit):
            game.foundations[f_idx].clear()
            suit_cards = [c for c in deck if c.suit == suit]
            suit_cards.sort(key=lambda c: c.rank.value)
            for c in suit_cards:
                c.is_face_up = True
                game.foundations[f_idx].push(c)

        self.assertTrue(game.is_won())

    def test_auto_complete_solver(self):
        game = KlondikeGame(seed=42)
        # Clear stock and waste
        game.stock.clear()
        game.waste.clear()

        for i in range(7):
            game.tableau[i].clear()

        # Place Aces on foundations and 2s on tableau
        ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.foundations[0].push(ace_spades)

        two_spades = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.tableau[0].push(two_spades)

        self.assertTrue(game.can_auto_finish())
        res = game.auto_finish_step()
        self.assertIsNotNone(res)
        self.assertTrue(res.success)
        self.assertEqual(game.foundations[0].peek(), two_spades)

    def test_restart(self):
        game = KlondikeGame(seed=777)
        initial_snap = game.get_state_snapshot()

        game.deal_stock()
        game.deal_stock()
        self.assertNotEqual(game.get_state_snapshot(), initial_snap)

        game.restart()
        self.assertEqual(game.get_state_snapshot(), initial_snap)

    def test_hint_engine(self):
        game = KlondikeGame(seed=42)
        hint = game.get_hint()
        self.assertIsNotNone(hint)
        self.assertTrue(game.is_legal_move(hint))

    def test_find_best_move_for_card(self):
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[0].push(ace)

        best_move = game.find_best_move_for_card("tableau_0", -1)
        self.assertIsNotNone(best_move)
        self.assertEqual(best_move.dest_pile_id, "foundation_0")

    def test_vegas_scoring_mode(self):
        game = KlondikeGame(scoring_mode=ScoringMode.VEGAS, seed=42)
        self.assertEqual(game.score, -52)

        # Move ace to foundation awards +$5
        game.tableau[0].clear()
        ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[0].push(ace)

        res = game.make_move(Move(MoveType.TABLEAU_TO_FOUNDATION, "tableau_0", "foundation_0", card_count=1))
        self.assertTrue(res.success)
        self.assertEqual(game.score, -47)


if __name__ == "__main__":
    unittest.main()
