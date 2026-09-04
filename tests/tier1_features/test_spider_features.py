"""Tier 1 Feature Coverage: Spider Solitaire Rules Engine.

Verifies Features 15, 16, 17, 18, 19, 20, and 21:
- Feature 15: Spider Initial Deal & Stock (>= 5 tests)
- Feature 16: Spider Tableau Building (>= 5 tests)
- Feature 17: Spider Sequence Moving (>= 5 tests)
- Feature 18: Spider 13-Card Run Clearing (>= 5 tests)
- Feature 19: Spider Stock Deal Guard (>= 5 tests)
- Feature 20: Spider Empty Column Movement (>= 5 tests)
- Feature 21: Move Validation & Rejection (Spider focus) (>= 5 tests)
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move, MoveResult
from solitaire.games.spider import SpiderGame, SpiderMoveType, SpiderDifficulty


class TestSpiderInitialDealAndStock(unittest.TestCase):
    """Feature 15: Spider Initial Deal & Stock."""

    def test_total_card_count_and_columns(self) -> None:
        """TC-SPID-F15-01: Spider layout contains exactly 104 cards across 10 columns and stock."""
        game = SpiderGame(num_suits=1, seed=42)
        tab_cards = sum(len(col) for col in game.tableau)
        stock_cards = len(game.stock)
        self.assertEqual(tab_cards, 54)
        self.assertEqual(stock_cards, 50)
        self.assertEqual(tab_cards + stock_cards, 104)

    def test_initial_tableau_distribution(self) -> None:
        """TC-SPID-F15-02: Columns 0-3 have 6 cards, Columns 4-9 have 5 cards."""
        game = SpiderGame(num_suits=1, seed=42)
        for i in range(4):
            self.assertEqual(len(game.tableau[i]), 6)
        for i in range(4, 10):
            self.assertEqual(len(game.tableau[i]), 5)

    def test_initial_face_up_invariants(self) -> None:
        """TC-SPID-F15-03: Exactly 1 card is face-up per column initially (10 total)."""
        game = SpiderGame(num_suits=1, seed=42)
        total_face_up = 0
        total_face_down = 0
        for col in game.tableau:
            self.assertTrue(col.peek().is_face_up)
            for c in col[:-1]:
                self.assertFalse(c.is_face_up)
                total_face_down += 1
            total_face_up += 1
        self.assertEqual(total_face_up, 10)
        self.assertEqual(total_face_down, 44)

    def test_stock_deals_10_cards_simultaneously(self) -> None:
        """TC-SPID-F15-04: Each stock deal distributes 1 card to every column."""
        game = SpiderGame(num_suits=1, seed=42)
        initial_lengths = [len(col) for col in game.tableau]
        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.stock), 40)
        for i in range(10):
            self.assertEqual(len(game.tableau[i]), initial_lengths[i] + 1)
            self.assertTrue(game.tableau[i].peek().is_face_up)

    def test_stock_deal_reversibility(self) -> None:
        """TC-SPID-F15-05: Undoing stock deal removes 1 card from each column and returns to stock."""
        game = SpiderGame(num_suits=1, seed=42)
        top_cards = [col.peek().card_id for col in game.tableau]
        game.deal_stock()
        self.assertEqual(len(game.stock), 40)
        game.undo()
        self.assertEqual(len(game.stock), 50)
        self.assertEqual([col.peek().card_id for col in game.tableau], top_cards)


class TestSpiderTableauBuilding(unittest.TestCase):
    """Feature 16: Spider Tableau Building."""

    def test_permissive_building_same_suit(self) -> None:
        """TC-SPID-F16-01: 8 of Spades placed on 9 of Spades."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        nine_s = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        eight_s = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)
        game.tableau[0].push(nine_s)
        game.tableau[1].push(eight_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=eight_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 2)
        self.assertEqual(game.tableau[0].peek(), eight_s)

    def test_permissive_building_different_suit(self) -> None:
        """TC-SPID-F16-02: In 2-suit Spider, 8 of Hearts can be placed on 9 of Spades."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        nine_s = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        eight_h = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        game.tableau[0].push(nine_s)
        game.tableau[1].push(eight_h)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=eight_h.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 2)
        self.assertEqual(game.tableau[0].peek(), eight_h)

    def test_reject_non_descending_rank_build(self) -> None:
        """TC-SPID-F16-03: Placing 7 on 9 is rejected (gap of 2)."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        nine_s = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        seven_s = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)
        game.tableau[0].push(nine_s)
        game.tableau[1].push(seven_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=seven_s.card_id))
        self.assertFalse(res.success)

    def test_reject_ascending_rank_build(self) -> None:
        """TC-SPID-F16-04: Placing 10 on 9 is rejected."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        nine_s = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        ten_s = Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9)
        game.tableau[0].push(nine_s)
        game.tableau[1].push(ten_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=ten_s.card_id))
        self.assertFalse(res.success)

    def test_tableau_build_undo(self) -> None:
        """TC-SPID-F16-05: Undoing single card build restores source column."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        nine_s = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        eight_s = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)
        game.tableau[0].push(nine_s)
        game.tableau[1].push(eight_s)

        game.make_move(Move("tableau_1", "tableau_0", card_id=eight_s.card_id))
        game.undo()
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.tableau[1].peek(), eight_s)


class TestSpiderSequenceMoving(unittest.TestCase):
    """Feature 17: Spider Sequence Moving."""

    def test_same_suit_sequence_can_move_together(self) -> None:
        """TC-SPID-F17-01: Descending stack of same suit (e.g. 8♠-7♠-6♠) moves as a unit."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Destination: 9 of Spades
        nine_s = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        game.tableau[0].push(nine_s)

        # Source: 8♠, 7♠, 6♠
        eight_s = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)
        seven_s = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)
        six_s = Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5)
        game.tableau[1].push_many([eight_s, seven_s, six_s])

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=eight_s.card_id, card_count=3))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 4)
        self.assertEqual(len(game.tableau[1]), 0)

    def test_different_suit_sequence_cannot_move_together(self) -> None:
        """TC-SPID-F17-02: Stack containing mixed suits (e.g. 8♠ on 9♥) cannot be moved as multi-card."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Destination: 10 of Clubs
        ten_s = Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9)
        game.tableau[0].push(ten_s)

        # Source: 9 of Spades and 8 of Hearts (mixed suit descending sequence)
        nine_s = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        eight_h = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        game.tableau[1].push_many([nine_s, eight_h])

        # Attempting to move the 2-card sequence starting from nine_s
        res = game.make_move(Move("tableau_1", "tableau_0", card_id=nine_s.card_id, card_count=2))
        self.assertFalse(res.success)

    def test_moving_same_suit_subsequence_from_mixed_stack(self) -> None:
        """TC-SPID-F17-03: Bottom-most same-suit run can be peeled off a mixed stack."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Destination: 7 of Spades
        seven_s = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)
        game.tableau[0].push(seven_s)

        # Source: King♠ (base), 6♠, 5♠
        k_s = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        six_s = Card(Suit.SPADES, Rank.SIX, is_face_up=True, card_id=5)
        five_s = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        game.tableau[1].push_many([k_s, six_s, five_s])

        # Move 6♠-5♠ onto 7♠
        res = game.make_move(Move("tableau_1", "tableau_0", card_id=six_s.card_id, card_count=2))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.tableau[1].peek(), k_s)
        self.assertEqual(len(game.tableau[0]), 3)

    def test_sequence_move_undo_restores_stack(self) -> None:
        """TC-SPID-F17-04: Undoing multi-card sequence move restores source column exactly."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        nine_s = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        game.tableau[0].push(nine_s)

        eight_s = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)
        seven_s = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)
        game.tableau[1].push_many([eight_s, seven_s])

        game.make_move(Move("tableau_1", "tableau_0", card_id=eight_s.card_id, card_count=2))
        game.undo()
        self.assertEqual(len(game.tableau[1]), 2)
        self.assertEqual(game.tableau[1][0], eight_s)
        self.assertEqual(game.tableau[1][1], seven_s)

    def test_reject_moving_broken_rank_sequence(self) -> None:
        """TC-SPID-F17-05: Sequence with non-sequential ranks cannot move as stack."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        ten_s = Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9)
        game.tableau[0].push(ten_s)

        nine_s = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        seven_s = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)  # Missing 8!
        game.tableau[1].push_many([nine_s, seven_s])

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=nine_s.card_id, card_count=2))
        self.assertFalse(res.success)


class TestSpider13CardRunClearing(unittest.TestCase):
    """Feature 18: Spider 13-Card Run Clearing."""

    def test_complete_13_card_same_suit_run_clears(self) -> None:
        """TC-SPID-F18-01: Assembling K through A same-suit run automatically moves to foundation."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        initial_score = game.score

        # Build K through 2 on tableau 0
        run_part1 = [
            Card(Suit.SPADES, rank, is_face_up=True, card_id=rank - 1)
            for rank in range(13, 1, -1)  # 13 down to 2 (12 cards)
        ]
        game.tableau[0].push_many(run_part1)

        # Put Ace on tableau 1
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(ace_s)

        # Move Ace onto 2 -> triggers 13-card run clearance!
        # Score changes: -1 for the player move, +100 for completed run
        res = game.make_move(Move("tableau_1", "tableau_0", card_id=ace_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 0)  # Entire run removed!
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertEqual(game.score, initial_score - 1 + 100)

    def test_run_clearing_uncovers_face_down_card(self) -> None:
        """TC-SPID-F18-02: Run clearance exposes and auto-flips face-down card underneath."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        hidden_base = Card(Suit.SPADES, Rank.FIVE, is_face_up=False, card_id=4)
        game.tableau[0].push(hidden_base)

        run_part1 = [
            Card(Suit.SPADES, rank, is_face_up=True, card_id=rank + 10)
            for rank in range(13, 1, -1)
        ]
        game.tableau[0].push_many(run_part1)

        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(ace_s)

        game.make_move(Move("tableau_1", "tableau_0", card_id=ace_s.card_id))
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertTrue(game.tableau[0].peek().is_face_up)
        self.assertEqual(game.tableau[0].peek().card_id, hidden_base.card_id)

    def test_run_clearing_undo_reconstructs_run(self) -> None:
        """TC-SPID-F18-03: Undoing run clearance returns all 13 cards to tableau and removes foundation."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        initial_score = game.score

        run_part1 = [
            Card(Suit.SPADES, rank, is_face_up=True, card_id=rank - 1)
            for rank in range(13, 1, -1)
        ]
        game.tableau[0].push_many(run_part1)
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(ace_s)

        game.make_move(Move("tableau_1", "tableau_0", card_id=ace_s.card_id))
        self.assertEqual(len(game.foundations[0]), 13)

        # Undo
        game.undo()
        self.assertEqual(len(game.foundations[0]), 0)
        self.assertEqual(len(game.tableau[0]), 12)
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.tableau[1].peek(), ace_s)
        self.assertEqual(game.score, initial_score)

    def test_incomplete_12_card_run_does_not_clear(self) -> None:
        """TC-SPID-F18-04: King down to 2 without Ace does NOT clear."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        run_part1 = [
            Card(Suit.SPADES, rank, is_face_up=True, card_id=rank - 1)
            for rank in range(13, 2, -1)  # 13 down to 3
        ]
        game.tableau[0].push_many(run_part1)
        two_s = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.tableau[1].push(two_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=two_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 12)  # Remains on tableau
        self.assertEqual(len(game.foundations[0]), 0)

    def test_mixed_suit_13_card_sequence_does_not_clear(self) -> None:
        """TC-SPID-F18-05: 13-card descending sequence with different suit does NOT clear."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # 13 cards descending, but 7 is Hearts instead of Spades
        for rank in range(13, 1, -1):
            s = Suit.HEARTS if rank == 7 else Suit.SPADES
            game.tableau[0].push(Card(s, rank, is_face_up=True, card_id=rank + 20))
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(ace_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=ace_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 13)
        self.assertEqual(len(game.foundations[0]), 0)


class TestSpiderStockDealGuard(unittest.TestCase):
    """Feature 19: Spider Stock Deal Guard."""

    def test_deal_blocked_when_one_column_empty(self) -> None:
        """TC-SPID-F19-01: Dealing is blocked if column 0 is empty."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        res = game.deal_stock()
        self.assertFalse(res.success)
        self.assertIn("empty", res.error_message.lower())

    def test_deal_blocked_when_last_column_empty(self) -> None:
        """TC-SPID-F19-02: Dealing is blocked if column 9 is empty."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[9].clear()
        res = game.deal_stock()
        self.assertFalse(res.success)

    def test_deal_succeeds_when_all_columns_non_empty(self) -> None:
        """TC-SPID-F19-03: Dealing succeeds when all 10 columns contain at least 1 card."""
        game = SpiderGame(num_suits=1, seed=42)
        self.assertTrue(all(len(col) > 0 for col in game.tableau))
        res = game.deal_stock()
        self.assertTrue(res.success)

    def test_deal_blocked_when_stock_exhausted(self) -> None:
        """TC-SPID-F19-04: Dealing fails gracefully when stock is empty."""
        game = SpiderGame(num_suits=1, seed=42)
        game.stock.clear()
        res = game.deal_stock()
        self.assertFalse(res.success)

    def test_deal_blocked_via_generic_move(self) -> None:
        """TC-SPID-F19-05: Move(DEAL_STOCK) rejected if empty column exists."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[4].clear()
        m = Move(SpiderMoveType.DEAL_STOCK, "stock", "tableau")
        res = game.make_move(m)
        self.assertFalse(res.success)


class TestSpiderEmptyColumnMovement(unittest.TestCase):
    """Feature 20: Spider Empty Column Movement."""

    def test_any_single_card_can_move_to_empty_column(self) -> None:
        """TC-SPID-F20-01: Non-King card (e.g. 5♠) can move to empty column."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        five_s = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        game.tableau[1].push(five_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=five_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.tableau[0].peek(), five_s)

    def test_valid_same_suit_sequence_can_move_to_empty(self) -> None:
        """TC-SPID-F20-02: Multi-card same-suit run can move to empty column."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        eight_s = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)
        seven_s = Card(Suit.SPADES, Rank.SEVEN, is_face_up=True, card_id=6)
        game.tableau[1].push_many([eight_s, seven_s])

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=eight_s.card_id, card_count=2))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 2)
        self.assertEqual(len(game.tableau[1]), 0)

    def test_mixed_suit_sequence_cannot_move_to_empty(self) -> None:
        """TC-SPID-F20-03: Multi-card mixed-suit sequence cannot move to empty column."""
        game = SpiderGame(num_suits=2, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        eight_s = Card(Suit.SPADES, Rank.EIGHT, is_face_up=True, card_id=7)
        seven_h = Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19)
        game.tableau[1].push_many([eight_s, seven_h])

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=eight_s.card_id, card_count=2))
        self.assertFalse(res.success)

    def test_empty_column_move_undo(self) -> None:
        """TC-SPID-F20-04: Undoing move to empty column empties column again."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        three_s = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        game.tableau[1].push(three_s)

        game.make_move(Move("tableau_1", "tableau_0", card_id=three_s.card_id))
        self.assertEqual(len(game.tableau[0]), 1)
        game.undo()
        self.assertEqual(len(game.tableau[0]), 0)
        self.assertEqual(game.tableau[1].peek(), three_s)

    def test_king_can_move_to_empty_column(self) -> None:
        """TC-SPID-F20-05: King can move to empty column."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        k_s = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        game.tableau[1].push(k_s)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=k_s.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.tableau[0].peek(), k_s)


class TestSpiderMoveValidationAndRejection(unittest.TestCase):
    """Feature 21: Move Validation & Rejection (Spider focus)."""

    def test_reject_null_move(self) -> None:
        """TC-SPID-F21-01: None move rejected."""
        game = SpiderGame(num_suits=1, seed=42)
        self.assertFalse(game.make_move(None).success)

    def test_reject_out_of_range_column(self) -> None:
        """TC-SPID-F21-02: Column 10 (valid is 0-9) rejected."""
        game = SpiderGame(num_suits=1, seed=42)
        res = game.make_move(Move("tableau_10", "tableau_0"))
        self.assertFalse(res.success)

    def test_reject_moving_from_empty_column(self) -> None:
        """TC-SPID-F21-03: Moving from empty column fails."""
        game = SpiderGame(num_suits=1, seed=42)
        game.tableau[0].clear()
        res = game.make_move(Move("tableau_0", "tableau_1"))
        self.assertFalse(res.success)

    def test_reject_moving_face_down_card(self) -> None:
        """TC-SPID-F21-04: Cannot initiate move on face-down card."""
        game = SpiderGame(num_suits=1, seed=42)
        face_down_card = game.tableau[0][0]
        self.assertFalse(face_down_card.is_face_up)
        res = game.make_move(Move("tableau_0", "tableau_1", card_id=face_down_card.card_id))
        self.assertFalse(res.success)

    def test_state_integrity_preserved_on_rejected_move(self) -> None:
        """TC-SPID-F21-05: Rejected move does not alter score, moves_count, or cards."""
        game = SpiderGame(num_suits=1, seed=42)
        snap_before = game.get_state_snapshot()
        game.make_move(Move("tableau_0", "tableau_1", card_id=9999))
        snap_after = game.get_state_snapshot()
        self.assertEqual(snap_before["score"], snap_after["score"])
        self.assertEqual(snap_before["moves_count"], snap_after["moves_count"])
        self.assertEqual(snap_before["piles"], snap_after["piles"])


if __name__ == "__main__":
    unittest.main()
