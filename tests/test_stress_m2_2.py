"""Empirical Stress, Random Walk Fuzzing, and Adversarial Challenge Suite.

Milestone 2: FreeCell and Spider Solitaire Engines
Author: teamwork_preview_challenger_m2_2

Coverage:
1. FreeCell Random Walk: 100 legal moves + 100 undos (exact initial deal equality) + 100 redos (exact post-walk equality),
   tested across seeds and Microsoft deal numbers with complete structural invariance at every step.
2. Spider Multi-Turn Random Play: 250+ steps across 1-suit, 2-suit, and 4-suit variants with interleaved moves, deals,
   undos, and redos. Invariant guarantees: total cards strictly 104, zero card duplication, valid runs.
3. Fuzz Invalid Moves: Exhaustive validation of malformed and illegal Move objects (invalid pile IDs, nonexistent card IDs,
   negative/zero counts, illegal placements, supermove overflows, empty-column deal guards) returning MoveResult.fail
   gracefully with zero unhandled exceptions and exact state snapshot preservation.
4. Adversarial Vulnerability Reproductions: Empirical demonstration of cross-pile rule bypasses (Spider tableau-to-foundation,
   foundation-to-tableau, tableau-to-stock; FreeCell foundation-to-foundation and foundation-to-freecell demotion).
"""

import unittest
import random
from typing import List, Dict, Any, Optional, Set

from solitaire.core.card import Color, Suit, Rank, Card
from solitaire.core.pile import PileType, Pile, Deck
from solitaire.core.commands import (
    Command,
    CardMoveCommand,
    StockDealCommand,
    CommandHistory,
)
from solitaire.core.base_game import BaseGame, GameStatus, Move, MoveResult
from solitaire.games.freecell import FreeCellGame, FreeCellMoveType
from solitaire.games.spider import SpiderGame, SpiderDifficulty, SpiderMoveType


class TestFreeCellStressAndRandomWalk(unittest.TestCase):
    """Target 1: FreeCell random walk, undo/redo state preservation, and structural invariants."""

    def _assert_freecell_invariants(self, game: FreeCellGame, step_msg: str = ""):
        """Verifies all structural invariants of FreeCell state."""
        # 1. Total cards must be exactly 52 across unique piles
        unique_piles = set(game.piles.values())
        all_cards: List[Card] = [c for p in unique_piles for c in p.cards]
        self.assertEqual(
            len(all_cards), 52,
            f"FreeCell total card count invariant violated ({len(all_cards)} != 52): {step_msg}"
        )

        # 2. All 52 unique card IDs (0..51) must be present without duplicates or omissions
        card_ids = [c.card_id for c in all_cards]
        self.assertEqual(
            len(set(card_ids)), 52,
            f"Duplicate or missing card IDs in FreeCell: {step_msg}"
        )
        self.assertEqual(
            set(card_ids), set(range(52)),
            f"Card IDs set mismatch in FreeCell: {step_msg}"
        )

        # 3. All cards in FreeCell are 100% face-up
        for c in all_cards:
            self.assertTrue(
                c.is_face_up,
                f"Card {c} is face-down in FreeCell: {step_msg}"
            )

        # 4. Free cells capacity <= 1
        for fc_idx, fc in enumerate(game.free_cells):
            self.assertLessEqual(
                len(fc), 1,
                f"Free cell {fc_idx} has {len(fc)} cards (max 1): {step_msg}"
            )

        # 5. Foundations: strictly single-suit ascending Ace through King
        for f_idx, f in enumerate(game.foundations):
            if not f.is_empty:
                f_suit = f[0].suit
                for idx, c in enumerate(f):
                    self.assertEqual(
                        c.suit, f_suit,
                        f"Foundation {f_idx} suit mismatch at {idx}: {c} != {f_suit}"
                    )
                    self.assertEqual(
                        c.rank.value, idx + 1,
                        f"Foundation {f_idx} rank mismatch at {idx}: expected {idx + 1}, got {c.rank.value}"
                    )



    def test_freecell_random_walk_100_moves_undo_redo_invariance(self):
        """TC-FC-STRESS-01: Generate 100 legal moves, execute them, then execute 100 undos
        -> verify exact board state equality with initial deal. Repeat with 100 redos ->
        verify exact board state equality with post-walk state.
        """
        random.seed(12345)
        game = FreeCellGame(seed=1)
        initial_snap = game.get_state_snapshot()
        self._assert_freecell_invariants(game, "initial state")

        executed_moves: List[Move] = []
        for step in range(100):
            legal_moves = game.get_legal_moves()
            self.assertTrue(
                len(legal_moves) > 0,
                f"Deadlock reached prematurely at step {step}"
            )
            move = random.choice(legal_moves)
            res = game.make_move(move)
            self.assertTrue(
                res.success,
                f"Legal move {move} failed to execute at step {step}: {res.error_message}"
            )
            executed_moves.append(move)
            self._assert_freecell_invariants(game, f"step {step}")

        self.assertEqual(len(executed_moves), 100)
        self.assertEqual(game.moves_count, 100)
        walk_snap = game.get_state_snapshot()

        # Execute 100 consecutive undos
        for i in range(100):
            self.assertTrue(game.can_undo, f"can_undo False before undo {i}")
            ok = game.undo()
            self.assertTrue(ok, f"Undo {i} failed")
            self._assert_freecell_invariants(game, f"undo step {i}")

        # Exact board equality with initial deal
        undone_snap = game.get_state_snapshot()
        self.assertEqual(
            undone_snap["piles"], initial_snap["piles"],
            "Board piles after 100 undos do not exactly match initial deal!"
        )
        self.assertEqual(game.moves_count, 0)
        self.assertEqual(game.score, 0)
        self.assertFalse(game.can_undo)

        # Execute 100 consecutive redos
        for i in range(100):
            self.assertTrue(game.can_redo, f"can_redo False before redo {i}")
            ok = game.redo()
            self.assertTrue(ok, f"Redo {i} failed")
            self._assert_freecell_invariants(game, f"redo step {i}")

        # Exact board equality with post-walk state
        redone_snap = game.get_state_snapshot()
        self.assertEqual(
            redone_snap["piles"], walk_snap["piles"],
            "Board piles after 100 redos do not exactly match post-walk state!"
        )
        self.assertEqual(game.moves_count, 100)
        self.assertFalse(game.can_redo)

    def test_freecell_multi_seed_random_walk_burst_undo_redo(self):
        """TC-FC-STRESS-02: Multi-deal stress test across Microsoft deal numbers
        and arbitrary seeds with randomized bursts of moves, undos, and redos.
        """
        test_configurations = [
            {"ms_game_number": 1},
            {"ms_game_number": 11982},
            {"seed": 2},
            {"seed": 8},
        ]

        for config in test_configurations:
            random.seed(999)
            game = FreeCellGame(**config)
            initial_snap = game.get_state_snapshot()

            moves_made = 0
            undos_made = 0
            redos_made = 0

            for step in range(120):
                self._assert_freecell_invariants(game, f"config {config} step {step}")
                action = random.random()

                if action < 0.25 and game.can_undo:
                    self.assertTrue(game.undo())
                    undos_made += 1
                elif action < 0.40 and game.can_redo:
                    self.assertTrue(game.redo())
                    redos_made += 1
                else:
                    legal = game.get_legal_moves()
                    if not legal:
                        if game.can_undo:
                            self.assertTrue(game.undo())
                            undos_made += 1
                        else:
                            break
                    else:
                        m = random.choice(legal)
                        res = game.make_move(m)
                        self.assertTrue(res.success)
                        moves_made += 1

            self._assert_freecell_invariants(game, f"config {config} completion")
            self.assertGreater(moves_made, 40)

    def test_freecell_supermove_formula_boundary_stress(self):
        """TC-FC-STRESS-03: Inductive Supermove formula (1 + N) * 2^K boundary enforcement.
        Moving exactly max allowed cards succeeds; moving max allowed + 1 cards is strictly rejected.
        """
        game = FreeCellGame(seed=42)
        for c in game.cascades:
            c.clear()
        for fc in game.free_cells:
            fc.clear()

        # N = 2 empty cells (occupy 2 cells), K = 1 empty cascade
        game.free_cells[0].push(Card(Suit.CLUBS, Rank.ACE, is_face_up=True, card_id=0))
        game.free_cells[1].push(Card(Suit.DIAMONDS, Rank.ACE, is_face_up=True, card_id=1))
        # Empty cells = 2 (freecell_2, freecell_3)
        self.assertEqual(game.get_empty_freecell_count(), 2)

        # Cascades 0..6 will be occupied; cascade 7 will be empty (K = 1)
        # In cascade 0, set up a valid descending alternating sequence of 7 cards:
        # [K♠, Q♥, J♠, 10♥, 9♠, 8♥, 7♠]
        test_ranks = [Rank.KING, Rank.QUEEN, Rank.JACK, Rank.TEN, Rank.NINE, Rank.EIGHT, Rank.SEVEN]
        test_suits = [Suit.SPADES, Suit.HEARTS, Suit.SPADES, Suit.HEARTS, Suit.SPADES, Suit.HEARTS, Suit.SPADES]
        for idx, (r, s) in enumerate(zip(test_ranks, test_suits)):
            game.cascades[0].push(Card(s, r, is_face_up=True, card_id=10 + idx))

        # Destination cascade 1 has A♠ (occupied)
        game.cascades[1].push(Card(Suit.HEARTS, Rank.TEN, is_face_up=True, card_id=30))
        # Cascades 2..6 occupied
        for i in range(2, 7):
            game.cascades[i].push(Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=40 + i))

        # Empty cascades count K = 1 (cascade_7 is empty)
        self.assertEqual(game.get_empty_cascade_count(), 1)

        # Max allowed to non-empty destination: (1 + 2) * 2^1 = 6 cards
        max_allowed = game.calculate_max_supermove_cards("cascade_1")
        self.assertEqual(max_allowed, 6)

        # Attempt to move 7 cards from cascade 0 to cascade 7 (empty column):
        # Max allowed to empty column: (1 + 2) * 2^(1 - 1) = 3 cards
        res_overflow_empty = game.make_move(
            Move("cascade_0", "cascade_7", card_count=4)
        )
        self.assertFalse(res_overflow_empty.success)
        self.assertIn("supermove", res_overflow_empty.error_message.lower())

        # Moving 3 cards to empty cascade_7 succeeds
        res_legal_empty = game.make_move(
            Move("cascade_0", "cascade_7", card_count=3)
        )
        self.assertTrue(res_legal_empty.success)
        self.assertEqual(len(game.cascades[7]), 3)

        # Undo restores state
        self.assertTrue(game.undo())
        self.assertEqual(len(game.cascades[7]), 0)


class TestSpiderMultiTurnStressTest(unittest.TestCase):
    """Target 2: Spider multi-turn random play, 104-card invariant, and stock deal reversibility."""

    def _assert_spider_invariants(self, game: SpiderGame, step_msg: str = ""):
        """Verifies core structural invariants of Spider Solitaire."""
        # 1. Total card count strictly 104 across distinct pile objects
        unique_piles = set(game.piles.values())
        all_cards = [c for p in unique_piles for c in p.cards]
        self.assertEqual(
            len(all_cards), 104,
            f"Spider total card count invariant violated ({len(all_cards)} != 104): {step_msg}"
        )

        # 2. Card IDs must be strictly range(104) with zero duplication
        card_ids = [c.card_id for c in all_cards]
        self.assertEqual(
            len(set(card_ids)), 104,
            f"Duplicate or missing card IDs in Spider ({len(set(card_ids))} != 104): {step_msg}"
        )
        self.assertEqual(
            set(card_ids), set(range(104)),
            f"Card IDs set mismatch in Spider: {step_msg}"
        )

        # 3. Stock pile cards must all be face-down and multiple of 10
        self.assertEqual(
            len(game.stock) % 10, 0,
            f"Stock size {len(game.stock)} is not a multiple of 10: {step_msg}"
        )
        self.assertEqual(
            game.deals_remaining, len(game.stock) // 10,
            f"deals_remaining mismatch: {game.deals_remaining} != {len(game.stock) // 10}: {step_msg}"
        )
        for c in game.stock:
            self.assertFalse(
                c.is_face_up,
                f"Stock card {c} is face-up: {step_msg}"
            )

        # 4. Foundations: Completed runs are strictly 13 cards of the identical suit, K down to A
        for f_idx, f in enumerate(game.foundations):
            if not f.is_empty:
                self.assertEqual(
                    len(f), 13,
                    f"Foundation {f_idx} has {len(f)} cards (must be 13): {step_msg}"
                )
                target_suit = f[0].suit
                for idx, c in enumerate(f):
                    self.assertTrue(c.is_face_up)
                    self.assertEqual(c.suit, target_suit)
                    self.assertEqual(c.rank.value, 13 - idx)

        # 5. Tableau columns: face-down cards can only precede face-up cards
        for t_idx, col in enumerate(game.tableau):
            seen_face_up = False
            for c_idx, c in enumerate(col):
                if c.is_face_up:
                    seen_face_up = True
                elif seen_face_up:
                    self.fail(
                        f"Face-down card found above face-up card in tableau {t_idx} at {c_idx}: {step_msg}"
                    )

    def test_spider_multi_turn_random_play_all_difficulties(self):
        """TC-SP-STRESS-01: Multi-turn random play across 1-suit, 2-suit, and 4-suit variants
        interspersed with random undos and redos -> verify zero crashes, zero card duplication,
        total card count strictly 104 at all steps.
        """
        difficulties = [
            SpiderDifficulty.ONE_SUIT,
            SpiderDifficulty.TWO_SUIT,
            SpiderDifficulty.FOUR_SUIT,
        ]

        for diff in difficulties:
            random.seed(42 + diff.value)
            game = SpiderGame(difficulty=diff, seed=100 + diff.value)
            self._assert_spider_invariants(game, f"initial {diff.name}")

            moves_executed = 0
            undos_executed = 0
            redos_executed = 0

            for step in range(250):
                self._assert_spider_invariants(game, f"{diff.name} step {step}")

                action = random.random()
                if action < 0.20 and game.can_undo:
                    self.assertTrue(game.undo())
                    undos_executed += 1
                elif action < 0.35 and game.can_redo:
                    self.assertTrue(game.redo())
                    redos_executed += 1
                else:
                    legal_moves = game.get_legal_moves()
                    if not legal_moves:
                        if game.can_undo:
                            self.assertTrue(game.undo())
                            undos_executed += 1
                        else:
                            break
                    else:
                        move = random.choice(legal_moves)
                        res = game.make_move(move)
                        self.assertTrue(
                            res.success,
                            f"Legal move {move} failed in {diff.name}: {res.error_message}"
                        )
                        moves_executed += 1

            self._assert_spider_invariants(game, f"{diff.name} finished")
            self.assertGreater(moves_executed, 100)

    def test_spider_100_moves_walk_with_exact_undo_redo_invariance(self):
        """TC-SP-STRESS-02: Execute 100 sequential legal moves/deals in Spider, then 100 undos
        -> verify exact board state equality with initial deal. Repeat with 100 redos ->
        verify exact board state equality with post-walk state.
        """
        for diff in [SpiderDifficulty.ONE_SUIT, SpiderDifficulty.TWO_SUIT, SpiderDifficulty.FOUR_SUIT]:
            random.seed(555 + diff.value)
            game = SpiderGame(difficulty=diff, seed=777 + diff.value)
            initial_snap = game.get_state_snapshot()

            moves_count = 0
            for step in range(100):
                legal = game.get_legal_moves()
                if not legal:
                    break
                m = random.choice(legal)
                res = game.make_move(m)
                self.assertTrue(res.success)
                moves_count += 1
                self._assert_spider_invariants(game, f"{diff.name} walk step {step}")

            walk_snap = game.get_state_snapshot()
            self.assertEqual(game.moves_count, moves_count)

            # Undo all
            for _ in range(moves_count):
                self.assertTrue(game.can_undo)
                self.assertTrue(game.undo())

            undone_snap = game.get_state_snapshot()
            self.assertEqual(
                undone_snap["piles"], initial_snap["piles"],
                f"Spider {diff.name} piles after undos mismatch initial deal!"
            )
            self.assertEqual(game.moves_count, 0)
            self.assertEqual(game.score, 500)
            self.assertFalse(game.can_undo)

            # Redo all
            for _ in range(moves_count):
                self.assertTrue(game.can_redo)
                self.assertTrue(game.redo())

            redone_snap = game.get_state_snapshot()
            self.assertEqual(
                redone_snap["piles"], walk_snap["piles"],
                f"Spider {diff.name} piles after redos mismatch post-walk state!"
            )
            self.assertEqual(game.moves_count, moves_count)
            self.assertFalse(game.can_redo)

    def test_spider_rapid_stock_deals_and_undo_redo(self):
        """TC-SP-STRESS-03: Execute all 5 stock deals (50 cards), then undo all 5 deals
        -> verify complete restoration of stock and tableau. Redo all 5 deals -> verify depletion.
        """
        game = SpiderGame(difficulty=SpiderDifficulty.ONE_SUIT, seed=42)
        initial_snap = game.get_state_snapshot()
        self.assertEqual(len(game.stock), 50)
        self.assertEqual(game.deals_remaining, 5)

        # Perform 5 stock deals
        for deal_num in range(5):
            res = game.deal_stock()
            self.assertTrue(res.success, f"Deal {deal_num} failed: {res.error_message}")
            self.assertEqual(len(game.stock), 50 - (deal_num + 1) * 10)
            self._assert_spider_invariants(game, f"after deal {deal_num}")

        self.assertEqual(len(game.stock), 0)
        self.assertEqual(game.deals_remaining, 0)
        five_deal_snap = game.get_state_snapshot()

        # Undo all 5 deals
        for deal_num in range(5):
            self.assertTrue(game.undo())
            self.assertEqual(len(game.stock), (deal_num + 1) * 10)

        undone_snap = game.get_state_snapshot()
        self.assertEqual(undone_snap["piles"], initial_snap["piles"])
        self.assertEqual(len(game.stock), 50)
        self.assertEqual(game.deals_remaining, 5)

        # Redo all 5 deals
        for deal_num in range(5):
            self.assertTrue(game.redo())

        redone_snap = game.get_state_snapshot()
        self.assertEqual(redone_snap["piles"], five_deal_snap["piles"])
        self.assertEqual(len(game.stock), 0)

    def test_spider_completed_run_clearing_stress_and_undo_redo(self):
        """TC-SP-STRESS-04: Atomic run clearance to foundation, score tracking (+100),
        and fog-of-war rollback re-hiding uncovered card.
        """
        game = SpiderGame(difficulty=SpiderDifficulty.ONE_SUIT, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # In tableau 0: 1 face-down card + K down to 2 Spades (12 cards)
        face_down_c = Card(Suit.SPADES, Rank.KING, is_face_up=False, card_id=103)
        game.tableau[0].push(face_down_c)
        for r in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, Rank(r), is_face_up=True, card_id=r))

        # In tableau 1: Ace of Spades (1 card)
        game.tableau[1].push(Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=1))

        initial_score = game.score
        initial_runs = game.completed_runs
        self.assertEqual(initial_runs, 0)

        # Move Ace of Spades from tableau 1 to tableau 0 -> completes 13-card run
        m = Move("tableau_1", "tableau_0", card_id=1)
        res = game.make_move(m)
        self.assertTrue(res.success)

        # Verification: run cleared atomically to foundation 0, underlying card auto-flipped face up
        self.assertEqual(game.completed_runs, 1)
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertTrue(game.tableau[0].peek().is_face_up)
        self.assertEqual(game.score, initial_score - 1 + 100)

        # Undo move: run restored to tableau 0, foundation 0 empty, underlying card re-hidden
        self.assertTrue(game.undo())
        self.assertEqual(game.completed_runs, 0)
        self.assertEqual(len(game.foundations[0]), 0)
        self.assertEqual(len(game.tableau[0]), 13)
        self.assertFalse(game.tableau[0][0].is_face_up, "Underlying card was not re-hidden on undo!")
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.score, initial_score)

        # Redo move: run re-cleared, underlying card re-flipped, score re-added
        self.assertTrue(game.redo())
        self.assertEqual(game.completed_runs, 1)
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertTrue(game.tableau[0].peek().is_face_up)
        self.assertEqual(game.score, initial_score - 1 + 100)


class TestFuzzInvalidMoves(unittest.TestCase):
    """Target 3: Exhaustive fuzzing and rejection of invalid Move objects with zero exceptions."""

    def test_freecell_fuzz_invalid_move_objects(self):
        """TC-FC-FUZZ-01: Arbitrary invalid Move objects rejected by FreeCell with MoveResult.fail."""
        game = FreeCellGame(seed=42)
        snap_before = game.get_state_snapshot()

        malformed_moves = [
            None,
            Move(None, None),
            Move("", ""),
            Move("nonexistent_pile", "cascade_0"),
            Move("cascade_0", "nonexistent_pile"),
            Move("cascade_99", "cascade_0"),
            Move("cascade_0", "cascade_99"),
            Move("freecell_99", "cascade_0"),
            Move("cascade_0", "freecell_99"),
            Move("foundation_99", "cascade_0"),
            Move("cascade_0", "foundation_99"),
            Move("stock", "cascade_0"),
            Move("cascade_0", "waste"),
            Move("cascade_0", "cascade_0"),
            Move("cascade_0", "cascade_1", card_count=-1),
            Move("cascade_0", "cascade_1", card_count=-10),
            Move("cascade_0", "cascade_1", card_count=0),
            Move("cascade_0", "cascade_1", card_count=999),
            Move("cascade_0", "cascade_1", card_id=-1),
            Move("cascade_0", "cascade_1", card_id=-999),
            Move("cascade_0", "cascade_1", card_id=52),
            Move("cascade_0", "cascade_1", card_id=99999),
            Move("cascade_0", "freecell_0", card_count=2),
            Move("cascade_0", "foundation_0", card_count=2),
            Move("freecell_0", "cascade_0"),  # empty freecell
        ]

        for m in malformed_moves:
            try:
                res = game.make_move(m)
                self.assertFalse(
                    res.success,
                    f"Expected move {m} to be rejected, but it succeeded!"
                )
                self.assertTrue(
                    len(res.error_message) > 0,
                    f"Expected error message for rejected move {m}"
                )
            except Exception as e:
                self.fail(f"FreeCell make_move({m}) raised unhandled exception: {type(e)}: {e}")

            # Verify is_legal_move also returns False gracefully
            try:
                is_legal = game.is_legal_move(m)
                self.assertFalse(is_legal, f"is_legal_move({m}) returned True for invalid move")
            except Exception as e:
                self.fail(f"FreeCell is_legal_move({m}) raised unhandled exception: {type(e)}: {e}")

        # State must remain 100% identical after all rejected moves
        self.assertEqual(game.get_state_snapshot(), snap_before)

    def test_spider_fuzz_invalid_move_objects(self):
        """TC-SP-FUZZ-01: Arbitrary invalid Move objects rejected by Spider with MoveResult.fail."""
        game = SpiderGame(difficulty=SpiderDifficulty.ONE_SUIT, seed=42)
        snap_before = game.get_state_snapshot()

        malformed_moves = [
            None,
            Move(None, None),
            Move("", ""),
            Move("nonexistent_pile", "tableau_0"),
            Move("tableau_0", "nonexistent_pile"),
            Move("tableau_99", "tableau_0"),
            Move("tableau_0", "tableau_99"),
            Move("freecell_0", "tableau_0"),
            Move("tableau_0", "freecell_0"),
            Move("tableau_0", "tableau_0"),
            Move("tableau_0", "tableau_1", card_count=-1),
            Move("tableau_0", "tableau_1", card_count=-10),
            Move("tableau_0", "tableau_1", card_count=0),
            Move("tableau_0", "tableau_1", card_count=999),
            Move("tableau_0", "tableau_1", card_id=-1),
            Move("tableau_0", "tableau_1", card_id=-999),
            Move("tableau_0", "tableau_1", card_id=104),
            Move("tableau_0", "tableau_1", card_id=99999),
            Move("tableau_0", "tableau_1", card_count=5),  # exceeds face-up cards
        ]

        for m in malformed_moves:
            try:
                res = game.make_move(m)
                self.assertFalse(
                    res.success,
                    f"Expected move {m} to be rejected, but it succeeded!"
                )
                self.assertTrue(
                    len(res.error_message) > 0,
                    f"Expected error message for rejected move {m}"
                )
            except Exception as e:
                self.fail(f"Spider make_move({m}) raised unhandled exception: {type(e)}: {e}")

            try:
                is_legal = game.is_legal_move(m)
                self.assertFalse(is_legal, f"is_legal_move({m}) returned True for invalid move")
            except Exception as e:
                self.fail(f"Spider is_legal_move({m}) raised unhandled exception: {type(e)}: {e}")

        self.assertEqual(game.get_state_snapshot(), snap_before)

    def test_spider_deal_stock_empty_column_guard_strict_rejection(self):
        """TC-SP-FUZZ-02: Spider dealing is strictly blocked if any column is empty."""
        game = SpiderGame(difficulty=SpiderDifficulty.ONE_SUIT, seed=42)
        game.tableau[4].clear()
        self.assertTrue(game.tableau[4].is_empty)

        snap_before = game.get_state_snapshot()
        res = game.deal_stock()
        self.assertFalse(res.success)
        self.assertIn("empty", res.error_message.lower())
        self.assertEqual(game.get_state_snapshot(), snap_before)

    def test_spider_mixed_suit_sequence_drag_rejected(self):
        """TC-SP-FUZZ-03: Spider multi-card stack with mixed suits must be rejected."""
        game = SpiderGame(difficulty=SpiderDifficulty.FOUR_SUIT, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Tableau 0: 7♠, 6♥ (descending numerical ranks, but DIFFERENT suits)
        game.tableau[0].push(Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=10))
        game.tableau[0].push(Card(Suit.HEARTS, Rank.SIX, is_face_up=True, card_id=20))

        # Tableau 1: 8♦
        game.tableau[1].push(Card(Suit.DIAMONDS, Rank.EIGHT, is_face_up=True, card_id=30))

        # Attempt to transfer the 2-card mixed sequence [7♠, 6♥]
        res = game.make_move(Move("tableau_0", "tableau_1", card_count=2))
        self.assertFalse(res.success)
        self.assertTrue(
            "single-suit" in res.error_message.lower() or "same suit" in res.error_message.lower()
        )

    def test_arbitrary_fuzzer_1000_moves_zero_exceptions_and_state_preservation(self):
        """TC-FUZZ-04: Fuzz 1,000 randomized arbitrary Move objects across active boards
        verifying zero crashes and exact state preservation on rejections.
        """
        random.seed(888)
        fc_game = FreeCellGame(seed=42)
        sp_game = SpiderGame(difficulty=SpiderDifficulty.TWO_SUIT, seed=42)

        fc_piles = list(fc_game.piles.keys()) + ["garbage_pile", "cascade_99", "freecell_99", ""]
        sp_piles = list(sp_game.piles.keys()) + ["garbage_pile", "tableau_99", "foundation_99", ""]

        for _ in range(500):
            # FreeCell fuzz
            fc_m = Move(
                source_pile_id=random.choice(fc_piles),
                dest_pile_id=random.choice(fc_piles),
                card_id=random.choice([None, -1, 0, 51, 52, 999, random.randint(-50, 100)]),
                card_count=random.choice([-5, -1, 0, 1, 2, 8, 53, random.randint(-10, 20)]),
            )
            fc_snap = fc_game.get_state_snapshot()
            try:
                res = fc_game.make_move(fc_m)
                if not res.success:
                    self.assertEqual(fc_game.get_state_snapshot(), fc_snap)
            except Exception as e:
                self.fail(f"FreeCell fuzzer crashed on {fc_m}: {type(e)}: {e}")

            # Spider fuzz
            sp_m = Move(
                source_pile_id=random.choice(sp_piles),
                dest_pile_id=random.choice(sp_piles),
                card_id=random.choice([None, -1, 0, 103, 104, 999, random.randint(-50, 200)]),
                card_count=random.choice([-5, -1, 0, 1, 2, 10, 105, random.randint(-10, 20)]),
            )
            sp_snap = sp_game.get_state_snapshot()
            try:
                res = sp_game.make_move(sp_m)
                if not res.success:
                    self.assertEqual(sp_game.get_state_snapshot(), sp_snap)
            except Exception as e:
                self.fail(f"Spider fuzzer crashed on {sp_m}: {type(e)}: {e}")


class TestAdversarialChallengeReproductions(unittest.TestCase):
    """Adversarial Challenge Findings: Cross-pile move validation vulnerabilities in M2 engines."""

    def test_defect1_spider_reject_manual_card_move_to_foundation(self):
        """DEFECT 1 (Spider): make_move allows manually moving individual cards from tableau
        to foundation piles! Foundations in Spider MUST ONLY accept completed 13-card runs
        via internal run clearance commands.
        """
        game = SpiderGame(difficulty=SpiderDifficulty.ONE_SUIT, seed=42)
        top_card = game.tableau[0].peek()

        # In Spider Solitaire, foundation piles are NOT destinations for manual player moves!
        # Calling make_move with destination 'foundation_0' MUST be rejected.
        m = Move(source_pile_id="tableau_0", dest_pile_id="foundation_0", card_id=top_card.card_id)
        res = game.make_move(m)

        self.assertFalse(
            res.success,
            f"VULNERABILITY: Spider make_move allowed manual transfer of {top_card} "
            f"to foundation_0! Foundation now contains {len(game.foundations[0])} cards."
        )

    def test_defect2_spider_reject_card_move_from_foundation_to_tableau(self):
        """DEFECT 2 (Spider): make_move allows moving cards from foundation piles to tableau!
        Once cards are placed in a Spider foundation, they are permanently locked.
        """
        game = SpiderGame(difficulty=SpiderDifficulty.ONE_SUIT, seed=42)
        game.tableau[0].clear()
        game.foundations[0].push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=99))

        m = Move(source_pile_id="foundation_0", dest_pile_id="tableau_0", card_id=99)
        res = game.make_move(m)

        self.assertFalse(
            res.success,
            "VULNERABILITY: Spider make_move allowed moving cards OUT of foundation_0 to tableau_0!"
        )

    def test_defect3_spider_reject_tableau_move_to_stock(self):
        """DEFECT 3 (Spider): make_move allows transferring tableau cards onto the stock pile
        if ranks happen to match!
        """
        game = SpiderGame(difficulty=SpiderDifficulty.ONE_SUIT, seed=42)
        game.stock.clear()
        game.stock.push(Card(Suit.SPADES, Rank.EIGHT, is_face_up=False, card_id=99))

        game.tableau[0].clear()
        game.tableau[0].push(Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=100))

        m = Move(source_pile_id="tableau_0", dest_pile_id="stock", card_id=100)
        res = game.make_move(m)

        self.assertFalse(
            res.success,
            "VULNERABILITY: Spider make_move allowed moving tableau cards onto the stock pile!"
        )

    def test_defect4_freecell_reject_card_move_between_foundations(self):
        """DEFECT 4 (FreeCell): make_move allows transferring cards between foundation piles,
        corrupting single-suit foundation ordering!
        """
        game = FreeCellGame(seed=42)
        game.foundations[0].push(Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=98))
        game.foundations[1].push(Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=99))

        # Attempt to move 8♠ from foundation_0 to foundation_1 (which has 9♥)
        m = Move(source_pile_id="foundation_0", dest_pile_id="foundation_1", card_id=98)
        res = game.make_move(m)

        self.assertFalse(
            res.success,
            f"VULNERABILITY: FreeCell allowed moving cards between foundations! "
            f"Foundation 1 now contains mixed suits: {game.foundations[1].cards}"
        )

    def test_defect5_freecell_reject_foundation_demotion_to_freecell_by_default(self):
        """DEFECT 5 (FreeCell): When allow_foundation_demotion=False (default), cards cannot
        be moved from foundations to free cells!
        """
        game = FreeCellGame(seed=42, allow_foundation_demotion=False)
        game.foundations[0].push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=98))

        m = Move(source_pile_id="foundation_0", dest_pile_id="freecell_0", card_id=98)
        res = game.make_move(m)

        self.assertFalse(
            res.success,
            "VULNERABILITY: FreeCell allowed foundation demotion to freecell when "
            "allow_foundation_demotion=False!"
        )


if __name__ == "__main__":
    unittest.main()
