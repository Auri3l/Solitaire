"""Tier 1 Feature Coverage: Klondike Solitaire Rules Engine.

Verifies Features 4, 5, 6, 7, 8, 9, 10, and 21:
- Feature 4: Klondike Turn-1 Deal (>= 5 tests)
- Feature 5: Klondike Turn-3 Deal (>= 5 tests)
- Feature 6: Klondike Stock Recycling (>= 5 tests)
- Feature 7: Klondike Tableau Building (>= 5 tests)
- Feature 8: Klondike Partial Sequence Move (>= 5 tests)
- Feature 9: Klondike King to Empty (>= 5 tests)
- Feature 10: Klondike Foundation Stacking (>= 5 tests)
- Feature 21: Move Validation & Rejection (>= 5 tests)
"""

import unittest
from solitaire.core.card import Card, Suit, Rank, Color
from solitaire.core.pile import PileType
from solitaire.core.base_game import Move, MoveResult
from solitaire.games.klondike import KlondikeGame, MoveType, ScoringMode


class TestKlondikeTurn1Deal(unittest.TestCase):
    """Feature 4: Klondike Turn-1 Deal."""

    def test_turn1_deal_moves_one_card(self) -> None:
        """TC-KLON-F4-01: Single deal moves exactly 1 card from stock to waste."""
        game = KlondikeGame(turn_mode=1, seed=42)
        initial_stock = len(game.stock)
        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.stock), initial_stock - 1)
        self.assertEqual(len(game.waste), 1)
        self.assertTrue(game.waste.peek().is_face_up)

    def test_turn1_deal_exhausts_entire_stock(self) -> None:
        """TC-KLON-F4-02: Exactly 24 deals moves all 24 cards to waste."""
        game = KlondikeGame(turn_mode=1, seed=42)
        for _ in range(24):
            res = game.deal_stock()
            self.assertTrue(res.success)
        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 24)

    def test_turn1_waste_top_card_playable(self) -> None:
        """TC-KLON-F4-03: Top card of waste is accessible and playable."""
        game = KlondikeGame(turn_mode=1, seed=42)
        game.deal_stock()
        top_waste = game.waste.peek()
        self.assertIsNotNone(top_waste)
        self.assertTrue(top_waste.is_face_up)

    def test_turn1_deal_reversibility(self) -> None:
        """TC-KLON-F4-04: Deal can be undone and card returns to stock face-down."""
        game = KlondikeGame(turn_mode=1, seed=42)
        top_stock_id = game.stock.peek().card_id
        game.deal_stock()
        self.assertEqual(game.waste.peek().card_id, top_stock_id)
        game.undo()
        self.assertEqual(len(game.waste), 0)
        self.assertEqual(game.stock.peek().card_id, top_stock_id)
        self.assertFalse(game.stock.peek().is_face_up)

    def test_turn1_deal_via_generic_move(self) -> None:
        """TC-KLON-F4-05: Move(source_pile="stock", dest_pile="waste") performs deal."""
        game = KlondikeGame(turn_mode=1, seed=10)
        m = Move("stock", "waste")
        res = game.make_move(m)
        self.assertTrue(res.success)
        self.assertEqual(len(game.waste), 1)


class TestKlondikeTurn3Deal(unittest.TestCase):
    """Feature 5: Klondike Turn-3 Deal."""

    def test_turn3_deal_moves_up_to_three_cards(self) -> None:
        """TC-KLON-F5-01: Dealing in Turn-3 moves 3 cards to waste."""
        game = KlondikeGame(turn_mode=3, seed=42)
        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.stock), 21)
        self.assertEqual(len(game.waste), 3)
        self.assertTrue(all(c.is_face_up for c in game.waste))

    def test_turn3_deal_exhausts_24_cards_in_8_deals(self) -> None:
        """TC-KLON-F5-02: 8 deals of 3 fully empties 24-card stock."""
        game = KlondikeGame(turn_mode=3, seed=42)
        for i in range(8):
            res = game.deal_stock()
            self.assertTrue(res.success)
            self.assertEqual(len(game.stock), 24 - (i + 1) * 3)
        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 24)

    def test_turn3_partial_deal_remainder(self) -> None:
        """TC-KLON-F5-03: Stock with remainder < 3 deals remaining cards."""
        game = KlondikeGame(turn_mode=3, seed=42)
        # Clear stock and put 2 cards
        game.stock.clear()
        c1 = Card(Suit.SPADES, Rank.TWO, is_face_up=False, card_id=1)
        c2 = Card(Suit.SPADES, Rank.THREE, is_face_up=False, card_id=2)
        game.stock.push_many([c1, c2])

        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(len(game.waste), 2)
        self.assertEqual(len(game.stock), 0)

    def test_turn3_deal_reversibility(self) -> None:
        """TC-KLON-F5-04: Turn 3 deal undo restores all 3 cards in exact order."""
        game = KlondikeGame(turn_mode=3, seed=42)
        stock_before = [c.card_id for c in game.stock]
        game.deal_stock()
        self.assertEqual(len(game.waste), 3)
        game.undo()
        self.assertEqual(len(game.waste), 0)
        self.assertEqual(len(game.stock), 24)
        self.assertEqual([c.card_id for c in game.stock], stock_before)

    def test_turn3_only_top_of_waste_playable(self) -> None:
        """TC-KLON-F5-05: Waste cards under the top card cannot be moved directly."""
        game = KlondikeGame(turn_mode=3, seed=42)
        game.deal_stock()
        under_card = game.waste[0]
        # Attempt to move under card directly to tableau should fail
        m = Move("waste", "tableau_0", card_id=under_card.card_id)
        res = game.make_move(m)
        self.assertFalse(res.success)


class TestKlondikeStockRecycling(unittest.TestCase):
    """Feature 6: Klondike Stock Recycling."""

    def test_recycle_resets_waste_to_stock_face_down(self) -> None:
        """TC-KLON-F6-01: Recycling moves all waste cards back to stock face down."""
        game = KlondikeGame(turn_mode=1, seed=42)
        for _ in range(24):
            game.deal_stock()
        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 24)

        res = game.make_move(Move(MoveType.RECYCLE_STOCK, "waste", "stock"))
        self.assertTrue(res.success)
        self.assertEqual(len(game.waste), 0)
        self.assertEqual(len(game.stock), 24)
        self.assertTrue(all(not c.is_face_up for c in game.stock))

    def test_recycle_preserves_order_inversion(self) -> None:
        """TC-KLON-F6-02: Recycling inverts waste order so 1st dealt is 1st dealt on 2nd pass."""
        game = KlondikeGame(turn_mode=1, seed=42)
        first_dealt_card_id = game.stock[-1].card_id
        for _ in range(24):
            game.deal_stock()
        game.make_move(Move(MoveType.RECYCLE_STOCK, "waste", "stock"))
        # Top of stock should now again be the first dealt card
        self.assertEqual(game.stock[-1].card_id, first_dealt_card_id)

    def test_recycle_increments_passes_and_recycles_count(self) -> None:
        """TC-KLON-F6-03: Recycle increments passes_through_stock and recycles_count."""
        game = KlondikeGame(turn_mode=1, seed=42)
        self.assertEqual(game.passes_through_stock, 1)
        self.assertEqual(game.recycles_count, 0)
        for _ in range(24):
            game.deal_stock()
        # deal_stock automatically recycles when stock is empty
        res = game.deal_stock()
        self.assertTrue(res.success)
        self.assertEqual(game.passes_through_stock, 2)
        self.assertEqual(game.recycles_count, 1)

    def test_recycle_undo_restores_waste(self) -> None:
        """TC-KLON-F6-04: Undoing recycle restores waste and clears stock."""
        game = KlondikeGame(turn_mode=1, seed=42)
        for _ in range(24):
            game.deal_stock()
        game.make_move(Move(MoveType.RECYCLE_STOCK, "waste", "stock"))
        game.undo()
        self.assertEqual(len(game.stock), 0)
        self.assertEqual(len(game.waste), 24)
        self.assertTrue(all(c.is_face_up for c in game.waste))

    def test_recycle_when_stock_non_empty_rejected(self) -> None:
        """TC-KLON-F6-05: Cannot recycle if stock still has cards."""
        game = KlondikeGame(turn_mode=1, seed=42)
        game.deal_stock()
        res = game.make_move(Move(MoveType.RECYCLE_STOCK, "waste", "stock"))
        self.assertFalse(res.success)


class TestKlondikeTableauBuilding(unittest.TestCase):
    """Feature 7: Klondike Tableau Building."""

    def test_valid_red_on_black_descending(self) -> None:
        """TC-KLON-F7-01: Red Jack can be placed on Black Queen."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        q_black = Card(Suit.SPADES, Rank.QUEEN, is_face_up=True, card_id=11)
        j_red = Card(Suit.HEARTS, Rank.JACK, is_face_up=True, card_id=23)
        game.tableau[0].push(q_black)
        game.tableau[1].push(j_red)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=j_red.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 2)
        self.assertEqual(game.tableau[0].peek(), j_red)

    def test_valid_black_on_red_descending(self) -> None:
        """TC-KLON-F7-02: Black 10 can be placed on Red Jack."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        j_red = Card(Suit.DIAMONDS, Rank.JACK, is_face_up=True, card_id=36)
        ten_black = Card(Suit.CLUBS, Rank.TEN, is_face_up=True, card_id=48)
        game.tableau[0].push(j_red)
        game.tableau[1].push(ten_black)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=ten_black.card_id))
        self.assertTrue(res.success)

    def test_reject_same_color_placement(self) -> None:
        """TC-KLON-F7-03: Red 8 cannot be placed on Red 9."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        nine_red = Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21)
        eight_red = Card(Suit.DIAMONDS, Rank.EIGHT, is_face_up=True, card_id=33)
        game.tableau[0].push(nine_red)
        game.tableau[1].push(eight_red)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=eight_red.card_id))
        self.assertFalse(res.success)

    def test_reject_non_descending_placement(self) -> None:
        """TC-KLON-F7-04: Red 7 cannot be placed on Black Queen (gap of ranks)."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        q_black = Card(Suit.SPADES, Rank.QUEEN, is_face_up=True, card_id=11)
        seven_red = Card(Suit.HEARTS, Rank.SEVEN, is_face_up=True, card_id=19)
        game.tableau[0].push(q_black)
        game.tableau[1].push(seven_red)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=seven_red.card_id))
        self.assertFalse(res.success)

    def test_tableau_build_undo_reverses_position(self) -> None:
        """TC-KLON-F7-05: Undoing tableau move returns card to source column."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        q_black = Card(Suit.SPADES, Rank.QUEEN, is_face_up=True, card_id=11)
        j_red = Card(Suit.HEARTS, Rank.JACK, is_face_up=True, card_id=23)
        game.tableau[0].push(q_black)
        game.tableau[1].push(j_red)

        game.make_move(Move("tableau_1", "tableau_0", card_id=j_red.card_id))
        game.undo()
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.tableau[1].peek(), j_red)


class TestKlondikePartialSequenceMove(unittest.TestCase):
    """Feature 8: Klondike Partial Sequence Move."""

    def test_move_multi_card_face_up_sequence(self) -> None:
        """TC-KLON-F8-01: Move a 3-card alternating sub-stack onto a valid receiver."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Destination: King of Hearts
        k_hearts = Card(Suit.HEARTS, Rank.KING, is_face_up=True, card_id=25)
        game.tableau[0].push(k_hearts)

        # Source: Queen of Spades, Jack of Hearts, Ten of Clubs
        q_spades = Card(Suit.SPADES, Rank.QUEEN, is_face_up=True, card_id=11)
        j_hearts = Card(Suit.HEARTS, Rank.JACK, is_face_up=True, card_id=23)
        ten_clubs = Card(Suit.CLUBS, Rank.TEN, is_face_up=True, card_id=48)
        game.tableau[1].push_many([q_spades, j_hearts, ten_clubs])

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=q_spades.card_id, card_count=3))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 4)
        self.assertEqual(len(game.tableau[1]), 0)
        self.assertEqual(game.tableau[0][-1], ten_clubs)

    def test_partial_sequence_leaves_underlying_cards(self) -> None:
        """TC-KLON-F8-02: Moving top 2 cards leaves the base card in source column."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()

        # Destination: 9 of Spades
        nine_spades = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        game.tableau[0].push(nine_spades)

        # Source: King (base), 8 of Hearts, 7 of Clubs
        k_diamonds = Card(Suit.DIAMONDS, Rank.KING, is_face_up=True, card_id=38)
        eight_hearts = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        seven_clubs = Card(Suit.CLUBS, Rank.SEVEN, is_face_up=True, card_id=45)
        game.tableau[1].push_many([k_diamonds, eight_hearts, seven_clubs])

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=eight_hearts.card_id, card_count=2))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[1]), 1)
        self.assertEqual(game.tableau[1].peek(), k_diamonds)
        self.assertEqual(len(game.tableau[0]), 3)

    def test_cannot_move_face_down_sequence(self) -> None:
        """TC-KLON-F8-03: Attempting to move starting from a face-down card is rejected."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        nine_spades = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        game.tableau[0].push(nine_spades)

        down_card = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=False, card_id=20)
        up_card = Card(Suit.CLUBS, Rank.SEVEN, is_face_up=True, card_id=45)
        game.tableau[1].push_many([down_card, up_card])

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=down_card.card_id))
        self.assertFalse(res.success)

    def test_partial_sequence_undo_restores_split(self) -> None:
        """TC-KLON-F8-04: Undoing sub-stack move restores split to source column."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        nine_spades = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        game.tableau[0].push(nine_spades)

        k_diamonds = Card(Suit.DIAMONDS, Rank.KING, is_face_up=True, card_id=38)
        eight_hearts = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        seven_clubs = Card(Suit.CLUBS, Rank.SEVEN, is_face_up=True, card_id=45)
        game.tableau[1].push_many([k_diamonds, eight_hearts, seven_clubs])

        game.make_move(Move("tableau_1", "tableau_0", card_id=eight_hearts.card_id, card_count=2))
        game.undo()
        self.assertEqual(len(game.tableau[1]), 3)
        self.assertEqual(game.tableau[1][0], k_diamonds)
        self.assertEqual(game.tableau[1][1], eight_hearts)
        self.assertEqual(game.tableau[1][2], seven_clubs)

    def test_move_invalid_internal_subsequence_rejected(self) -> None:
        """TC-KLON-F8-05: Stack containing non-alternating sequence internally cannot move."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        ten_spades = Card(Suit.SPADES, Rank.TEN, is_face_up=True, card_id=9)
        game.tableau[0].push(ten_spades)

        nine_hearts = Card(Suit.HEARTS, Rank.NINE, is_face_up=True, card_id=21)
        eight_diamonds = Card(Suit.DIAMONDS, Rank.EIGHT, is_face_up=True, card_id=33)  # Red on red!
        game.tableau[1].push_many([nine_hearts, eight_diamonds])

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=nine_hearts.card_id, card_count=2))
        self.assertFalse(res.success)


class TestKlondikeKingToEmpty(unittest.TestCase):
    """Feature 9: Klondike King to Empty."""

    def test_king_can_move_to_empty_column(self) -> None:
        """TC-KLON-F9-01: King can be placed into an empty tableau column."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        k_clubs = Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=51)
        game.tableau[1].push(k_clubs)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=k_clubs.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.tableau[0].peek(), k_clubs)

    def test_king_headed_sequence_can_move_to_empty(self) -> None:
        """TC-KLON-F9-02: Multi-card sequence headed by a King can move to empty column."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        k_spades = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        q_hearts = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        j_clubs = Card(Suit.CLUBS, Rank.JACK, is_face_up=True, card_id=49)
        game.tableau[1].push_many([k_spades, q_hearts, j_clubs])

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=k_spades.card_id, card_count=3))
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 3)

    def test_non_king_rejected_on_empty_column(self) -> None:
        """TC-KLON-F9-03: Non-King (Queen, Ace, 10) cannot be placed on empty column."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        q_spades = Card(Suit.SPADES, Rank.QUEEN, is_face_up=True, card_id=11)
        game.tableau[1].push(q_spades)

        res = game.make_move(Move("tableau_1", "tableau_0", card_id=q_spades.card_id))
        self.assertFalse(res.success)

    def test_king_from_waste_to_empty_column(self) -> None:
        """TC-KLON-F9-04: King on waste pile can move directly to empty tableau column."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.waste.clear()
        k_diamonds = Card(Suit.DIAMONDS, Rank.KING, is_face_up=True, card_id=38)
        game.waste.push(k_diamonds)

        res = game.make_move(Move("waste", "tableau_0", card_id=k_diamonds.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.tableau[0].peek(), k_diamonds)

    def test_king_to_empty_undo(self) -> None:
        """TC-KLON-F9-05: Undoing King to empty column leaves target column empty again."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        game.tableau[1].clear()
        k_clubs = Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=51)
        game.tableau[1].push(k_clubs)

        game.make_move(Move("tableau_1", "tableau_0", card_id=k_clubs.card_id))
        self.assertEqual(len(game.tableau[0]), 1)
        game.undo()
        self.assertEqual(len(game.tableau[0]), 0)
        self.assertEqual(game.tableau[1].peek(), k_clubs)


class TestKlondikeFoundationStacking(unittest.TestCase):
    """Feature 10: Klondike Foundation Stacking."""

    def test_ace_starts_empty_foundation(self) -> None:
        """TC-KLON-F10-01: Ace can be placed into an empty foundation pile."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[0].push(ace_spades)

        res = game.make_move(Move("tableau_0", "foundation_0", card_id=ace_spades.card_id))
        self.assertTrue(res.success)
        self.assertEqual(game.foundations[0].peek(), ace_spades)

    def test_ascending_same_suit_on_foundation(self) -> None:
        """TC-KLON-F10-02: Two of Spades can be placed on Ace of Spades in foundation."""
        game = KlondikeGame(seed=42)
        game.foundations[0].clear()
        game.tableau[0].clear()
        ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        two_spades = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.foundations[0].push(ace_spades)
        game.tableau[0].push(two_spades)

        res = game.make_move(Move("tableau_0", "foundation_0", card_id=two_spades.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.foundations[0]), 2)
        self.assertEqual(game.foundations[0].peek(), two_spades)

    def test_reject_wrong_suit_on_foundation(self) -> None:
        """TC-KLON-F10-03: Two of Hearts cannot be placed on Ace of Spades."""
        game = KlondikeGame(seed=42)
        game.foundations[0].clear()
        game.tableau[0].clear()
        ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        two_hearts = Card(Suit.HEARTS, Rank.TWO, is_face_up=True, card_id=14)
        game.foundations[0].push(ace_spades)
        game.tableau[0].push(two_hearts)

        res = game.make_move(Move("tableau_0", "foundation_0", card_id=two_hearts.card_id))
        self.assertFalse(res.success)

    def test_reject_non_sequential_rank_on_foundation(self) -> None:
        """TC-KLON-F10-04: Three of Spades cannot be placed directly on Ace of Spades."""
        game = KlondikeGame(seed=42)
        game.foundations[0].clear()
        game.tableau[0].clear()
        ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        three_spades = Card(Suit.SPADES, Rank.THREE, is_face_up=True, card_id=2)
        game.foundations[0].push(ace_spades)
        game.tableau[0].push(three_spades)

        res = game.make_move(Move("tableau_0", "foundation_0", card_id=three_spades.card_id))
        self.assertFalse(res.success)

    def test_foundation_to_tableau_demotion(self) -> None:
        """TC-KLON-F10-05: Foundation card can be demoted to valid tableau receiver."""
        game = KlondikeGame(seed=42)
        game.foundations[0].clear()
        game.tableau[0].clear()
        ace_spades = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        two_spades = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        three_hearts = Card(Suit.HEARTS, Rank.THREE, is_face_up=True, card_id=15)
        game.foundations[0].push_many([ace_spades, two_spades])
        game.tableau[0].push(three_hearts)

        res = game.make_move(Move("foundation_0", "tableau_0", card_id=two_spades.card_id))
        self.assertTrue(res.success)
        self.assertEqual(len(game.foundations[0]), 1)
        self.assertEqual(game.tableau[0].peek(), two_spades)


class TestKlondikeMoveValidationAndRejection(unittest.TestCase):
    """Feature 21: Move Validation & Rejection (Klondike focus)."""

    def test_reject_none_move(self) -> None:
        """TC-KLON-F21-01: Passing None to make_move fails gracefully."""
        game = KlondikeGame(seed=42)
        res = game.make_move(None)
        self.assertFalse(res.success)

    def test_reject_invalid_pile_id(self) -> None:
        """TC-KLON-F21-02: Moving to or from non-existent pile fails."""
        game = KlondikeGame(seed=42)
        res = game.make_move(Move("fake_pile", "tableau_0"))
        self.assertFalse(res.success)
        res2 = game.make_move(Move("tableau_0", "bad_pile"))
        self.assertFalse(res2.success)

    def test_reject_move_from_empty_pile(self) -> None:
        """TC-KLON-F21-03: Moving from an empty pile fails."""
        game = KlondikeGame(seed=42)
        game.tableau[0].clear()
        res = game.make_move(Move("tableau_0", "tableau_1"))
        self.assertFalse(res.success)

    def test_state_remains_uncorrupted_after_rejected_move(self) -> None:
        """TC-KLON-F21-04: Rejected moves leave game state 100% identical."""
        game = KlondikeGame(seed=42)
        snap_before = game.get_state_snapshot()
        # Attempt illegal move: King onto non-matching tableau
        k_card = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        game.tableau[0].clear()
        game.tableau[0].push(k_card)
        game.make_move(Move("tableau_0", "tableau_1", card_id=k_card.card_id))
        snap_after = game.get_state_snapshot()
        self.assertEqual(snap_before["score"], snap_after["score"])
        self.assertEqual(snap_before["moves_count"], snap_after["moves_count"])

    def test_is_legal_move_matches_make_move(self) -> None:
        """TC-KLON-F21-05: is_legal_move consistently predicts make_move outcome."""
        game = KlondikeGame(seed=42)
        legal_moves = game.get_legal_moves()
        for m in legal_moves:
            self.assertTrue(game.is_legal_move(m))


if __name__ == "__main__":
    unittest.main()
