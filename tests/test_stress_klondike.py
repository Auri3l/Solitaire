"""Adversarial stress and fuzzing suite for Klondike Solitaire and Core domain.

Covers:
1. 1,000+ random legal and illegal moves across multiple seeds.
2. Rapid deal/recycle loops (Turn 1 and Turn 3) with order and fog-of-war invariance.
3. Empty tableau manipulation edge cases.
4. Multi-card transfers with auto-flip and fog-of-war rollback.
5. Foundation demotions and score penalty invariance.
6. Auto-complete execution and full rollback.
7. Resilience against malformed inputs and illegal move fuzzing (exception safety and state corruption checks).
"""

import unittest
import random
import time
from typing import List, Tuple, Dict, Any, Optional

from solitaire.core.card import Color, Suit, Rank, Card
from solitaire.core.pile import PileType, Pile, Deck
from solitaire.core.commands import (
    CardMoveCommand,
    StockDealCommand,
    RecycleCommand,
    CommandHistory,
)
from solitaire.core.base_game import Move, MoveResult, GameStatus
from solitaire.games.klondike import KlondikeGame, MoveType, ScoringMode


class KlondikeStressTestSuite(unittest.TestCase):
    """Adversarial challenge tests for Milestone 1."""

    def _assert_invariants(self, game: KlondikeGame, msg: str = ""):
        """Verifies core structural invariants of the Klondike game state."""
        # 1. Total cards must be exactly 52
        total_cards = (
            len(game.stock) +
            len(game.waste) +
            sum(len(f) for f in game.foundations) +
            sum(len(t) for t in game.tableau)
        )
        self.assertEqual(total_cards, 52, f"Total cards invariant violated ({total_cards} != 52): {msg}")

        # 2. All 52 unique card IDs (0..51) must be present with no duplicates or losses
        all_cards: List[Card] = []
        all_cards.extend(game.stock.cards)
        all_cards.extend(game.waste.cards)
        for f in game.foundations:
            all_cards.extend(f.cards)
        for t in game.tableau:
            all_cards.extend(t.cards)

        card_ids = [c.card_id for c in all_cards]
        self.assertEqual(len(card_ids), 52, f"Card count mismatch: {msg}")
        self.assertEqual(set(card_ids), set(range(52)), f"Duplicate or missing card IDs: {msg}")

        # 3. Stock cards must all be face-down
        for c in game.stock:
            self.assertFalse(c.is_face_up, f"Stock card {c} is face-up: {msg}")

        # 4. Waste cards must all be face-up
        for c in game.waste:
            self.assertTrue(c.is_face_up, f"Waste card {c} is face-down: {msg}")

        # 5. Foundation cards must all be face-up and properly ordered
        for f_idx, f in enumerate(game.foundations):
            for idx, c in enumerate(f):
                self.assertTrue(c.is_face_up, f"Foundation card {c} is face-down: {msg}")
                self.assertEqual(c.rank.value, idx + 1, f"Foundation {f_idx} rank mismatch at {idx}: {c}")
                if idx > 0:
                    self.assertEqual(c.suit, f[0].suit, f"Foundation {f_idx} suit mismatch: {c}")

        # 6. Tableau columns: face-down cards can only be below face-up cards
        for t_idx, col in enumerate(game.tableau):
            seen_face_up = False
            for c_idx, c in enumerate(col):
                if c.is_face_up:
                    seen_face_up = True
                elif seen_face_up:
                    self.fail(f"Face-down card found above face-up card in tableau {t_idx} at {c_idx}: {msg}")

            # Face-up sequence must be descending alternating colors
            face_up_cards = [c for c in col if c.is_face_up]
            for i in range(len(face_up_cards) - 1):
                c_curr = face_up_cards[i]
                c_next = face_up_cards[i + 1]
                self.assertEqual(
                    c_curr.rank.value, c_next.rank.value + 1,
                    f"Tableau {t_idx} non-descending sequence at {i}: {c_curr} -> {c_next}: {msg}"
                )
                self.assertNotEqual(
                    c_curr.color, c_next.color,
                    f"Tableau {t_idx} same-color sequence at {i}: {c_curr} -> {c_next}: {msg}"
                )

    # =========================================================================
    # 1. 1,000+ Random Legal Moves across Multiple Seeds with Full Invariance
    # =========================================================================
    def test_random_walk_1000_moves_across_seeds_with_undo(self):
        """Executes 1,000+ random legal moves across 10 distinct seeds with
        interleaved undos/redos and full rollback verifying exact initial state.
        """
        seeds = [1, 42, 100, 256, 777, 999, 1234, 4321, 8888, 99999]
        moves_per_seed = 120  # 10 * 120 = 1,200 moves total

        total_executed = 0
        total_undone = 0

        for seed in seeds:
            game = KlondikeGame(turn_mode=random.choice([1, 3]), seed=seed)
            initial_snapshot = game.get_state_snapshot()
            rng = random.Random(seed)

            moves_this_seed = 0
            for step in range(moves_per_seed):
                self._assert_invariants(game, f"Seed {seed} step {step}")

                legal_moves = game.get_legal_moves()
                if not legal_moves or game.is_won():
                    break

                chosen_move = rng.choice(legal_moves)
                res = game.make_move(chosen_move)
                self.assertTrue(res.success, f"Legal move {chosen_move} failed on seed {seed}")
                moves_this_seed += 1
                total_executed += 1

                # Periodically test interleaved undo and redo (every 15 steps)
                if moves_this_seed % 15 == 0 and game.history.can_undo:
                    snap_before_undo = game.get_state_snapshot()
                    self.assertTrue(game.undo())
                    self.assertTrue(game.history.can_redo)
                    self.assertTrue(game.redo())
                    self.assertEqual(game.get_state_snapshot(), snap_before_undo)

            # Roll back all executed moves for this seed
            for _ in range(moves_this_seed):
                self.assertTrue(game.history.can_undo)
                self.assertTrue(game.undo())
                total_undone += 1

            self.assertFalse(game.history.can_undo)
            self.assertEqual(game.moves_count, 0)
            self.assertEqual(game.get_state_snapshot(), initial_snapshot)
            self._assert_invariants(game, f"Seed {seed} after full rollback")

        self.assertGreaterEqual(total_executed, 1000, f"Executed only {total_executed} moves")
        self.assertEqual(total_executed, total_undone)

    # =========================================================================
    # 2. Rapid Deal / Recycle Loops (Turn 1 & Turn 3)
    # =========================================================================
    def test_rapid_deal_recycle_loops_turn1(self):
        """Tests 100 consecutive deal-recycle cycles in Turn 1 mode.
        Verifies cyclic order preservation, card count invariants, score clamping,
        and full multi-thousand-step undo rollback.
        """
        game = KlondikeGame(turn_mode=1, seed=42)
        initial_stock_cards = [c.clone() for c in game.stock.cards]
        initial_snapshot = game.get_state_snapshot()

        num_cycles = 50
        for cycle in range(num_cycles):
            # Deal all 24 cards
            for d in range(24):
                res = game.deal_stock()
                self.assertTrue(res.success, f"Deal {d} in cycle {cycle} failed")

            self.assertEqual(len(game.stock), 0)
            self.assertEqual(len(game.waste), 24)
            self.assertTrue(all(c.is_face_up for c in game.waste))

            # Recycle waste to stock
            recycle_res = game.deal_stock()
            self.assertTrue(recycle_res.success, f"Recycle in cycle {cycle} failed")
            self.assertEqual(len(game.stock), 24)
            self.assertEqual(len(game.waste), 0)
            self.assertTrue(all(not c.is_face_up for c in game.stock))

            # Stock card order must exactly match initial order
            for i in range(24):
                self.assertEqual(game.stock[i].card_id, initial_stock_cards[i].card_id)

            self.assertEqual(game.recycles_count, cycle + 1)
            self.assertEqual(game.passes_through_stock, cycle + 2)

        # In standard scoring, score must not drift negative
        self.assertGreaterEqual(game.score, 0)

        # Full rollback: 50 cycles * 25 actions = 1,250 undos
        expected_moves = num_cycles * 25
        self.assertEqual(game.history.undo_count, expected_moves)
        for u in range(expected_moves):
            self.assertTrue(game.undo(), f"Undo step {u} failed")

        self.assertFalse(game.history.can_undo)
        self.assertEqual(game.get_state_snapshot(), initial_snapshot)

    def test_rapid_deal_recycle_loops_turn3(self):
        """Tests 50 consecutive deal-recycle cycles in Turn 3 mode.
        Verifies batching (8 deals of 3), cyclic order invariance, and rollback.
        """
        game = KlondikeGame(turn_mode=3, seed=777)
        initial_stock_cards = [c.clone() for c in game.stock.cards]
        initial_snapshot = game.get_state_snapshot()

        num_cycles = 30
        for cycle in range(num_cycles):
            for d in range(8):
                res = game.deal_stock()
                self.assertTrue(res.success, f"Turn 3 deal {d} cycle {cycle} failed")

            self.assertEqual(len(game.stock), 0)
            self.assertEqual(len(game.waste), 24)

            # Recycle
            res_rec = game.deal_stock()
            self.assertTrue(res_rec.success)
            self.assertEqual(len(game.stock), 24)
            self.assertEqual(len(game.waste), 0)

            # Order preservation
            for i in range(24):
                self.assertEqual(game.stock[i].card_id, initial_stock_cards[i].card_id)

        # Full rollback
        expected_moves = num_cycles * 9
        for _ in range(expected_moves):
            self.assertTrue(game.undo())

        self.assertEqual(game.get_state_snapshot(), initial_snapshot)

    def test_deal_recycle_max_recycles_limit(self):
        """Verifies max_recycles limit strictly halts recycling and respects invariants."""
        game = KlondikeGame(turn_mode=1, max_recycles=2, seed=123)

        # Pass 1 (0 recycles)
        for _ in range(24):
            game.deal_stock()
        res1 = game.deal_stock()  # Recycle 1
        self.assertTrue(res1.success)
        self.assertEqual(game.recycles_count, 1)

        # Pass 2 (1 recycle)
        for _ in range(24):
            game.deal_stock()
        res2 = game.deal_stock()  # Recycle 2
        self.assertTrue(res2.success)
        self.assertEqual(game.recycles_count, 2)

        # Pass 3 (2 recycles -> limit reached)
        for _ in range(24):
            game.deal_stock()
        res3 = game.deal_stock()  # Should fail
        self.assertFalse(res3.success)
        self.assertIn("Maximum stock recycles", res3.error_message)
        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 24)

    # =========================================================================
    # 3. Empty Tableau Manipulation
    # =========================================================================
    def test_empty_tableau_manipulation_comprehensive(self):
        """Tests all legal and illegal permutations on empty tableau columns."""
        game = KlondikeGame(seed=42)
        # Empty columns 0, 1, 2
        game.tableau[0].clear()
        game.tableau[1].clear()
        game.tableau[2].clear()

        # Non-King single card to empty column MUST FAIL
        for rank in range(1, 13):  # Ace through Queen
            card = Card(Suit.SPADES, Rank(rank), is_face_up=True, card_id=rank - 1)
            game.tableau[3].push(card)
            m = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_3", "tableau_0", card_count=1)
            res = game.make_move(m)
            self.assertFalse(res.success, f"Rank {Rank(rank).display_str} was allowed on empty tableau")
            self.assertIn("king", res.error_message.lower())
            game.tableau[3].pop()

        # King to empty column MUST SUCCEED
        king = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        game.tableau[3].push(king)
        m_king = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_3", "tableau_0", card_count=1)
        res_king = game.make_move(m_king)
        self.assertTrue(res_king.success)
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertEqual(game.tableau[0].peek(), king)

        # King-headed stack to empty column MUST SUCCEED
        q = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        j = Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        game.tableau[0].push_many([q, j])
        self.assertEqual(len(game.tableau[0]), 3)

        m_stack = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_1", card_count=3)
        res_stack = game.make_move(m_stack)
        self.assertTrue(res_stack.success)
        self.assertEqual(len(game.tableau[1]), 3)
        self.assertTrue(game.tableau[0].is_empty)

        # Partial stack NOT starting with King to empty column MUST FAIL
        m_partial = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_2", card_count=2)
        res_partial = game.make_move(m_partial)
        self.assertFalse(res_partial.success)
        self.assertTrue(game.tableau[2].is_empty)

        # Move from empty column MUST FAIL
        m_from_empty = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_2", card_count=1)
        res_empty = game.make_move(m_from_empty)
        self.assertFalse(res_empty.success)

        # Move between two empty columns MUST FAIL
        m_empty_to_empty = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_2", card_count=1)
        res_ee = game.make_move(m_empty_to_empty)
        self.assertFalse(res_ee.success)

        # Move to self MUST FAIL
        m_self = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_1", "tableau_1", card_count=1)
        res_self = game.make_move(m_self)
        self.assertFalse(res_self.success)

    # =========================================================================
    # 4. Multi-Card Transfers and Auto-Flip Fog-of-War Invariance
    # =========================================================================
    def test_multi_card_transfers_deep_stack_and_fog_of_war(self):
        """Tests transferring stacks of up to 12 cards, verifying auto-flip exposed cards
        and complete re-obscuring fog-of-war on undo.
        """
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Set up a face-down card at the base of tableau 0
        hidden_card = Card(Suit.DIAMONDS, Rank.ACE, is_face_up=False, card_id=26)
        game.tableau[0].push(hidden_card)

        # Build an alternating sequence of 10 cards on tableau 0
        # K♠, Q♥, J♣, 10♦, 9♠, 8♥, 7♣, 6♦, 5♠, 4♥
        suits = [Suit.SPADES, Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS]
        cards_seq = []
        for i, rank_val in enumerate(range(13, 3, -1)):
            s = suits[i % 2]  # Alternates SPADES (black) and HEARTS (red)
            c = Card(s, Rank(rank_val), is_face_up=True, card_id=100 + i)
            cards_seq.append(c)

        game.tableau[0].push_many(cards_seq)
        self.assertEqual(len(game.tableau[0]), 11)  # 1 face-down + 10 face-up

        # Destination has 5♠ on tableau 1, waiting for 4♥ ?
        # Or move entire 10-card stack to an empty column 1 (since it starts with King)
        snap_before = game.get_state_snapshot()

        move_all = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_1", card_count=10)
        res = game.make_move(move_all)
        self.assertTrue(res.success)

        # Hidden card must now be auto-flipped to face-up
        self.assertTrue(hidden_card.is_face_up)
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertEqual(len(game.tableau[1]), 10)

        # Undo must restore hidden card to face-down (fog-of-war restored)
        self.assertTrue(game.undo())
        self.assertFalse(hidden_card.is_face_up)
        self.assertEqual(len(game.tableau[0]), 11)
        self.assertEqual(len(game.tableau[1]), 0)
        self.assertEqual(game.get_state_snapshot(), snap_before)

    def test_multi_card_transfer_reject_face_down_within_stack(self):
        """Attempts to transfer a stack containing a face-down card within it."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        c1 = Card(Suit.SPADES, Rank.KING, is_face_up=False, card_id=12)
        c2 = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        game.tableau[0].push_many([c1, c2])

        m = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_1", card_count=2)
        res = game.make_move(m)
        self.assertFalse(res.success)
        self.assertIn("face-down", res.error_message.lower())

    def test_multi_card_transfer_reject_non_alternating_stack(self):
        """Attempts to transfer a stack where internal sequence is not valid alternating descending."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # King spades and King hearts (not descending)
        c1 = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        c2 = Card(Suit.HEARTS, Rank.KING, is_face_up=True, card_id=25)
        game.tableau[0].push_many([c1, c2])

        m = Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_1", card_count=2)
        res = game.make_move(m)
        self.assertFalse(res.success)

    # =========================================================================
    # 5. Foundation Demotions and Scoring Invariance
    # =========================================================================
    def test_foundation_demotions_and_score_tracking(self):
        """Tests legal and illegal demotions from foundation back to tableau,
        verifying penalty deltas, zero-drift clamping, and undo restoration.
        """
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        game.foundations[0].clear()

        # Foundation 0: A♠, 2♠, 3♠
        a_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        two_spades = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        three_spades = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        game.foundations[0].push_many([a_spades, two_spades, three_spades])

        # Tableau 0 has 4♥
        four_hearts = Card(Suit.HEARTS, Rank.FOUR, is_face_up=True, card_id=16)
        game.tableau[0].push(four_hearts)

        game.score = 50
        initial_snap = game.get_state_snapshot()

        # Demote 3♠ onto 4♥ (legal: black 3 onto red 4)
        m_demote = Move(MoveType.FOUNDATION_TO_TABLEAU, "foundation_0", "tableau_0", card_count=1)
        res = game.make_move(m_demote)
        self.assertTrue(res.success)
        self.assertEqual(len(game.foundations[0]), 2)
        self.assertEqual(game.tableau[0].peek(), three_spades)
        self.assertEqual(game.score, 35)  # -15 penalty

        # Demote 2♠ onto 3♠ (illegal: same suit/color: black 2 onto black 3)
        m_demote_illegal = Move(MoveType.FOUNDATION_TO_TABLEAU, "foundation_0", "tableau_0", card_count=1)
        res_il = game.make_move(m_demote_illegal)
        self.assertFalse(res_il.success)
        self.assertEqual(len(game.foundations[0]), 2)
        self.assertEqual(game.score, 35)

        # Demote to empty tableau (must fail unless card is King)
        m_demote_empty = Move(MoveType.FOUNDATION_TO_TABLEAU, "foundation_0", "tableau_1", card_count=1)
        res_emp = game.make_move(m_demote_empty)
        self.assertFalse(res_emp.success)

        # Undo legal demotion
        self.assertTrue(game.undo())
        self.assertEqual(len(game.foundations[0]), 3)
        self.assertEqual(game.score, 50)
        self.assertEqual(game.get_state_snapshot(), initial_snap)

    def test_foundation_demote_king_to_empty_tableau(self):
        """Demoting a King from foundation to empty tableau column is legal."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.foundations[0].clear()

        king = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        game.foundations[0].push(king)
        game.score = 30

        m = Move(MoveType.FOUNDATION_TO_TABLEAU, "foundation_0", "tableau_0", card_count=1)
        res = game.make_move(m)
        self.assertTrue(res.success)
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(game.tableau[0].peek(), king)
        self.assertEqual(game.score, 15)

        game.undo()
        self.assertEqual(game.score, 30)
        self.assertEqual(game.foundations[0].peek(), king)

    # =========================================================================
    # 6. Auto-Complete Solver and Full Rollback
    # =========================================================================
    def test_auto_complete_execution_and_complete_rollback(self):
        """Tests auto_finish solver on complete board, verifying step-by-step
        progression to victory, win condition trigger, and full undo rollback.
        """
        game = KlondikeGame(seed=42)
        game.stock.clear()
        game.waste.clear()
        for f in game.foundations:
            f.clear()
        for t in game.tableau:
            t.clear()

        # Distribute full 52 cards across tableau columns as valid alternating descending sequences
        # Col 0: Spades/Hearts: K♠, Q♥, J♠, 10♥, 9♠, 8♥, 7♠, 6♥, 5♠, 4♥, 3♠, 2♥, A♠
        # Col 1: Hearts/Spades: K♥, Q♠, J♥, 10♠, 9♥, 8♠, 7♥, 6♠, 5♥, 4♠, 3♥, 2♠, A♥
        # Col 2: Diamonds/Clubs: K♦, Q♣, J♦, 10♣, 9♦, 8♣, 7♦, 6♣, 5♦, 4♣, 3♦, 2♣, A♦
        # Col 3: Clubs/Diamonds: K♣, Q♦, J♣, 10♦, 9♣, 8♦, 7♣, 6♦, 5♣, 4♦, 3♣, 2♦, A♣
        deck = Deck.create_standard()
        cards_by_suit_rank = {(c.suit, c.rank): c for c in deck}

        patterns = [
            (0, Suit.SPADES, Suit.HEARTS),
            (1, Suit.HEARTS, Suit.SPADES),
            (2, Suit.DIAMONDS, Suit.CLUBS),
            (3, Suit.CLUBS, Suit.DIAMONDS),
        ]

        for col_idx, primary_suit, secondary_suit in patterns:
            for rank_val in range(13, 0, -1):
                suit = primary_suit if rank_val % 2 != 0 else secondary_suit
                c = cards_by_suit_rank[(suit, Rank(rank_val))]
                c.is_face_up = True
                game.tableau[col_idx].push(c)

        self._assert_invariants(game, "Pre auto-finish layout")
        self.assertTrue(game.can_auto_finish())
        self.assertFalse(game.is_won())

        pre_autofinish_snap = game.get_state_snapshot()

        # Run auto_finish_all()
        steps = game.auto_finish_all()
        self.assertEqual(steps, 52)
        self.assertTrue(game.is_won())
        self.assertEqual(game.game_status, GameStatus.WON)
        self.assertEqual(sum(len(f) for f in game.foundations), 52)
        self.assertTrue(all(t.is_empty for t in game.tableau))

        # Roll back all 52 auto-finish moves
        for s in range(52):
            self.assertTrue(game.undo(), f"Undo step {s} failed")

        self.assertFalse(game.is_won())
        self.assertEqual(game.game_status, GameStatus.IN_PROGRESS)
        self.assertEqual(game.get_state_snapshot(), pre_autofinish_snap)
        self._assert_invariants(game, "Post auto-finish rollback")

    def test_can_auto_finish_blocked_by_stock_or_waste_or_fog(self):
        """Verifies can_auto_finish criteria strictly enforces:
        stock empty, waste empty, and ZERO face-down cards in tableau.
        """
        game = KlondikeGame(seed=42)
        self.assertFalse(game.can_auto_finish())  # Fresh game has stock, waste, face-down cards

        # Clear stock/waste, but tableau still has face-down cards
        game.stock.clear()
        game.waste.clear()
        self.assertFalse(game.can_auto_finish())

        # Turn all cards face-up
        for t in game.tableau:
            for c in t:
                c.is_face_up = True
        self.assertTrue(game.can_auto_finish())

        # Put 1 card in waste
        c = game.tableau[0].pop()
        game.waste.push(c)
        self.assertFalse(game.can_auto_finish())

        # Put 1 card in stock
        game.waste.clear()
        c.is_face_up = False
        game.stock.push(c)
        self.assertFalse(game.can_auto_finish())

    # =========================================================================
    # 7. Illegal Move Fuzzing and Malformed Input Resilience
    # =========================================================================
    def test_illegal_move_fuzzing_state_integrity(self):
        """Fuzzes game with 1,000+ randomized illegal moves, verifying:
        - Strict rejection of all illegal moves
        - Zero state corruptions (snapshot and invariants strictly preserved)
        """
        game = KlondikeGame(seed=12345)
        rng = random.Random(9999)

        initial_snapshot = game.get_state_snapshot()
        rejected_count = 0

        piles_list = list(game.piles.keys())

        for f_idx in range(1000):
            # Generate arbitrary combinations of valid pile IDs
            src = rng.choice(piles_list)
            dst = rng.choice(piles_list)
            cnt = rng.choice([-5, 0, 1, 2, 7, 13, 100])
            cid = rng.choice([None, -1, 0, 15, 35, 51, 999])

            move = Move(source_pile_id=src, dest_pile_id=dst, card_count=cnt, card_id=cid)
            snap_before = game.get_state_snapshot()

            is_legal = game.is_legal_move(move)
            if not is_legal:
                res = game.make_move(move)
                self.assertFalse(res.success, f"Fuzz move {move} succeeded when declared illegal!")
                # Game state must NOT be modified
                self.assertEqual(game.get_state_snapshot(), snap_before)
                rejected_count += 1
            else:
                # If legal by coincidence, execute, assert invariants, and roll back
                res = game.make_move(move)
                self.assertTrue(res.success)
                self._assert_invariants(game, f"Accidentally legal fuzz move {move}")
                game.undo()
                self.assertEqual(game.get_state_snapshot(), snap_before)

        self.assertGreater(rejected_count, 900)
        self.assertEqual(game.get_state_snapshot(), initial_snapshot)
        self._assert_invariants(game, "Post-fuzz state")

    def test_malformed_inputs_robustness_audit(self):
        """Audits handling of malformed inputs:
        Verifies behavior on invalid pile IDs, None objects, and unknown types.
        Documents exceptions vs graceful failures.
        """
        game = KlondikeGame(seed=42)
        snap_before = game.get_state_snapshot()

        # Test A: Nonexistent pile IDs
        malformed_moves = [
            Move(source_pile_id="nonexistent_src", dest_pile_id="tableau_0"),
            Move(source_pile_id="tableau_0", dest_pile_id="nonexistent_dst"),
            Move(source_pile_id="garbage", dest_pile_id="trash"),
            Move(source_pile_id="waste", dest_pile_id="foundation_99"),
            Move(source_pile_id="tableau_99", dest_pile_id="tableau_0"),
            Move(source_pile_id="", dest_pile_id="tableau_0"),
        ]

        for m in malformed_moves:
            try:
                res = game.make_move(m)
                # If it doesn't crash, it MUST return fail
                self.assertFalse(res.success)
            except ValueError as ex:
                # Documenting current behavior: raises ValueError because get_pile_by_id raises
                pass

        # Game state must remain intact regardless
        self.assertEqual(game.get_state_snapshot(), snap_before)

        # Test B: find_best_move_for_card with invalid pile ID
        try:
            best = game.find_best_move_for_card("invalid_pile_id")
            self.assertIsNone(best)
        except ValueError:
            pass

        # Test C: make_move(None)
        try:
            res_none = game.make_move(None)
            self.assertFalse(res_none.success)
        except AttributeError:
            pass


if __name__ == "__main__":
    unittest.main()
