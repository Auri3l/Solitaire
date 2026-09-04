"""Tier 1 Feature Coverage: Core Card, Deck, Pile, and Reversible Command Engine.

Verifies Features 1, 2, and 3:
- Feature 1: Standard Card & Deck Model (>= 5 tests)
- Feature 2: Multi-Deck Spider Model (>= 5 tests)
- Feature 3: Reversible Command Delta Engine (>= 5 tests)
"""

import unittest
from typing import List

from solitaire.core.card import Card, Suit, Rank, Color
from solitaire.core.pile import Pile, PileType, Deck
from solitaire.core.commands import (
    CardMoveCommand,
    StockDealCommand,
    RecycleCommand,
    CommandHistory,
)


class DummyTestGame:
    """Minimal opaque state container for testing Command executions directly."""
    def __init__(self) -> None:
        self.piles = {
            "p1": Pile("p1", PileType.TABLEAU),
            "p2": Pile("p2", PileType.TABLEAU),
            "stock": Pile("stock", PileType.STOCK),
            "waste": Pile("waste", PileType.WASTE),
        }
        self.score = 0
        self.moves_count = 0
        self.recycles_count = 0
        self.passes_through_stock = 1

    def get_pile(self, pile_id: str) -> Pile:
        return self.piles[pile_id]

    def get_pile_by_id(self, pile_id: str) -> Pile:
        return self.piles[pile_id]


class TestStandardCardAndDeckModel(unittest.TestCase):
    """Feature 1: Standard Card & Deck Model."""

    def test_card_instantiation_and_attributes(self) -> None:
        """TC-CORE-F1-01: Verifies Card rank, suit, color, and id attributes."""
        c = Card(suit=Suit.HEARTS, rank=Rank.ACE, is_face_up=True, card_id=13)
        self.assertEqual(c.suit, Suit.HEARTS)
        self.assertEqual(c.rank, Rank.ACE)
        self.assertEqual(c.color, Color.RED)
        self.assertTrue(c.is_red)
        self.assertFalse(c.is_black)
        self.assertTrue(c.is_face_up)
        self.assertEqual(c.card_id, 13)
        self.assertEqual(c.id, 13)

    def test_card_from_integers_and_strings(self) -> None:
        """TC-CORE-F1-02: Verifies flexible instantiation from string symbols and integer ranks."""
        s = Suit.from_string("♠")
        self.assertEqual(s, Suit.SPADES)
        s2 = Suit.from_string("diamonds")
        self.assertEqual(s2, Suit.DIAMONDS)
        r = Rank.from_string("K")
        self.assertEqual(r, Rank.KING)
        c = Card(suit=Suit.SPADES, rank=13, is_face_up=False, card_id=12)
        self.assertEqual(c.rank, Rank.KING)
        self.assertEqual(c.display_name, "??")
        c.flip()
        self.assertEqual(c.display_name, "K♠")

    def test_card_equality_hashing_and_cloning(self) -> None:
        """TC-CORE-F1-03: Verifies Card equality, hashing, and independent cloning."""
        c1 = Card(suit=Suit.CLUBS, rank=Rank.QUEEN, is_face_up=True, card_id=50)
        c2 = c1.clone()
        self.assertEqual(c1, c2)
        self.assertEqual(hash(c1), hash(c2))
        c2.is_face_up = False
        self.assertTrue(c1.is_face_up)
        self.assertFalse(c2.is_face_up)

    def test_card_serialization_roundtrip(self) -> None:
        """TC-CORE-F1-04: Verifies serialization to and from dictionary."""
        c = Card(suit=Suit.DIAMONDS, rank=Rank.TEN, is_face_up=True, card_id=35)
        d = c.to_dict()
        restored = Card.from_dict(d)
        self.assertEqual(c, restored)
        self.assertEqual(restored.is_face_up, True)
        self.assertEqual(restored.rank, Rank.TEN)
        self.assertEqual(restored.suit, Suit.DIAMONDS)

    def test_standard_52_deck_generation(self) -> None:
        """TC-CORE-F1-05: Verifies standard 52-card deck distribution and unique IDs."""
        deck = Deck.create_standard()
        self.assertEqual(len(deck), 52)
        cards = deck.cards
        self.assertEqual(len(set(c.card_id for c in cards)), 52)
        suits_count = {s: 0 for s in Suit}
        for c in cards:
            suits_count[c.suit] += 1
            self.assertFalse(c.is_face_up)
        for s in Suit:
            self.assertEqual(suits_count[s], 13)


class TestMultiDeckSpiderModel(unittest.TestCase):
    """Feature 2: Multi-Deck Spider Model."""

    def test_spider_1suit_deck_composition(self) -> None:
        """TC-CORE-F2-01: Verifies 1-suit Spider deck has 104 cards, all Spades."""
        deck = Deck.create_spider_deck(num_suits=1)
        self.assertEqual(len(deck), 104)
        self.assertTrue(all(c.suit == Suit.SPADES for c in deck))
        self.assertEqual(len(set(c.card_id for c in deck)), 104)
        ranks_count = {r: 0 for r in Rank}
        for c in deck:
            ranks_count[c.rank] += 1
        for r in Rank:
            self.assertEqual(ranks_count[r], 8)  # 8 copies of each rank

    def test_spider_2suit_deck_composition(self) -> None:
        """TC-CORE-F2-02: Verifies 2-suit Spider deck has 52 Spades and 52 Hearts."""
        deck = Deck.create_spider_deck(num_suits=2)
        self.assertEqual(len(deck), 104)
        spades = [c for c in deck if c.suit == Suit.SPADES]
        hearts = [c for c in deck if c.suit == Suit.HEARTS]
        self.assertEqual(len(spades), 52)
        self.assertEqual(len(hearts), 52)
        self.assertEqual(len(set(c.card_id for c in deck)), 104)

    def test_spider_4suit_deck_composition(self) -> None:
        """TC-CORE-F2-03: Verifies 4-suit Spider deck has 26 of each suit."""
        deck = Deck.create_spider_deck(num_suits=4)
        self.assertEqual(len(deck), 104)
        for suit in Suit:
            suit_cards = [c for c in deck if c.suit == suit]
            self.assertEqual(len(suit_cards), 26)
        self.assertEqual(len(set(c.card_id for c in deck)), 104)

    def test_spider_invalid_suit_count_rejection(self) -> None:
        """TC-CORE-F2-04: Verifies invalid suit counts (e.g. 3, 5) raise ValueError."""
        with self.assertRaises(ValueError):
            Deck.create_spider_deck(num_suits=3)
        with self.assertRaises(ValueError):
            Deck.create_spider_deck(num_suits=0)

    def test_spider_deck_deterministic_shuffle(self) -> None:
        """TC-CORE-F2-05: Deterministic shuffling produces identical permutations with fixed seed."""
        d1 = Deck.create_spider_deck(num_suits=2)
        d2 = Deck.create_spider_deck(num_suits=2)
        s1 = Deck.shuffle_cards(d1, seed=777)
        s2 = Deck.shuffle_cards(d2, seed=777)
        self.assertEqual([c.card_id for c in s1], [c.card_id for c in s2])


class TestReversibleCommandDeltaEngine(unittest.TestCase):
    """Feature 3: Reversible Command Delta Engine."""

    def test_card_move_command_execute_and_undo(self) -> None:
        """TC-CORE-F3-01: Verifies CardMoveCommand moves cards and restores exact state on undo."""
        game = DummyTestGame()
        c1 = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=12)
        c2 = Card(Suit.HEARTS, Rank.QUEEN, is_face_up=True, card_id=24)
        game.piles["p1"].push_many([c1, c2])

        cmd = CardMoveCommand("p1", "p2", [c1.card_id, c2.card_id], score_delta=10)
        self.assertTrue(cmd.execute(game))
        self.assertEqual(len(game.piles["p1"]), 0)
        self.assertEqual(len(game.piles["p2"]), 2)
        self.assertEqual(game.score, 10)
        self.assertEqual(game.moves_count, 1)

        self.assertTrue(cmd.undo(game))
        self.assertEqual(len(game.piles["p1"]), 2)
        self.assertEqual(len(game.piles["p2"]), 0)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.moves_count, 0)

    def test_card_move_auto_flip_reversibility(self) -> None:
        """TC-CORE-F3-02: Verifies uncovering face-down card flips on execute and re-hides on undo."""
        game = DummyTestGame()
        bottom = Card(Suit.CLUBS, Rank.NINE, is_face_up=False, card_id=47)
        top = Card(Suit.DIAMONDS, Rank.EIGHT, is_face_up=True, card_id=33)
        game.piles["p1"].push_many([bottom, top])

        cmd = CardMoveCommand("p1", "p2", [top.card_id], uncovered_card_id=bottom.card_id, score_delta=5)
        cmd.execute(game)
        self.assertTrue(bottom.is_face_up)

        cmd.undo(game)
        self.assertFalse(bottom.is_face_up)
        self.assertEqual(len(game.piles["p1"]), 2)

    def test_stock_deal_command_execute_and_undo(self) -> None:
        """TC-CORE-F3-03: Verifies StockDealCommand transfers cards from stock to waste and reverses."""
        game = DummyTestGame()
        for i in range(5):
            game.piles["stock"].push(Card(Suit.SPADES, i + 1, is_face_up=False, card_id=i))

        cmd = StockDealCommand(count=3, source_pile_id="stock", dest_pile_id="waste")
        self.assertTrue(cmd.execute(game))
        self.assertEqual(len(game.piles["stock"]), 2)
        self.assertEqual(len(game.piles["waste"]), 3)
        self.assertTrue(all(c.is_face_up for c in game.piles["waste"]))

        self.assertTrue(cmd.undo(game))
        self.assertEqual(len(game.piles["stock"]), 5)
        self.assertEqual(len(game.piles["waste"]), 0)
        self.assertTrue(all(not c.is_face_up for c in game.piles["stock"]))

    def test_recycle_command_execute_and_undo(self) -> None:
        """TC-CORE-F3-04: Verifies RecycleCommand inverts waste back to stock face down."""
        game = DummyTestGame()
        c1 = Card(Suit.HEARTS, Rank.TWO, is_face_up=True, card_id=14)
        c2 = Card(Suit.HEARTS, Rank.THREE, is_face_up=True, card_id=15)
        game.piles["waste"].push_many([c1, c2])

        cmd = RecycleCommand(source_pile_id="waste", dest_pile_id="stock")
        self.assertTrue(cmd.execute(game))
        self.assertEqual(len(game.piles["waste"]), 0)
        self.assertEqual(len(game.piles["stock"]), 2)
        self.assertTrue(all(not c.is_face_up for c in game.piles["stock"]))
        # Inverted order: c2 was on top of waste, now c2 is on bottom of stock
        self.assertEqual(game.piles["stock"][0].card_id, c2.card_id)
        self.assertEqual(game.piles["stock"][1].card_id, c1.card_id)

        self.assertTrue(cmd.undo(game))
        self.assertEqual(len(game.piles["waste"]), 2)
        self.assertEqual(len(game.piles["stock"]), 0)
        self.assertTrue(all(c.is_face_up for c in game.piles["waste"]))
        self.assertEqual(game.piles["waste"][0].card_id, c1.card_id)
        self.assertEqual(game.piles["waste"][1].card_id, c2.card_id)

    def test_command_history_multi_step_and_branch_clearing(self) -> None:
        """TC-CORE-F3-05: Verifies CommandHistory stack tracking and clearing redo upon new action."""
        history = CommandHistory()
        self.assertFalse(history.can_undo())
        self.assertFalse(history.can_redo())

        game = DummyTestGame()
        c1 = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.piles["p1"].push(c1)
        cmd1 = CardMoveCommand("p1", "p2", [c1.card_id])
        cmd1.execute(game)
        history.push(cmd1)

        self.assertTrue(history.can_undo())
        self.assertFalse(history.can_redo())
        self.assertEqual(history.undo_count, 1)

        # Undo
        self.assertTrue(history.undo(game))
        self.assertFalse(history.can_undo())
        self.assertTrue(history.can_redo())
        self.assertEqual(len(game.piles["p1"]), 1)

        # Branch clear: executing new move should purge redo stack
        cmd2 = CardMoveCommand("p1", "waste", [c1.card_id])
        cmd2.execute(game)
        history.push(cmd2)
        self.assertTrue(history.can_undo())
        self.assertFalse(history.can_redo())
        self.assertEqual(history.redo_count, 0)


if __name__ == "__main__":
    unittest.main()
