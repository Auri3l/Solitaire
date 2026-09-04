"""Tier 2 Boundary Value Analysis: FreeCell Supermove Extremal Thresholds.

Verifies exact inductive boundary conditions for multi-card cascade movements:
- Target non-empty: M = (1 + N) * 2^K
  - Moving M cards succeeds; moving M + 1 cards is strictly rejected.
- Target empty: M = (1 + N) * 2^(K - 1)
  - Moving M cards succeeds; moving M + 1 cards is strictly rejected.
- N = 0, K = 0 lower bound (single card only).
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move
from solitaire.games.freecell import FreeCellGame


class TestFreeCellSupermoveBoundaries(unittest.TestCase):
    """BVA: Exact mathematical thresholds of FreeCell supermove formulas."""

    def _setup_board_with_caps(self, empty_cells_count: int, empty_cascades_count: int) -> FreeCellGame:
        """Configures a FreeCellGame with exact N empty freecells and K empty cascades."""
        game = FreeCellGame(seed=42)
        # 1. Fill 4 - N free cells
        for i in range(4):
            game.free_cells[i].clear()
            if i >= empty_cells_count:
                game.free_cells[i].push(Card(Suit.CLUBS, i + 1, is_face_up=True, card_id=40 + i))

        # 2. Clear cascades 0 and 1 for test staging
        game.cascades[0].clear()
        game.cascades[1].clear()

        # 3. Handle cascades 2-7
        # We need empty_cascades_count empty cascades total across the board
        # If target (cascade 0) is empty, it counts towards empty cascades.
        # But here let's configure remaining cascades 2..7:
        for idx in range(2, 8):
            game.cascades[idx].clear()
            # If we need more empty cascades, leave empty, otherwise push a dummy blocker
            # Currently empty cascades count includes 0, 1 and however many among 2..7 we leave empty.
            game.cascades[idx].push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=60 + idx))

        return game

    def test_n0_k0_boundary_to_nonempty_cascade(self) -> None:
        """TC-BVA-SM-01: (N=0, K=0) -> Max M=1. Moving 1 card succeeds, moving 2 cards fails."""
        game = FreeCellGame(seed=42)
        # All 4 free cells occupied
        for i, fc in enumerate(game.free_cells):
            fc.clear()
            fc.push(Card(Suit.CLUBS, i + 1, is_face_up=True, card_id=40 + i))

        # Ensure all cascades 0-7 are non-empty
        # Target: Cascade 0 (King of Spades)
        game.cascades[0].clear()
        k_s = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        game.cascades[0].push(k_s)

        # Source: Cascade 1 has Queen of Hearts and Jack of Clubs
        game.cascades[1].clear()
        q_h = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        j_c = Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        game.cascades[1].push_many([q_h, j_c])

        self.assertEqual(game.get_empty_freecell_count(), 0)
        self.assertEqual(game.get_empty_cascade_count(), 0)
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=False), 1)

        # Moving 2 cards (M+1) must fail
        res_fail = game.make_move(Move("cascade_1", "cascade_0", card_id=q_h.card_id, card_count=2))
        self.assertFalse(res_fail.success)

        # Moving 1 card (top card j_c, if valid) or moving single card within capacity:
        # j_c cannot go on k_s, but capacity check is verified by failure on count=2
        # Let's verify moving 1 card with matching rank:
        game.cascades[1].clear()
        game.cascades[1].push(q_h)
        res_ok = game.make_move(Move("cascade_1", "cascade_0", card_id=q_h.card_id, card_count=1))
        self.assertTrue(res_ok.success)

    def test_n1_k0_boundary_to_nonempty_cascade(self) -> None:
        """TC-BVA-SM-02: (N=1, K=0) -> Max M=(1+1)*1=2. Moving 2 succeeds, moving 3 fails."""
        game = FreeCellGame(seed=42)
        # 3 cells filled, 1 empty (N=1)
        for i in range(4):
            game.free_cells[i].clear()
            if i < 3:
                game.free_cells[i].push(Card(Suit.CLUBS, i + 1, is_face_up=True, card_id=40 + i))

        # Target: Cascade 0 (King of Spades)
        game.cascades[0].clear()
        game.cascades[0].push(Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12))

        # Source: Cascade 1 has Q♥, J♣, 10♦
        game.cascades[1].clear()
        q_h = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        j_c = Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        ten_d = Card(Suit.DIAMONDS, Rank.TEN, is_face_up=True, card_id=35)
        game.cascades[1].push_many([q_h, j_c, ten_d])

        self.assertEqual(game.get_empty_freecell_count(), 1)
        self.assertEqual(game.get_empty_cascade_count(), 0)
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=False), 2)

        # Attempt moving 3 cards (M+1) -> strictly rejected!
        res3 = game.make_move(Move("cascade_1", "cascade_0", card_id=q_h.card_id, card_count=3))
        self.assertFalse(res3.success)

        # Attempt moving 2 cards (M=2) starting from red Jack onto Black Queen:
        game.cascades[0].clear()
        q_black = Card(Suit.SPADES, Rank.QUEEN, is_face_up=True, card_id=11)
        game.cascades[0].push(q_black)

        game.cascades[1].clear()
        j_red = Card(Suit.HEARTS, Rank.JACK, is_face_up=True, card_id=23)
        ten_black = Card(Suit.CLUBS, Rank.TEN, is_face_up=True, card_id=48)
        game.cascades[1].push_many([j_red, ten_black])

        res2 = game.make_move(Move("cascade_1", "cascade_0", card_id=j_red.card_id, card_count=2))
        self.assertTrue(res2.success)

    def test_n0_k1_boundary_to_empty_cascade(self) -> None:
        """TC-BVA-SM-03: (N=0, K=1) -> Target empty column itself is K=1.
        M = (1 + 0) * 2^(1 - 1) = 1. Moving 1 succeeds, moving 2 fails.
        """
        game = FreeCellGame(seed=42)
        # All 4 free cells filled (N=0)
        for i in range(4):
            game.free_cells[i].clear()
            game.free_cells[i].push(Card(Suit.CLUBS, i + 1, is_face_up=True, card_id=40 + i))

        # Cascade 0 is the ONLY empty cascade (K=1)
        game.cascades[0].clear()

        # Source: Cascade 1 has 2 valid cards
        game.cascades[1].clear()
        q_h = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        j_c = Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        game.cascades[1].push_many([q_h, j_c])

        self.assertEqual(game.get_empty_freecell_count(), 0)
        self.assertEqual(game.get_empty_cascade_count(), 1)
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=True), 1)

        # Moving 2 cards to empty column fails
        res2 = game.make_move(Move("cascade_1", "cascade_0", card_id=q_h.card_id, card_count=2))
        self.assertFalse(res2.success)

        # Moving single card (q_h) to empty column succeeds
        game.cascades[1].clear()
        game.cascades[1].push(q_h)
        res1 = game.make_move(Move("cascade_1", "cascade_0", card_id=q_h.card_id, card_count=1))
        self.assertTrue(res1.success)

    def test_n1_k1_boundary_to_empty_cascade(self) -> None:
        """TC-BVA-SM-04: (N=1, K=1) -> Target empty cascade is K=1.
        M = (1 + 1) * 2^(1 - 1) = 2. Moving 2 succeeds, moving 3 fails.
        """
        game = FreeCellGame(seed=42)
        # 3 cells filled, 1 empty (N=1)
        for i in range(4):
            game.free_cells[i].clear()
            if i < 3:
                game.free_cells[i].push(Card(Suit.CLUBS, i + 1, is_face_up=True, card_id=40 + i))

        # Cascade 0 is empty (K=1)
        game.cascades[0].clear()

        # Source: 3 cards
        game.cascades[1].clear()
        q_h = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        j_c = Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        ten_d = Card(Suit.DIAMONDS, Rank.TEN, is_face_up=True, card_id=35)
        game.cascades[1].push_many([q_h, j_c, ten_d])

        self.assertEqual(game.get_empty_freecell_count(), 1)
        self.assertEqual(game.get_empty_cascade_count(), 1)
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=True), 2)

        # Moving 3 cards (M+1) to empty column fails
        res3 = game.make_move(Move("cascade_1", "cascade_0", card_id=q_h.card_id, card_count=3))
        self.assertFalse(res3.success)

        # Moving 2 cards (M=2) to empty column succeeds
        game.cascades[1].clear()
        game.cascades[1].push_many([j_c, ten_d])
        res2 = game.make_move(Move("cascade_1", "cascade_0", card_id=j_c.card_id, card_count=2))
        self.assertTrue(res2.success)

    def test_destination_empty_with_zero_empty_cascades(self) -> None:
        """TC-BVA-SM-05: calculate_max_supermove returns 0 when destination is empty but K=0."""
        game = FreeCellGame(seed=42)
        self.assertEqual(game.calculate_max_supermove(dest_is_empty=True, empty_cells=2, empty_cascades=0), 0)


if __name__ == "__main__":
    unittest.main()
