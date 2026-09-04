"""Tier 2 Boundary Value Analysis: Pile Container and Boundary Extremes.

Verifies boundary conditions and error limits on card containers:
- Empty pile pop/peek/slice bounds
- Out of range slice indices (negative, >= len)
- remove_from exact boundary (0, len-1, len, len+1)
- Removing non-existent card ID
- Full capacity pile boundaries (e.g. FreeCell cell capacity = 1)
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.pile import Pile, PileType
from solitaire.games.freecell import FreeCellGame
from solitaire.core.base_game import Move


class TestPileContainerBoundaries(unittest.TestCase):
    """BVA: Pile container operational boundaries."""

    def test_empty_pile_pop_raises_index_error(self) -> None:
        """TC-BVA-PILE-01: Popping an empty pile raises IndexError."""
        p = Pile("test_pile", PileType.TABLEAU)
        self.assertTrue(p.is_empty)
        with self.assertRaises(IndexError):
            p.pop()

    def test_empty_pile_peek_returns_none(self) -> None:
        """TC-BVA-PILE-02: Peeking an empty pile safely returns None."""
        p = Pile("test_pile", PileType.TABLEAU)
        self.assertIsNone(p.peek())
        self.assertIsNone(p.peek_at(0))
        self.assertIsNone(p.peek_at(-1))

    def test_slice_out_of_bounds_raises_index_error(self) -> None:
        """TC-BVA-PILE-03: Slicing at negative index or index >= len raises IndexError."""
        p = Pile("test_pile", PileType.TABLEAU)
        c1 = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        p.push(c1)
        self.assertEqual(len(p), 1)

        with self.assertRaises(IndexError):
            p.slice(-1)
        with self.assertRaises(IndexError):
            p.slice(1)  # Index 1 is out of range for length 1
        with self.assertRaises(IndexError):
            p.slice(99)

        # Exact boundary: index 0 works
        res = p.slice(0)
        self.assertEqual(len(res), 1)

    def test_remove_from_extremal_boundaries(self) -> None:
        """TC-BVA-PILE-04: remove_from exact index boundaries [0, len-1, len, len+1]."""
        p = Pile("test_pile", PileType.TABLEAU)
        c1 = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        c2 = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        p.push_many([c1, c2])

        # len+1 should raise IndexError
        with self.assertRaises(IndexError):
            p.remove_from(3)

        # Exact len: removes 0 cards, leaves pile intact
        removed_empty = p.remove_from(2)
        self.assertEqual(len(removed_empty), 0)
        self.assertEqual(len(p), 2)

        # Index len-1: removes top card
        removed_top = p.remove_from(1)
        self.assertEqual(len(removed_top), 1)
        self.assertEqual(removed_top[0], c2)
        self.assertEqual(len(p), 1)

        # Index 0: removes all remaining cards
        removed_all = p.remove_from(0)
        self.assertEqual(len(removed_all), 1)
        self.assertEqual(len(p), 0)

    def test_remove_nonexistent_card_id_raises_value_error(self) -> None:
        """TC-BVA-PILE-05: Removing card ID not present in pile raises ValueError."""
        p = Pile("test_pile", PileType.TABLEAU)
        c = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=10)
        p.push(c)
        with self.assertRaises(ValueError):
            p.remove_card_by_id(999)

    def test_freecell_single_card_capacity_boundary(self) -> None:
        """TC-BVA-PILE-06: Free cell capacity boundary: exactly 1 card accepted, 2nd card rejected."""
        game = FreeCellGame(seed=42)
        top0 = game.cascades[0].peek()
        top1 = game.cascades[1].peek()

        # First card to empty cell succeeds (size becomes 1)
        res1 = game.make_move(Move("cascade_0", "freecell_0", card_id=top0.card_id))
        self.assertTrue(res1.success)
        self.assertEqual(len(game.free_cells[0]), 1)

        # Second card to now-full cell must be strictly rejected
        res2 = game.make_move(Move("cascade_1", "freecell_0", card_id=top1.card_id))
        self.assertFalse(res2.success)
        self.assertEqual(len(game.free_cells[0]), 1)


if __name__ == "__main__":
    unittest.main()
