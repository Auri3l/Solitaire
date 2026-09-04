"""Unit tests for solitaire.core.

Covers Card primitives, Pile container operations, Deck generation/shuffling,
and the Reversible Command Delta Architecture.
"""

import unittest
from typing import List

from solitaire.core.card import Color, Suit, Rank, Card
from solitaire.core.pile import PileType, Pile, Deck
from solitaire.core.commands import (
    Command,
    CardMoveCommand,
    MoveCommand,
    StockDealCommand,
    RecycleCommand,
    CommandHistory,
)
from solitaire.core.base_game import BaseGame, GameStatus, Move, MoveResult


class DummyGame(BaseGame):
    """Minimal mock game for testing commands in isolation."""

    def __init__(self) -> None:
        super().__init__(mode_name="dummy")
        self.piles = {
            "p1": Pile("p1", PileType.TABLEAU),
            "p2": Pile("p2", PileType.TABLEAU),
            "stock": Pile("stock", PileType.STOCK),
            "waste": Pile("waste", PileType.WASTE),
            "foundation_0": Pile("foundation_0", PileType.FOUNDATION),
        }
        self.score = 0
        self.moves_count = 0
        self.recycles_count = 0
        self.passes_through_stock = 1

    def start_new_game(self, seed=None):
        pass

    def restart(self):
        pass

    def get_legal_moves(self):
        return []

    def is_legal_move(self, move):
        return True

    def make_move(self, move):
        return MoveResult.ok()

    def is_won(self):
        return False

    def can_auto_finish(self):
        return False

    def auto_finish_step(self):
        return None

    def get_hint(self):
        return None


class TestCardPrimitives(unittest.TestCase):
    """TC-CORE-001 through TC-CORE-005: Card model and primitives."""

    def test_suit_enumeration_and_colors(self):
        self.assertEqual(len(Suit), 4)
        self.assertEqual(Suit.SPADES.color, Color.BLACK)
        self.assertEqual(Suit.CLUBS.color, Color.BLACK)
        self.assertEqual(Suit.HEARTS.color, Color.RED)
        self.assertEqual(Suit.DIAMONDS.color, Color.RED)

        self.assertTrue(Suit.SPADES.is_black)
        self.assertFalse(Suit.SPADES.is_red)
        self.assertTrue(Suit.HEARTS.is_red)
        self.assertFalse(Suit.HEARTS.is_black)

        self.assertEqual(Suit.SPADES.symbol, "♠")
        self.assertEqual(Suit.HEARTS.symbol, "♥")
        self.assertEqual(Suit.DIAMONDS.symbol, "♦")
        self.assertEqual(Suit.CLUBS.symbol, "♣")

        self.assertEqual(Suit.from_string("spades"), Suit.SPADES)
        self.assertEqual(Suit.from_string("s"), Suit.SPADES)
        self.assertEqual(Suit.from_string("♠"), Suit.SPADES)
        self.assertEqual(Suit.from_string("HEARTS"), Suit.HEARTS)

        with self.assertRaises(ValueError):
            Suit.from_string("invalid_suit")

    def test_rank_enumeration_and_display(self):
        self.assertEqual(len(Rank), 13)
        self.assertEqual(Rank.ACE.value, 1)
        self.assertEqual(Rank.TWO.value, 2)
        self.assertEqual(Rank.TEN.value, 10)
        self.assertEqual(Rank.JACK.value, 11)
        self.assertEqual(Rank.QUEEN.value, 12)
        self.assertEqual(Rank.KING.value, 13)

        self.assertEqual(Rank.ACE.display_str, "A")
        self.assertEqual(Rank.TWO.display_str, "2")
        self.assertEqual(Rank.TEN.display_str, "10")
        self.assertEqual(Rank.JACK.display_str, "J")
        self.assertEqual(Rank.QUEEN.display_str, "Q")
        self.assertEqual(Rank.KING.display_str, "K")

        self.assertTrue(Rank.ACE.is_ace)
        self.assertFalse(Rank.TWO.is_ace)
        self.assertTrue(Rank.KING.is_king)
        self.assertTrue(Rank.JACK.is_face_card)
        self.assertTrue(Rank.QUEEN.is_face_card)
        self.assertTrue(Rank.KING.is_face_card)
        self.assertFalse(Rank.TEN.is_face_card)

        self.assertEqual(Rank.from_string("A"), Rank.ACE)
        self.assertEqual(Rank.from_string("10"), Rank.TEN)
        self.assertEqual(Rank.from_string("k"), Rank.KING)

        with self.assertRaises(ValueError):
            Rank(0)
        with self.assertRaises(ValueError):
            Rank(14)
        with self.assertRaises(ValueError):
            Rank.from_string("Z")

    def test_card_instantiation_and_properties(self):
        c1 = Card(suit=Suit.HEARTS, rank=Rank.QUEEN, card_id=24, is_face_up=True)
        self.assertEqual(c1.card_id, 24)
        self.assertEqual(c1.suit, Suit.HEARTS)
        self.assertEqual(c1.rank, Rank.QUEEN)
        self.assertEqual(c1.color, Color.RED)
        self.assertTrue(c1.is_red)
        self.assertFalse(c1.is_black)
        self.assertTrue(c1.is_face_up)
        self.assertEqual(c1.display_name, "Q♥")
        self.assertEqual(c1.full_name, "Q♥")

        c2 = Card(suit=Suit.SPADES, rank=Rank.ACE, card_id=0, is_face_up=False)
        self.assertEqual(c2.color, Color.BLACK)
        self.assertFalse(c2.is_face_up)
        self.assertEqual(c2.display_name, "??")
        self.assertEqual(c2.full_name, "A♠")

        # Flip
        c2.flip()
        self.assertTrue(c2.is_face_up)
        self.assertEqual(c2.display_name, "A♠")

    def test_card_equality_and_hashing(self):
        ca = Card(suit=Suit.SPADES, rank=Rank.KING, card_id=12, is_face_up=True)
        cb = Card(suit=Suit.SPADES, rank=Rank.KING, card_id=12, is_face_up=False)
        cc = Card(suit=Suit.HEARTS, rank=Rank.KING, card_id=25, is_face_up=True)

        self.assertEqual(ca, cb)
        self.assertNotEqual(ca, cc)
        self.assertEqual(hash(ca), hash(cb))

        card_set = {ca, cb, cc}
        self.assertEqual(len(card_set), 2)
        self.assertIn(ca, card_set)
        self.assertIn(cc, card_set)

        card_dict = {ca: "king_spades", cc: "king_hearts"}
        self.assertEqual(card_dict[cb], "king_spades")

    def test_card_cloning_and_face_state(self):
        orig = Card(suit=Suit.CLUBS, rank=Rank.SEVEN, card_id=6, is_face_up=False)
        clone = orig.clone()

        self.assertEqual(clone.card_id, orig.card_id)
        self.assertEqual(clone.suit, orig.suit)
        self.assertEqual(clone.rank, orig.rank)
        self.assertEqual(clone.is_face_up, orig.is_face_up)

        # Mutate clone
        clone.is_face_up = True
        self.assertTrue(clone.is_face_up)
        self.assertFalse(orig.is_face_up)

    def test_card_serialization(self):
        card = Card(suit=Suit.DIAMONDS, rank=Rank.JACK, card_id=36, is_face_up=True)
        d = card.to_dict()
        restored = Card.from_dict(d)
        self.assertEqual(card, restored)
        self.assertEqual(card.is_face_up, restored.is_face_up)


class TestPileOperations(unittest.TestCase):
    """TC-CORE-006 through TC-CORE-010: Pile container operations."""

    def test_pile_initialization(self):
        p = Pile("tableau_0", PileType.TABLEAU)
        self.assertTrue(p.is_empty)
        self.assertEqual(len(p), 0)
        self.assertEqual(p.cards, ())
        self.assertEqual(p.pile_type, PileType.TABLEAU)
        self.assertEqual(p.pile_id, "tableau_0")

        # Alternate positional argument order
        p2 = Pile(PileType.STOCK, "stock")
        self.assertEqual(p2.pile_type, PileType.STOCK)
        self.assertEqual(p2.pile_id, "stock")

    def test_pile_push_pop_peek(self):
        p = Pile("p1", PileType.TABLEAU)
        c1 = Card(Suit.SPADES, Rank.ACE, card_id=0)
        c2 = Card(Suit.SPADES, Rank.TWO, card_id=1)
        c3 = Card(Suit.SPADES, Rank.THREE, card_id=2)

        p.push(c1)
        p.push(c2)
        p.push(c3)

        self.assertEqual(len(p), 3)
        self.assertEqual(p.peek(), c3)
        self.assertEqual(len(p), 3)  # peek does not remove

        popped = p.pop()
        self.assertEqual(popped, c3)
        self.assertEqual(p.peek(), c2)
        self.assertEqual(len(p), 2)

        self.assertEqual(p.pop(), c2)
        self.assertEqual(p.pop(), c1)
        self.assertTrue(p.is_empty)

    def test_pile_empty_boundaries(self):
        p = Pile("waste", PileType.WASTE)
        self.assertIsNone(p.peek())
        with self.assertRaises(IndexError):
            p.pop()

    def test_pile_slice_and_remove_from(self):
        p = Pile("p1", PileType.TABLEAU)
        cards = [Card(Suit.SPADES, Rank(i), card_id=i) for i in range(1, 6)]
        p.push_many(cards)

        # Slice is non-destructive
        sub = p.slice(2)
        self.assertEqual(len(sub), 3)
        self.assertEqual(sub[0], cards[2])
        self.assertEqual(len(p), 5)

        # remove_from is destructive
        removed = p.remove_from(2)
        self.assertEqual(len(removed), 3)
        self.assertEqual(removed[0], cards[2])
        self.assertEqual(len(p), 2)
        self.assertEqual(p.cards, (cards[0], cards[1]))

    def test_pile_out_of_bounds_protection(self):
        p = Pile("p1", PileType.TABLEAU)
        cards = [Card(Suit.SPADES, Rank(i), card_id=i) for i in range(1, 4)]
        p.push_many(cards)

        with self.assertRaises(IndexError):
            p.slice(3)
        with self.assertRaises(IndexError):
            p.slice(10)
        with self.assertRaises(IndexError):
            p.slice(-1)

        with self.assertRaises(IndexError):
            p.remove_from(10)
        with self.assertRaises(IndexError):
            p.remove_from(-1)

    def test_pile_containment_and_search(self):
        p = Pile("p1", PileType.TABLEAU)
        c1 = Card(Suit.SPADES, Rank.ACE, card_id=0)
        c2 = Card(Suit.HEARTS, Rank.KING, card_id=25)
        p.push(c1)
        p.push(c2)

        self.assertTrue(p.contains_card(0))
        self.assertTrue(p.contains_card(25))
        self.assertFalse(p.contains_card(99))

        self.assertEqual(p.find_card_index(0), 0)
        self.assertEqual(p.find_card_index(25), 1)
        self.assertIsNone(p.find_card_index(99))

        removed = p.remove_card_by_id(0)
        self.assertEqual(removed, c1)
        self.assertEqual(len(p), 1)

    def test_pile_face_counts_and_clear(self):
        p = Pile("p1", PileType.TABLEAU)
        p.push(Card(Suit.SPADES, Rank.ACE, is_face_up=False, card_id=0))
        p.push(Card(Suit.HEARTS, Rank.TWO, is_face_up=True, card_id=14))

        self.assertEqual(p.face_down_count, 1)
        self.assertEqual(p.face_up_count, 1)

        p.clear()
        self.assertTrue(p.is_empty)
        self.assertEqual(p.face_down_count, 0)
        self.assertEqual(p.face_up_count, 0)

    def test_pile_serialization(self):
        p = Pile("tableau_3", PileType.TABLEAU, index=3)
        p.push(Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4))
        d = p.to_dict()
        restored = Pile.from_dict(d)
        self.assertEqual(restored.pile_id, p.pile_id)
        self.assertEqual(restored.pile_type, p.pile_type)
        self.assertEqual(len(restored), len(p))
        self.assertEqual(restored.peek(), p.peek())


class TestDeckOperations(unittest.TestCase):
    """TC-CORE-011 through TC-CORE-013: Deck generation and shuffle."""

    def test_deck_standard_52_cards(self):
        deck = Deck.create_standard()
        self.assertEqual(len(deck), 52)

        ids = [c.card_id for c in deck]
        self.assertEqual(len(set(ids)), 52)
        self.assertEqual(set(ids), set(range(52)))

        for suit in Suit:
            suit_cards = [c for c in deck if c.suit == suit]
            self.assertEqual(len(suit_cards), 13)

        for rank in Rank:
            rank_cards = [c for c in deck if c.rank == rank]
            self.assertEqual(len(rank_cards), 4)

        self.assertTrue(all(not c.is_face_up for c in deck))

    def test_deck_deterministic_seeded_shuffle(self):
        d1 = Deck.create_standard()
        d2 = Deck.create_standard()

        d1.shuffle(seed=42)
        d2.shuffle(seed=42)

        ids1 = [c.card_id for c in d1]
        ids2 = [c.card_id for c in d2]
        self.assertEqual(ids1, ids2)

    def test_deck_distinct_seeds_produce_distinct_permutations(self):
        d1 = Deck.create_standard()
        d2 = Deck.create_standard()

        d1.shuffle(seed=100)
        d2.shuffle(seed=200)

        ids1 = [c.card_id for c in d1]
        ids2 = [c.card_id for c in d2]
        self.assertNotEqual(ids1, ids2)

    def test_deck_draw_until_empty(self):
        deck = Deck.create_standard()
        drawn = []
        while not deck.is_empty:
            drawn.append(deck.draw())

        self.assertEqual(len(drawn), 52)
        self.assertTrue(deck.is_empty)
        with self.assertRaises(IndexError):
            deck.draw()

    def test_deck_spider_deck(self):
        d1 = Deck.create_spider_deck(num_suits=1)
        self.assertEqual(len(d1), 104)
        self.assertTrue(all(c.suit == Suit.SPADES for c in d1))
        self.assertEqual(len(set(c.card_id for c in d1)), 104)

        d2 = Deck.create_spider_deck(num_suits=2)
        self.assertEqual(len(d2), 104)
        spades = sum(1 for c in d2 if c.suit == Suit.SPADES)
        hearts = sum(1 for c in d2 if c.suit == Suit.HEARTS)
        self.assertEqual(spades, 52)
        self.assertEqual(hearts, 52)

        d4 = Deck.create_spider_deck(num_suits=4)
        self.assertEqual(len(d4), 104)


class TestCommandDeltaEngine(unittest.TestCase):
    """TC-CORE-014 through TC-CORE-018: Command delta execution and inversion."""

    def test_move_command_forward_and_inverse(self):
        game = DummyGame()
        c0 = Card(Suit.SPADES, Rank.KING, card_id=12, is_face_up=True)
        c1 = Card(Suit.HEARTS, Rank.QUEEN, card_id=24, is_face_up=True)
        c2 = Card(Suit.CLUBS, Rank.JACK, card_id=49, is_face_up=True)
        c3 = Card(Suit.DIAMONDS, Rank.KING, card_id=38, is_face_up=True)

        game.piles["p1"].push_many([c0, c1, c2])
        game.piles["p2"].push(c3)

        cmd = CardMoveCommand(
            source_pile_id="p1",
            dest_pile_id="p2",
            card_ids=[c1.card_id, c2.card_id],
            nominal_score_delta=5
        )

        # Forward
        success = cmd.execute(game)
        self.assertTrue(success)
        self.assertEqual(len(game.piles["p1"]), 1)
        self.assertEqual(len(game.piles["p2"]), 3)
        self.assertEqual(game.piles["p2"][-1], c2)
        self.assertEqual(game.score, 5)
        self.assertEqual(game.moves_count, 1)

        # Inverse
        undo_res = cmd.undo(game)
        self.assertTrue(undo_res)
        self.assertEqual(len(game.piles["p1"]), 3)
        self.assertEqual(len(game.piles["p2"]), 1)
        self.assertEqual(game.piles["p1"].cards, (c0, c1, c2))
        self.assertEqual(game.piles["p2"].cards, (c3,))
        self.assertEqual(game.score, 0)
        self.assertEqual(game.moves_count, 0)

    def test_move_command_with_uncovered_card_inversion(self):
        game = DummyGame()
        c_hidden = Card(Suit.SPADES, Rank.TEN, card_id=9, is_face_up=False)
        c_top = Card(Suit.HEARTS, Rank.NINE, card_id=21, is_face_up=True)

        game.piles["p1"].push_many([c_hidden, c_top])

        cmd = CardMoveCommand(
            source_pile_id="p1",
            dest_pile_id="p2",
            card_ids=[c_top.card_id],
            uncovered_card_id=c_hidden.card_id,
            nominal_score_delta=10
        )

        cmd.execute(game)
        # c_hidden must be auto-flipped to face-up
        self.assertTrue(c_hidden.is_face_up)
        self.assertEqual(game.score, 10)

        # Undo must restore c_hidden to face-down (fog-of-war)
        cmd.undo(game)
        self.assertFalse(c_hidden.is_face_up)
        self.assertTrue(c_top.is_face_up)
        self.assertEqual(game.score, 0)

    def test_stock_deal_command_forward_and_inverse(self):
        game = DummyGame()
        s0 = Card(Suit.SPADES, Rank.ACE, card_id=0, is_face_up=False)
        s1 = Card(Suit.SPADES, Rank.TWO, card_id=1, is_face_up=False)
        s2 = Card(Suit.SPADES, Rank.THREE, card_id=2, is_face_up=False)
        s3 = Card(Suit.SPADES, Rank.FOUR, card_id=3, is_face_up=False)

        game.piles["stock"].push_many([s0, s1, s2, s3])
        # Deal top 3 cards (s1, s2, s3)
        cards_to_deal = [s1.card_id, s2.card_id, s3.card_id]

        cmd = StockDealCommand(card_ids=cards_to_deal)
        cmd.execute(game)

        self.assertEqual(len(game.piles["stock"]), 1)
        self.assertEqual(len(game.piles["waste"]), 3)
        self.assertTrue(all(c.is_face_up for c in game.piles["waste"]))
        self.assertEqual(game.piles["waste"][-1], s1)
        self.assertEqual(game.piles["waste"][0], s3)

        # Undo
        cmd.undo(game)
        self.assertEqual(len(game.piles["stock"]), 4)
        self.assertEqual(len(game.piles["waste"]), 0)
        self.assertTrue(all(not c.is_face_up for c in game.piles["stock"]))
        self.assertEqual(game.piles["stock"].cards, (s0, s1, s2, s3))

    def test_recycle_command_forward_and_inverse(self):
        game = DummyGame()
        w0 = Card(Suit.SPADES, Rank.ACE, card_id=0, is_face_up=True)
        w1 = Card(Suit.SPADES, Rank.TWO, card_id=1, is_face_up=True)
        w2 = Card(Suit.SPADES, Rank.THREE, card_id=2, is_face_up=True)

        game.piles["waste"].push_many([w0, w1, w2])
        game.score = 100

        cmd = RecycleCommand(nominal_score_delta=-100)
        cmd.execute(game)

        self.assertEqual(len(game.piles["waste"]), 0)
        self.assertEqual(len(game.piles["stock"]), 3)
        self.assertTrue(all(not c.is_face_up for c in game.piles["stock"]))
        # Stock top is w0 (first dealt card in previous pass)
        self.assertEqual(game.piles["stock"][-1], w0)
        self.assertEqual(game.recycles_count, 1)

        # Undo
        cmd.undo(game)
        self.assertEqual(len(game.piles["stock"]), 0)
        self.assertEqual(len(game.piles["waste"]), 3)
        self.assertTrue(all(c.is_face_up for c in game.piles["waste"]))
        self.assertEqual(game.piles["waste"].cards, (w0, w1, w2))
        self.assertEqual(game.recycles_count, 0)
        self.assertEqual(game.score, 100)

    def test_command_history_multi_step_rollback(self):
        game = DummyGame()
        history = CommandHistory()

        c0 = Card(Suit.SPADES, Rank.ACE, card_id=0, is_face_up=True)
        c1 = Card(Suit.HEARTS, Rank.TWO, card_id=14, is_face_up=True)
        game.piles["p1"].push_many([c0, c1])

        cmd1 = CardMoveCommand("p1", "p2", [c1.card_id], nominal_score_delta=5)
        cmd1.execute(game)
        history.push(cmd1)

        self.assertTrue(history.can_undo())
        self.assertFalse(history.can_redo())
        self.assertEqual(history.undo_count, 1)

        cmd2 = CardMoveCommand("p1", "p2", [c0.card_id], nominal_score_delta=10)
        cmd2.execute(game)
        history.push(cmd2)

        self.assertEqual(history.undo_count, 2)
        self.assertEqual(game.score, 15)

        # Undo step 2
        self.assertTrue(history.undo(game))
        self.assertEqual(history.undo_count, 1)
        self.assertTrue(history.can_redo())
        self.assertEqual(game.score, 5)

        # Undo step 1
        self.assertTrue(history.undo(game))
        self.assertFalse(history.can_undo())
        self.assertEqual(game.score, 0)

        # Redo step 1
        self.assertTrue(history.redo(game))
        self.assertEqual(game.score, 5)

        # Redo step 2
        self.assertTrue(history.redo(game))
        self.assertEqual(game.score, 15)

    def test_command_history_redo_invalidation(self):
        game = DummyGame()
        history = CommandHistory()

        c0 = Card(Suit.SPADES, Rank.ACE, card_id=0, is_face_up=True)
        game.piles["p1"].push(c0)

        cmd1 = CardMoveCommand("p1", "p2", [c0.card_id])
        cmd1.execute(game)
        history.push(cmd1)

        # Undo
        history.undo(game)
        self.assertTrue(history.can_redo())

        # Make fresh move -> redo stack must clear
        cmd2 = CardMoveCommand("p1", "p2", [c0.card_id])
        cmd2.execute(game)
        history.push(cmd2)

        self.assertFalse(history.can_redo())
        self.assertEqual(history.redo_count, 0)

    def test_mathematical_delta_invariance_formula(self):
        """Validates Apply(Delta^-1, Apply(Delta, S)) == S across all command types."""
        game = DummyGame()
        initial_snap = game.get_state_snapshot()

        # 1. CardMoveCommand delta invariance
        c1 = Card(Suit.SPADES, Rank.KING, card_id=12, is_face_up=True)
        game.piles["p1"].push(c1)
        snap1 = game.get_state_snapshot()

        cmd_move = CardMoveCommand("p1", "p2", [c1.card_id], nominal_score_delta=10)
        cmd_move.execute(game)
        cmd_move.undo(game)
        self.assertEqual(game.get_state_snapshot(), snap1)

        # 2. StockDealCommand delta invariance
        s1 = Card(Suit.HEARTS, Rank.TWO, card_id=14, is_face_up=False)
        game.piles["stock"].push(s1)
        snap_stock = game.get_state_snapshot()

        cmd_deal = StockDealCommand(count=1)
        cmd_deal.execute(game)
        cmd_deal.undo(game)
        self.assertEqual(game.get_state_snapshot(), snap_stock)

        # 3. RecycleCommand delta invariance
        game.piles["stock"].clear()
        w1 = Card(Suit.CLUBS, Rank.FIVE, card_id=43, is_face_up=True)
        game.piles["waste"].push(w1)
        snap_recycle = game.get_state_snapshot()

        cmd_recycle = RecycleCommand()
        cmd_recycle.execute(game)
        cmd_recycle.undo(game)
        self.assertEqual(game.get_state_snapshot(), snap_recycle)


if __name__ == "__main__":
    unittest.main()
