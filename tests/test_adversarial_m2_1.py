"""Empirical Adversarial Test Suite for Milestone 2: FreeCell and Spider Engines.

Author: teamwork_preview_challenger_m2_1
Target Modules:
  - solitaire.games.freecell
  - solitaire.games.spider

Probes exact boundary conditions:
1. FreeCell Supermove limits: exact acceptance at M, strict rejection at M+1 for occupied and empty targets.
2. FreeCell empty cascades interaction: K=1 empty cascade capacity M' = 1 + N.
3. Spider deal guards: exactly 1 empty column out of 10 strictly rejects stock deal; stock count unchanged.
4. Spider 13-card sequence clearing: K-to-A runs with mixed suits (first, middle, last card) strictly NOT cleared.
5. Spider atomic clearing undo: full rollback of foundation, card order, score delta, and fog-of-war auto-flipped cards.
6. Secondary command reversibility: exposed runs on source or deal-triggered runs cleanly undone.
"""

import unittest
from typing import List, Optional

from solitaire.core.card import Color, Suit, Rank, Card
from solitaire.core.pile import PileType, Pile, Deck
from solitaire.core.commands import Command, CardMoveCommand, StockDealCommand, CommandHistory
from solitaire.core.base_game import BaseGame, GameStatus, Move, MoveResult
from solitaire.games.freecell import FreeCellGame, FreeCellMoveType
from solitaire.games.spider import SpiderGame, SpiderMoveType, SpiderDifficulty


class TestAdversarialFreeCellSupermoveBoundaries(unittest.TestCase):
    """Empirically probes exact boundary conditions for FreeCell supermoves.
    
    Theorems:
      Target Non-Empty Cascade: M  = (1 + N) * 2^K
      Target Empty Cascade:     M' = (1 + N) * 2^(K - 1)  (for K >= 1)
    """

    def _setup_board(
        self,
        game: FreeCellGame,
        empty_cells: int,
        empty_cascades: int,
    ) -> None:
        for cell in game.free_cells:
            cell.clear()
        for i in range(4):
            if i >= empty_cells:
                game.free_cells[i].push(Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=300 + i))

        for cascade in game.cascades:
            cascade.clear()

    def _generate_alternating_sequence(self, top_rank: int, length: int, top_suit: Suit = Suit.SPADES) -> List[Card]:
        cards: List[Card] = []
        for i in range(length):
            rank_val = top_rank - i
            if rank_val < 1:
                raise ValueError(f'Rank underflow for top_rank {top_rank} length {length}')
            if top_suit.is_black:
                suit = Suit.SPADES if (i % 2 == 0) else Suit.HEARTS
            else:
                suit = Suit.HEARTS if (i % 2 == 0) else Suit.SPADES
            cards.append(Card(suit, Rank(rank_val), is_face_up=True, card_id=500 + i))
        return cards

    def test_occupied_cascade_supermove_exact_boundaries(self):
        """Probes sequence length == M (succeeds) and sequence length == M + 1 (strictly rejected)
        for target OCCUPIED cascade across multiple (N, K) parameter combinations:
          M = (1 + N) * 2^K
        """
        test_cases = [
            (0, 0, 1),
            (1, 0, 2),
            (2, 0, 3),
            (3, 0, 4),
            (4, 0, 5),
            (0, 1, 2),
            (1, 1, 4),
            (2, 1, 6),
            (3, 1, 8),
            (0, 2, 4),
            (1, 2, 8),
            (2, 2, 12),
        ]

        for N, K, expected_M in test_cases:
            with self.subTest(N=N, K=K, target='occupied', M=expected_M):
                game = FreeCellGame(seed=42)
                self._setup_board(game, empty_cells=N, empty_cascades=K)

                # Destination cascade_0: occupied with King of Spades (rank 13)
                dst_card = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=100)
                game.cascades[0].push(dst_card)

                # Source cascade_1: alternating sequence of length M starting with rank 12 (Queen of Hearts)
                seq_m = self._generate_alternating_sequence(top_rank=12, length=expected_M, top_suit=Suit.HEARTS)
                game.cascades[1].push_many(seq_m)

                # Cascades 2..(1 + K) remain empty (exactly K empty cascades)
                # Cascades (2 + K)..7 filled with dummy cards
                for c_idx in range(2 + K, 8):
                    game.cascades[c_idx].push(Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=400 + c_idx))

                self.assertEqual(game.get_empty_freecell_count(), N)
                self.assertEqual(game.get_empty_cascade_count(), K)
                self.assertEqual(game.calculate_max_supermove_cards('cascade_0'), expected_M)

                # Move of length M succeeds
                move_m = Move('cascade_1', 'cascade_0', card_count=expected_M, card_id=seq_m[0].card_id)
                self.assertTrue(game.is_legal_move(move_m))
                res_m = game.make_move(move_m)
                self.assertTrue(res_m.success)
                self.assertEqual(len(game.cascades[0]), 1 + expected_M)
                self.assertEqual(len(game.cascades[1]), 0)

                # Undo
                self.assertTrue(game.undo())
                self.assertEqual(len(game.cascades[0]), 1)
                self.assertEqual(len(game.cascades[1]), expected_M)

                # Move of length M + 1 strictly rejected
                if expected_M + 1 <= 12:
                    game.cascades[1].clear()
                    seq_m_plus_1 = self._generate_alternating_sequence(top_rank=12, length=expected_M + 1, top_suit=Suit.HEARTS)
                    game.cascades[1].push_many(seq_m_plus_1)

                    move_m_plus_1 = Move('cascade_1', 'cascade_0', card_count=expected_M + 1, card_id=seq_m_plus_1[0].card_id)
                    self.assertFalse(game.is_legal_move(move_m_plus_1))
                    res_fail = game.make_move(move_m_plus_1)
                    self.assertFalse(res_fail.success)
                    self.assertIn('supermove', res_fail.error_message.lower())
                    self.assertEqual(len(game.cascades[0]), 1)
                    self.assertEqual(len(game.cascades[1]), expected_M + 1)

    def test_empty_cascade_supermove_exact_boundaries(self):
        """Probes sequence length == M' (succeeds) and sequence length == M' + 1 (strictly rejected)
        for target EMPTY cascade across multiple (N, K) parameter combinations:
          M' = (1 + N) * 2^(K - 1)
        """
        test_cases = [
            (0, 1, 1),
            (1, 1, 2),
            (2, 1, 3),
            (3, 1, 4),
            (4, 1, 5),
            (0, 2, 2),
            (1, 2, 4),
            (2, 2, 6),
            (3, 2, 8),
            (4, 2, 10),
            (0, 3, 4),
            (1, 3, 8),
        ]

        for N, K, expected_M_prime in test_cases:
            with self.subTest(N=N, K=K, target='empty', M_prime=expected_M_prime):
                game = FreeCellGame(seed=42)
                self._setup_board(game, empty_cells=N, empty_cascades=K)

                # Destination cascade_0 is EMPTY.
                # Source cascade_1: alternating sequence of length M_prime
                seq_m = self._generate_alternating_sequence(top_rank=13, length=expected_M_prime, top_suit=Suit.SPADES)
                game.cascades[1].push_many(seq_m)

                # Target cascade_0 is empty (1 empty cascade).
                # Cascades 2..K are empty (K - 1 empty cascades).
                # Cascades (1 + K)..7 filled with dummy cards.
                for c_idx in range(1 + K, 8):
                    game.cascades[c_idx].push(Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=400 + c_idx))

                self.assertEqual(game.get_empty_freecell_count(), N)
                self.assertEqual(game.get_empty_cascade_count(), K)
                self.assertEqual(game.calculate_max_supermove_cards('cascade_0'), expected_M_prime)

                # Move of length M' succeeds
                move_m = Move('cascade_1', 'cascade_0', card_count=expected_M_prime, card_id=seq_m[0].card_id)
                self.assertTrue(game.is_legal_move(move_m))
                res_m = game.make_move(move_m)
                self.assertTrue(res_m.success)
                self.assertEqual(len(game.cascades[0]), expected_M_prime)
                self.assertEqual(len(game.cascades[1]), 0)

                # Undo
                self.assertTrue(game.undo())
                self.assertEqual(len(game.cascades[0]), 0)
                self.assertEqual(len(game.cascades[1]), expected_M_prime)

                # Move of length M' + 1 strictly rejected
                if expected_M_prime + 1 <= 13:
                    game.cascades[1].clear()
                    seq_m_plus_1 = self._generate_alternating_sequence(top_rank=13, length=expected_M_prime + 1, top_suit=Suit.SPADES)
                    game.cascades[1].push_many(seq_m_plus_1)

                    move_m_plus_1 = Move('cascade_1', 'cascade_0', card_count=expected_M_prime + 1, card_id=seq_m_plus_1[0].card_id)
                    self.assertFalse(game.is_legal_move(move_m_plus_1))
                    res_fail = game.make_move(move_m_plus_1)
                    self.assertFalse(res_fail.success)
                    self.assertIn('supermove', res_fail.error_message.lower())
                    self.assertEqual(len(game.cascades[0]), 0)
                    self.assertEqual(len(game.cascades[1]), expected_M_prime + 1)

    def test_empty_cascades_interaction_k1_exact_capacity(self):
        """Probes specific scenario: K=1 empty cascade (dest itself), no other empty cascades.
        Capacity M' = 1 + N.
        """
        for N in range(5):
            expected_cap = 1 + N
            with self.subTest(N=N, expected_capacity=expected_cap):
                game = FreeCellGame(seed=42)
                self._setup_board(game, empty_cells=N, empty_cascades=1)

                seq_ok = self._generate_alternating_sequence(top_rank=10, length=expected_cap, top_suit=Suit.SPADES)
                game.cascades[1].push_many(seq_ok)

                # Cascades 2..7 filled with dummy cards (only cascade_0 is empty)
                for c_idx in range(2, 8):
                    game.cascades[c_idx].push(Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=400 + c_idx))

                self.assertEqual(game.get_empty_freecell_count(), N)
                self.assertEqual(game.get_empty_cascade_count(), 1)
                self.assertEqual(game.calculate_max_supermove_cards('cascade_0'), expected_cap)

                # Exact capacity succeeds
                res_ok = game.make_move(Move('cascade_1', 'cascade_0', card_count=expected_cap, card_id=seq_ok[0].card_id))
                self.assertTrue(res_ok.success)
                self.assertEqual(len(game.cascades[0]), expected_cap)

                # Undo
                self.assertTrue(game.undo())
                self.assertEqual(len(game.cascades[0]), 0)

                # Capacity + 1 strictly rejected
                game.cascades[1].clear()
                seq_bad = self._generate_alternating_sequence(top_rank=10, length=expected_cap + 1, top_suit=Suit.SPADES)
                game.cascades[1].push_many(seq_bad)

                res_bad = game.make_move(Move('cascade_1', 'cascade_0', card_count=expected_cap + 1, card_id=seq_bad[0].card_id))
                self.assertFalse(res_bad.success)
                self.assertIn('supermove', res_bad.error_message.lower())
                self.assertEqual(len(game.cascades[0]), 0)

    def test_supermove_rejection_non_alternating_color(self):
        """Rejects multi-card sequence if any adjacent pair has identical color."""
        game = FreeCellGame(seed=42)
        self._setup_board(game, empty_cells=4, empty_cascades=2)
        game.cascades[0].push(Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=100))

        # 9♥ (red) and 8♦ (red)
        c9 = Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=509)
        c8 = Card(Suit.DIAMONDS, Rank.EIGHT, is_face_up=True, card_id=508)
        game.cascades[1].push_many([c9, c8])
        for c_idx in range(4, 8):
            game.cascades[c_idx].push(Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=400 + c_idx))

        res = game.make_move(Move('cascade_1', 'cascade_0', card_count=2, card_id=c9.card_id))
        self.assertFalse(res.success)
        self.assertIn('alternat', res.error_message.lower())

    def test_supermove_rejection_wrong_destination_rank(self):
        """Rejects multi-card sequence if base card does not match destination rank - 1."""
        game = FreeCellGame(seed=42)
        self._setup_board(game, empty_cells=4, empty_cascades=2)
        game.cascades[0].push(Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=100))

        seq = self._generate_alternating_sequence(top_rank=9, length=2, top_suit=Suit.HEARTS)
        game.cascades[1].push_many(seq)
        for c_idx in range(4, 8):
            game.cascades[c_idx].push(Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=400 + c_idx))

        res = game.make_move(Move('cascade_1', 'cascade_0', card_count=2, card_id=seq[0].card_id))
        self.assertFalse(res.success)


class TestAdversarialSpiderDealGuards(unittest.TestCase):
    """Empirically probes Spider Solitaire deal guard boundary conditions.
    Dealing from stock is strictly forbidden if ANY of the 10 tableau columns is empty.
    """

    def test_deal_attempt_with_each_individual_empty_column_rejected(self):
        """Probes each column 0 through 9 being the SOLE empty column out of 10."""
        for empty_col_idx in range(10):
            with self.subTest(empty_column=empty_col_idx):
                game = SpiderGame(num_suits=1, seed=42)
                for i, col in enumerate(game.tableau):
                    col.clear()
                    if i != empty_col_idx:
                        col.push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=i))

                stock_before = len(game.stock)
                self.assertGreaterEqual(stock_before, 10)
                self.assertEqual(len(game.tableau[empty_col_idx]), 0)

                deal_move = Move(SpiderMoveType.DEAL_STOCK, 'stock', 'tableau_0')
                self.assertFalse(game.is_legal_move(deal_move))

                res = game.deal_stock()
                self.assertFalse(res.success)
                self.assertIn('empty', res.error_message.lower())

                # Stock count and columns unchanged
                self.assertEqual(len(game.stock), stock_before)
                self.assertEqual(len(game.tableau[empty_col_idx]), 0)
                for i, col in enumerate(game.tableau):
                    if i != empty_col_idx:
                        self.assertEqual(len(col), 1)

    def test_deal_attempt_with_multiple_empty_columns_rejected(self):
        """Probes multiple empty columns (2 empty, 5 empty, all 10 empty)."""
        for num_empty in (2, 5, 10):
            with self.subTest(num_empty=num_empty):
                game = SpiderGame(num_suits=1, seed=42)
                for i, col in enumerate(game.tableau):
                    col.clear()
                    if i >= num_empty:
                        col.push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=i))

                stock_before = len(game.stock)
                res = game.deal_stock()
                self.assertFalse(res.success)
                self.assertEqual(len(game.stock), stock_before)

    def test_deal_attempt_with_exhausted_stock_rejected(self):
        """Probes dealing when stock is empty."""
        game = SpiderGame(num_suits=1, seed=42)
        for col in game.tableau:
            if col.is_empty:
                col.push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=999))
        game.stock.clear()
        res = game.deal_stock()
        self.assertFalse(res.success)
        self.assertIn('stock', res.error_message.lower())

    def test_deal_success_when_all_10_columns_non_empty(self):
        """Verifies deal succeeds cleanly when all 10 columns are non-empty."""
        game = SpiderGame(num_suits=1, seed=42)
        for i, col in enumerate(game.tableau):
            col.clear()
            col.push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=i))

        stock_before = len(game.stock)
        score_before = game.score
        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.stock), stock_before - 10)
        self.assertEqual(game.score, score_before - 1)
        for col in game.tableau:
            self.assertEqual(len(col), 2)
            self.assertTrue(col.peek().is_face_up)


class TestAdversarialSpiderSequenceClearing(unittest.TestCase):
    """Empirically probes Spider 13-card sequence clearing logic.
    A complete King-to-Ace sequence must be of the IDENTICAL suit.
    """

    def test_13_card_run_mixed_suit_at_king_strictly_NOT_cleared(self):
        """King is HEARTS, cards Q down to A are SPADES (suit break at top card)."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        game.tableau[0].push(Card(Suit.HEARTS, Rank.KING, is_face_up=True, card_id=100))
        for r in range(12, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(c_ace)

        score_before = game.score
        res = game.make_move(Move('tableau_1', 'tableau_0', card_id=c_ace.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 13)
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(game.score, score_before - 1)

    def test_13_card_run_mixed_suit_at_middle_strictly_NOT_cleared(self):
        """Rank 7 is HEARTS, all other 12 cards are SPADES (suit break in middle)."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        for r in range(13, 1, -1):
            suit = Suit.HEARTS if r == 7 else Suit.SPADES
            game.tableau[0].push(Card(suit, Rank(r), is_face_up=True, card_id=100 + r))
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(c_ace)

        score_before = game.score
        res = game.make_move(Move('tableau_1', 'tableau_0', card_id=c_ace.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 13)
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(game.score, score_before - 1)

    def test_13_card_run_mixed_suit_at_ace_strictly_NOT_cleared(self):
        """Cards K down to 2 are SPADES, final Ace is HEARTS (suit break at bottom card)."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))
        c_ace_hearts = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=200)
        game.tableau[1].push(c_ace_hearts)

        score_before = game.score
        res = game.make_move(Move('tableau_1', 'tableau_0', card_id=c_ace_hearts.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 13)
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(game.score, score_before - 1)

    def test_13_card_run_invalid_rank_order_not_cleared(self):
        """13 cards of same suit but wrong order (missing rank 6, duplicate 5)."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        ranks = [13, 12, 11, 10, 9, 8, 7, 5, 5, 4, 3, 2]
        for idx, r in enumerate(ranks):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=300 + idx))
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(c_ace)

        res = game.make_move(Move('tableau_1', 'tableau_0', card_id=c_ace.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 13)
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)

    def test_12_card_incomplete_run_not_cleared(self):
        """12 cards K down to 2 of same suit: not cleared."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        for r in range(13, 2, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))
        c2 = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.tableau[1].push(c2)

        res = game.make_move(Move('tableau_1', 'tableau_0', card_id=c2.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 12)
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)

    def test_13_card_run_buried_under_card_not_cleared_until_uncovered(self):
        """A complete K-to-A run buried under extra card only clears when covering card moves."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        game.tableau[2].clear()

        for r in range(13, 0, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1))
        extra_5 = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=55)
        game.tableau[0].push(extra_5)

        self.assertEqual(len(game.tableau[0]), 14)
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)

        target_6 = Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=66)
        game.tableau[2].push(target_6)

        res = game.make_move(Move('tableau_0', 'tableau_2', card_id=extra_5.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.completed_runs, 1)
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertTrue(game.tableau[0].is_empty)
        self.assertEqual(len(game.tableau[2]), 2)


class TestAdversarialSpiderAtomicClearingUndo(unittest.TestCase):
    """Empirically probes Spider Solitaire atomic clearing undo and fog-of-war reversibility."""

    def test_atomic_clearing_undo_reversibility_and_fog_of_war(self):
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        hidden_0 = Card(Suit.SPADES, Rank.NINE, is_face_up=False, card_id=700)
        hidden_1 = Card(Suit.SPADES, Rank.TEN, is_face_up=False, card_id=701)
        game.tableau[0].push(hidden_0)
        game.tableau[0].push(hidden_1)

        expected_k_to_2_ids = []
        for r in range(13, 1, -1):
            c = Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1)
            game.tableau[0].push(c)
            expected_k_to_2_ids.append(c.card_id)

        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(c_ace)

        initial_score = game.score
        initial_moves = game.moves_count
        initial_snap = game.get_state_snapshot()

        # Move completing run
        res = game.make_move(Move('tableau_1', 'tableau_0', card_id=c_ace.card_id))
        self.assertTrue(res.success)

        # Invariants after run clearance:
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertEqual(game.completed_runs, 1)
        foundation_ids = [c.card_id for c in game.foundations[0].cards]
        self.assertEqual(foundation_ids, expected_k_to_2_ids + [c_ace.card_id])
        self.assertEqual(game.score, initial_score - 1 + 100)
        self.assertEqual(game.moves_count, initial_moves + 1)
        self.assertEqual(len(game.tableau[0]), 2)
        self.assertFalse(hidden_0.is_face_up)
        self.assertTrue(hidden_1.is_face_up)
        self.assertTrue(game.tableau[1].is_empty)

        # Undo
        self.assertTrue(game.undo())
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(game.completed_runs, 0)
        self.assertEqual(len(game.tableau[0]), 14)
        tab_ids = [c.card_id for c in game.tableau[0].cards]
        self.assertEqual(tab_ids, [hidden_0.card_id, hidden_1.card_id] + expected_k_to_2_ids)
        self.assertFalse(hidden_1.is_face_up)
        self.assertFalse(hidden_0.is_face_up)
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.tableau[1].peek().card_id, c_ace.card_id)
        self.assertTrue(game.tableau[1].peek().is_face_up)
        self.assertEqual(game.score, initial_score)
        self.assertEqual(game.moves_count, initial_moves)
        self.assertEqual(game.get_state_snapshot(), initial_snap)

        # Redo
        self.assertTrue(game.redo())
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertEqual(game.completed_runs, 1)
        self.assertEqual(game.score, initial_score - 1 + 100)
        self.assertTrue(hidden_1.is_face_up)
        self.assertTrue(game.tableau[1].is_empty)

        # Second Undo
        self.assertTrue(game.undo())
        self.assertEqual(game.get_state_snapshot(), initial_snap)

    def test_exposed_source_run_clearance_undo_reversibility(self):
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        k_to_a_ids = []
        for r in range(13, 0, -1):
            c = Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r - 1)
            game.tableau[0].push(c)
            k_to_a_ids.append(c.card_id)

        c4 = Card(Suit.SPADES, Rank.FOUR, is_face_up=True, card_id=804)
        game.tableau[0].push(c4)

        c5 = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=805)
        game.tableau[1].push(c5)

        initial_snap = game.get_state_snapshot()
        initial_score = game.score

        res = game.make_move(Move('tableau_0', 'tableau_1', card_id=c4.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.completed_runs, 1)
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertTrue(game.tableau[0].is_empty)
        self.assertEqual(len(game.tableau[1]), 2)
        self.assertEqual(game.score, initial_score - 1 + 100)

        # Undo
        self.assertTrue(game.undo())
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(len(game.tableau[0]), 14)
        tab0_ids = [c.card_id for c in game.tableau[0].cards]
        self.assertEqual(tab0_ids, k_to_a_ids + [c4.card_id])
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.tableau[1].peek().card_id, c5.card_id)
        self.assertEqual(game.score, initial_score)
        self.assertEqual(game.get_state_snapshot(), initial_snap)

    def test_deal_stock_run_clearing_undo_reversibility(self):
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
        initial_score = game.score

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(game.completed_runs, 1)
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertTrue(game.tableau[0].is_empty)

        # Undo
        self.assertTrue(game.undo())
        self.assertEqual(game.completed_runs, 0)
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(len(game.stock), 50)
        self.assertEqual(len(game.tableau[0]), 12)
        self.assertEqual(game.score, initial_score)
        self.assertEqual(game.get_state_snapshot(), initial_snap)

    def test_mixed_suit_stack_movement_strictly_rejected(self):
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        game.tableau[0].push(Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4))

        # 4♥ and 3♠
        c4 = Card(Suit.HEARTS, Rank.FOUR, is_face_up=True, card_id=16)
        c3 = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        game.tableau[1].push_many([c4, c3])

        res = game.make_move(Move('tableau_1', 'tableau_0', card_count=2, card_id=c4.card_id))
        self.assertFalse(res.success)
        self.assertIn('suit', res.error_message.lower())
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertEqual(len(game.tableau[1]), 2)

    def test_same_suit_stack_movement_to_empty_column_accepted(self):
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c4 = Card(Suit.SPADES, Rank.FOUR, is_face_up=True, card_id=3)
        c3 = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        c2 = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.tableau[1].push_many([c4, c3, c2])

        res = game.make_move(Move('tableau_1', 'tableau_0', card_count=3, card_id=c4.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 3)
        self.assertTrue(game.tableau[1].is_empty)

        # Undo
        self.assertTrue(game.undo())
        self.assertTrue(game.tableau[0].is_empty)
        self.assertEqual(len(game.tableau[1]), 3)


if __name__ == '__main__':
    unittest.main()
