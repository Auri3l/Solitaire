"""Empirical Invariance, Fog-of-War, and Redo Consistency Test Suite.

Author: teamwork_preview_challenger_m1_2
Scope: Milestone 1 mathematical verification and stress testing.
"""

import unittest
import random
from typing import List, Dict, Any, Tuple, Optional

from solitaire.core.card import Card, Suit, Rank, Color
from solitaire.core.pile import PileType, Pile, Deck
from solitaire.core.commands import (
    Command,
    CardMoveCommand,
    StockDealCommand,
    RecycleCommand,
    CommandHistory,
)
from solitaire.core.base_game import BaseGame, GameStatus, Move, MoveResult
from solitaire.games.klondike import KlondikeGame, MoveType, ScoringMode


class TestEmpiricalInvarianceWalks(unittest.TestCase):
    """1. Invariance check: Apply(Delta^-1, Apply(Delta, S)) == S.
    Execute property-based random walks of 100 steps followed by 100 undos
    across 10 distinct seeds. Verify that final state matches initial state
    bit-for-bit with 0 score drift.
    """

    def _assert_states_identical(self, state_a: Dict[str, Any], state_b: Dict[str, Any], msg_prefix: str = "") -> None:
        """Deep comparison of two game snapshots ensuring bit-for-bit equality."""
        self.assertEqual(state_a["mode_name"], state_b["mode_name"], f"{msg_prefix} mode mismatch")
        self.assertEqual(state_a["seed"], state_b["seed"], f"{msg_prefix} seed mismatch")
        self.assertEqual(state_a["score"], state_b["score"], f"{msg_prefix} score mismatch (score drift detected!)")
        self.assertEqual(state_a["moves_count"], state_b["moves_count"], f"{msg_prefix} moves_count mismatch")
        self.assertEqual(state_a["recycles_count"], state_b["recycles_count"], f"{msg_prefix} recycles_count mismatch")
        self.assertEqual(state_a["passes_through_stock"], state_b["passes_through_stock"], f"{msg_prefix} passes_through_stock mismatch")
        self.assertEqual(state_a["is_won"], state_b["is_won"], f"{msg_prefix} is_won mismatch")

        piles_a = state_a["piles"]
        piles_b = state_b["piles"]
        self.assertEqual(set(piles_a.keys()), set(piles_b.keys()), f"{msg_prefix} pile keys mismatch")

        for pid in piles_a:
            p_a = piles_a[pid]
            p_b = piles_b[pid]
            self.assertEqual(p_a["pile_id"], p_b["pile_id"])
            self.assertEqual(p_a["pile_type"], p_b["pile_type"])
            self.assertEqual(p_a["index"], p_b["index"])
            cards_a = p_a["cards"]
            cards_b = p_b["cards"]
            self.assertEqual(len(cards_a), len(cards_b), f"{msg_prefix} pile {pid} card count mismatch")
            for idx, (ca, cb) in enumerate(zip(cards_a, cards_b)):
                self.assertEqual(ca["card_id"], cb["card_id"], f"{msg_prefix} pile {pid} card {idx} id mismatch")
                self.assertEqual(ca["suit"], cb["suit"], f"{msg_prefix} pile {pid} card {idx} suit mismatch")
                self.assertEqual(ca["rank"], cb["rank"], f"{msg_prefix} pile {pid} card {idx} rank mismatch")
                self.assertEqual(ca["is_face_up"], cb["is_face_up"], f"{msg_prefix} pile {pid} card {idx} face_up mismatch (fog-of-war drift!)")

    def test_turn1_100_step_random_walks_10_seeds(self):
        """Turn 1: 100 steps + 100 undos across 10 distinct seeds with 0 score drift."""
        seeds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        for seed in seeds:
            game = KlondikeGame(turn_mode=1, seed=seed)
            initial_snap = game.get_state_snapshot()
            rng = random.Random(seed)

            # 100 forward steps
            for step in range(100):
                legal_moves = game.get_legal_moves()
                self.assertTrue(len(legal_moves) > 0, f"Deadlock at step {step} for seed {seed}")
                move = rng.choice(legal_moves)
                res = game.make_move(move)
                self.assertTrue(res.success, f"Move failed at step {step} for seed {seed}: {res.error_message}")

            self.assertEqual(game.moves_count, 100)
            self.assertTrue(game.can_undo())

            # 100 backward undos
            for step in range(100):
                self.assertTrue(game.can_undo(), f"can_undo False at undo step {step} for seed {seed}")
                res = game.undo()
                self.assertTrue(res, f"undo failed at step {step} for seed {seed}")

            self.assertFalse(game.can_undo())
            self.assertEqual(game.moves_count, 0)
            self.assertEqual(game.score, 0, f"Score drift detected for seed {seed}: score={game.score}")

            final_snap = game.get_state_snapshot()
            self._assert_states_identical(initial_snap, final_snap, msg_prefix=f"[Seed {seed}]")

    def test_turn3_100_step_random_walks_10_seeds(self):
        """Turn 3: 100 steps + 100 undos across 10 distinct seeds with remainder deals and recycles."""
        seeds = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]
        for seed in seeds:
            game = KlondikeGame(turn_mode=3, seed=seed)
            initial_snap = game.get_state_snapshot()
            rng = random.Random(seed)

            for step in range(100):
                legal_moves = game.get_legal_moves()
                self.assertTrue(len(legal_moves) > 0, f"Deadlock at step {step} for Turn 3 seed {seed}")
                move = rng.choice(legal_moves)
                res = game.make_move(move)
                self.assertTrue(res.success, f"Move failed at step {step} for Turn 3 seed {seed}: {res.error_message}")

            self.assertEqual(game.moves_count, 100)

            for step in range(100):
                self.assertTrue(game.can_undo())
                self.assertTrue(game.undo())

            self.assertFalse(game.can_undo())
            self.assertEqual(game.moves_count, 0)
            self.assertEqual(game.score, 0)

            final_snap = game.get_state_snapshot()
            self._assert_states_identical(initial_snap, final_snap, msg_prefix=f"[Turn 3 Seed {seed}]")

    def test_vegas_scoring_100_step_random_walks_10_seeds(self):
        """Vegas scoring: 100 steps + 100 undos across 10 seeds starting at -52."""
        seeds = [201, 202, 203, 204, 205, 206, 207, 208, 209, 210]
        for seed in seeds:
            game = KlondikeGame(scoring_mode=ScoringMode.VEGAS, seed=seed)
            initial_snap = game.get_state_snapshot()
            self.assertEqual(game.score, -52)
            rng = random.Random(seed)

            for step in range(100):
                legal_moves = game.get_legal_moves()
                move = rng.choice(legal_moves)
                res = game.make_move(move)
                self.assertTrue(res.success)

            self.assertEqual(game.moves_count, 100)

            for step in range(100):
                self.assertTrue(game.undo())

            self.assertFalse(game.can_undo())
            self.assertEqual(game.moves_count, 0)
            self.assertEqual(game.score, -52, f"Vegas score drift for seed {seed}: {game.score}")

            final_snap = game.get_state_snapshot()
            self._assert_states_identical(initial_snap, final_snap, msg_prefix=f"[Vegas Seed {seed}]")


class TestEmpiricalFogOfWar(unittest.TestCase):
    """2. Fog-of-war check: Verify that auto-uncovered face-down cards
    are strictly re-hidden to face-down on undo.
    """

    def test_fog_of_war_random_walk_dynamic_tracking(self):
        """Verify that every auto-uncovered card across 10 seeds is strictly re-hidden on undo."""
        seeds = [301, 302, 303, 304, 305, 306, 307, 308, 309, 310]
        total_uncovered_events = 0

        for seed in seeds:
            game = KlondikeGame(seed=seed)
            rng = random.Random(seed)

            # Record moves and uncoverings
            events: List[Tuple[Any, Optional[int]]] = []
            for step in range(100):
                legal = game.get_legal_moves()
                move = rng.choice(legal)
                res = game.make_move(move)
                self.assertTrue(res.success)
                cmd = res.command
                unc_id = getattr(cmd, "uncovered_card_id", None)
                if unc_id is not None:
                    # Assert card is now face-up
                    found = game.find_card(unc_id)
                    self.assertIsNotNone(found)
                    self.assertTrue(found[2].is_face_up)
                    total_uncovered_events += 1
                events.append((cmd, unc_id))

            # Undo and verify strict re-hiding
            for step in reversed(range(100)):
                cmd, unc_id = events[step]
                self.assertTrue(game.undo())
                if unc_id is not None:
                    found = game.find_card(unc_id)
                    self.assertIsNotNone(found, f"Card {unc_id} vanished during undo!")
                    pile, idx, card = found
                    self.assertFalse(
                        card.is_face_up,
                        f"FOG-OF-WAR BREACH: Card {unc_id} in pile {pile.pile_id} at {idx} was not re-hidden to face-down on undo!"
                    )

        self.assertGreater(total_uncovered_events, 0, "Expected multiple auto-uncover events across random walks")

    def test_fog_of_war_cascading_uncover_in_same_column(self):
        """Col 0 has 4 cards (bottom 3 face-down, top face-up). Each is uncovered sequentially and re-hidden on undo."""
        game = KlondikeGame(seed=42)
        for i in range(7):
            game.tableau[i].clear()

        c1 = Card(Suit.SPADES, Rank.ACE, is_face_up=False, card_id=0)
        c2 = Card(Suit.HEARTS, Rank.TWO, is_face_up=False, card_id=14)
        c3 = Card(Suit.SPADES, Rank.THREE, is_face_up=False, card_id=2)
        c4 = Card(Suit.HEARTS, Rank.FOUR, is_face_up=True, card_id=16)
        game.tableau[0].push_many([c1, c2, c3, c4])

        # Targets with alternating colors
        game.tableau[1].push(Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4))   # Black
        game.tableau[2].push(Card(Suit.DIAMONDS, Rank.FOUR, is_face_up=True, card_id=29)) # Red
        game.tableau[3].push(Card(Suit.CLUBS, Rank.THREE, is_face_up=True, card_id=41))   # Black

        snap_initial = game.get_state_snapshot()

        # Step 1: Move 4♥ onto 5♠ -> exposes 3♠
        res1 = game.make_move(Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_1", card_count=1))
        self.assertTrue(res1.success)
        self.assertTrue(c3.is_face_up)
        self.assertFalse(c2.is_face_up)
        self.assertFalse(c1.is_face_up)

        # Step 2: Move 3♠ onto 4♦ -> exposes 2♥
        res2 = game.make_move(Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_2", card_count=1))
        self.assertTrue(res2.success)
        self.assertTrue(c2.is_face_up)
        self.assertFalse(c1.is_face_up)

        # Step 3: Move 2♥ onto 3♣ -> exposes 1♠ (Ace)
        res3 = game.make_move(Move(MoveType.TABLEAU_TO_TABLEAU, "tableau_0", "tableau_3", card_count=1))
        self.assertTrue(res3.success)
        self.assertTrue(c1.is_face_up)

        # Undo 3: 2♥ returns to col 0 -> 1♠ strictly re-hidden
        self.assertTrue(game.undo())
        self.assertFalse(c1.is_face_up)
        self.assertTrue(c2.is_face_up)

        # Undo 2: 3♠ returns to col 0 -> 2♥ strictly re-hidden
        self.assertTrue(game.undo())
        self.assertFalse(c1.is_face_up)
        self.assertFalse(c2.is_face_up)
        self.assertTrue(c3.is_face_up)

        # Undo 1: 4♥ returns to col 0 -> 3♠ strictly re-hidden
        self.assertTrue(game.undo())
        self.assertFalse(c1.is_face_up)
        self.assertFalse(c2.is_face_up)
        self.assertFalse(c3.is_face_up)
        self.assertTrue(c4.is_face_up)

        self.assertEqual(game.get_state_snapshot(), snap_initial)

    def test_fog_of_war_tableau_to_foundation_uncover(self):
        """Moving Ace to foundation uncovers card underneath. Undo strictly re-hides it."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()

        c_down = Card(Suit.HEARTS, Rank.SEVEN, is_face_up=False, card_id=19)
        c_ace = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[0].push_many([c_down, c_ace])

        snap_pre = game.get_state_snapshot()
        res = game.make_move(Move(MoveType.TABLEAU_TO_FOUNDATION, "tableau_0", "foundation_0", card_count=1))
        self.assertTrue(res.success)
        self.assertTrue(c_down.is_face_up)

        # Undo
        self.assertTrue(game.undo())
        self.assertFalse(c_down.is_face_up)
        self.assertTrue(c_ace.is_face_up)
        self.assertEqual(game.get_state_snapshot(), snap_pre)

        # Redo
        self.assertTrue(game.redo())
        self.assertTrue(c_down.is_face_up)

        # Undo again
        self.assertTrue(game.undo())
        self.assertFalse(c_down.is_face_up)
        self.assertEqual(game.get_state_snapshot(), snap_pre)


class TestEmpiricalRedoConsistency(unittest.TestCase):
    """3. Redo consistency: Verify that undo followed by redo produces
    identical state to forward execution.
    """

    def test_single_step_undo_redo_all_100_steps_10_seeds(self):
        """At EVERY step of 100-step walk across 10 seeds: undo restores previous, redo restores forward."""
        seeds = [401, 402, 403, 404, 405, 406, 407, 408, 409, 410]
        for seed in seeds:
            game = KlondikeGame(seed=seed)
            rng = random.Random(seed)

            for step in range(100):
                snap_before = game.get_state_snapshot()
                legal = game.get_legal_moves()
                move = rng.choice(legal)
                res = game.make_move(move)
                self.assertTrue(res.success)
                snap_after = game.get_state_snapshot()

                # Undo step
                self.assertTrue(game.undo())
                self.assertEqual(game.get_state_snapshot(), snap_before, f"Single-step undo failed at step {step}, seed {seed}")

                # Redo step
                self.assertTrue(game.redo())
                self.assertEqual(game.get_state_snapshot(), snap_after, f"Single-step redo failed at step {step}, seed {seed}")

    def test_full_100_step_rollback_and_rollforward_10_seeds(self):
        """Record 100 states. Undo all 100 asserting exact intermediate match. Redo all 100 asserting exact match."""
        seeds = [501, 502, 503, 504, 505, 506, 507, 508, 509, 510]
        for seed in seeds:
            game = KlondikeGame(seed=seed)
            rng = random.Random(seed)

            states = [game.get_state_snapshot()]
            for step in range(100):
                legal = game.get_legal_moves()
                move = rng.choice(legal)
                res = game.make_move(move)
                self.assertTrue(res.success)
                states.append(game.get_state_snapshot())

            # Roll back all 100
            for k in range(100, 0, -1):
                self.assertTrue(game.can_undo())
                self.assertTrue(game.undo())
                self.assertEqual(game.get_state_snapshot(), states[k - 1])

            self.assertFalse(game.can_undo())

            # Roll forward all 100
            for k in range(1, 101):
                self.assertTrue(game.can_redo())
                self.assertTrue(game.redo())
                self.assertEqual(game.get_state_snapshot(), states[k])

            self.assertFalse(game.can_redo())

    def test_interleaved_oracle_tracking_turn1_10_seeds(self):
        """250 interleaved actions per seed (move, undo, redo) tracking shadow oracle stack in Turn 1."""
        seeds = [601, 602, 603, 604, 605, 606, 607, 608, 609, 610]
        for seed in seeds:
            game = KlondikeGame(turn_mode=1, seed=seed)
            rng = random.Random(seed)

            oracle = [game.get_state_snapshot()]
            pointer = 0

            for action_i in range(250):
                choices = ["move"]
                if game.can_undo():
                    choices.append("undo")
                if game.can_redo():
                    choices.append("redo")

                act = rng.choices(choices, weights=[0.6 if c == "move" else 0.2 for c in choices])[0]
                if act == "move":
                    legal = game.get_legal_moves()
                    if not legal:
                        continue
                    move = rng.choice(legal)
                    res = game.make_move(move)
                    self.assertTrue(res.success)
                    oracle = oracle[:pointer + 1]
                    oracle.append(game.get_state_snapshot())
                    pointer += 1
                elif act == "undo":
                    self.assertTrue(game.undo())
                    pointer -= 1
                    self.assertEqual(game.get_state_snapshot(), oracle[pointer])
                elif act == "redo":
                    self.assertTrue(game.redo())
                    pointer += 1
                    self.assertEqual(game.get_state_snapshot(), oracle[pointer])

            # Final complete rollback to start
            while game.can_undo():
                self.assertTrue(game.undo())
                pointer -= 1
                self.assertEqual(game.get_state_snapshot(), oracle[pointer])

            self.assertEqual(pointer, 0)
            self.assertEqual(game.get_state_snapshot(), oracle[0])

    def test_interleaved_oracle_tracking_turn3_10_seeds(self):
        """250 interleaved actions per seed tracking shadow oracle stack in Turn 3."""
        seeds = [701, 702, 703, 704, 705, 706, 707, 708, 709, 710]
        for seed in seeds:
            game = KlondikeGame(turn_mode=3, seed=seed)
            rng = random.Random(seed)

            oracle = [game.get_state_snapshot()]
            pointer = 0

            for action_i in range(250):
                choices = ["move"]
                if game.can_undo():
                    choices.append("undo")
                if game.can_redo():
                    choices.append("redo")

                act = rng.choices(choices, weights=[0.6 if c == "move" else 0.2 for c in choices])[0]
                if act == "move":
                    legal = game.get_legal_moves()
                    if not legal:
                        continue
                    move = rng.choice(legal)
                    res = game.make_move(move)
                    self.assertTrue(res.success)
                    oracle = oracle[:pointer + 1]
                    oracle.append(game.get_state_snapshot())
                    pointer += 1
                elif act == "undo":
                    self.assertTrue(game.undo())
                    pointer -= 1
                    self.assertEqual(game.get_state_snapshot(), oracle[pointer])
                elif act == "redo":
                    self.assertTrue(game.redo())
                    pointer += 1
                    self.assertEqual(game.get_state_snapshot(), oracle[pointer])

            while game.can_undo():
                self.assertTrue(game.undo())
                pointer -= 1
                self.assertEqual(game.get_state_snapshot(), oracle[pointer])

            self.assertEqual(pointer, 0)
            self.assertEqual(game.get_state_snapshot(), oracle[0])


class TestEmpiricalScoringZeroDriftUnderClamping(unittest.TestCase):
    """Stress tests on score clamping at 0 to guarantee zero score drift."""

    def test_recycle_penalty_full_and_partial_clamping(self):
        # Full clamping at 0
        g1 = KlondikeGame(turn_mode=1, seed=42)
        g1.score = 0
        for _ in range(24):
            g1.deal_stock()
        s_pre1 = g1.get_state_snapshot()
        g1.deal_stock() # Recycle with -100 penalty
        self.assertEqual(g1.score, 0)
        self.assertTrue(g1.undo())
        self.assertEqual(g1.score, 0)
        self.assertEqual(g1.get_state_snapshot(), s_pre1)

        # Partial clamping: score 40 - 100 -> 0 (actual delta -40)
        g2 = KlondikeGame(turn_mode=1, seed=42)
        g2.score = 40
        for _ in range(24):
            g2.deal_stock()
        s_pre2 = g2.get_state_snapshot()
        g2.deal_stock()
        self.assertEqual(g2.score, 0)
        self.assertTrue(g2.undo())
        self.assertEqual(g2.score, 40)
        self.assertEqual(g2.get_state_snapshot(), s_pre2)

        # Redo after partial clamping
        self.assertTrue(g2.redo())
        self.assertEqual(g2.score, 0)
        self.assertTrue(g2.undo())
        self.assertEqual(g2.score, 40)
        self.assertEqual(g2.get_state_snapshot(), s_pre2)


if __name__ == "__main__":
    unittest.main()
