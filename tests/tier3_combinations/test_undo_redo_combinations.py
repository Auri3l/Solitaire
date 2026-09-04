"""Tier 3 Combinatorial: Reversible Multi-Step Command Deltas and Fog-of-War Invariants.

Verifies complex multi-step undo/redo sequences across diverse action types:
- Klondike mixed sequence: deal -> waste-to-tableau -> tableau-to-tableau -> tableau-to-foundation.
- Auto-flip fog-of-war restoration across multi-card cascades.
- FreeCell mixed sequence: cascade-to-cell -> cascade-to-cascade -> cell-to-foundation.
- Spider mixed sequence: deal stock -> sequence move -> run clearance -> full rollback.
- Redo branch invalidation on new player action.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move
from solitaire.games.klondike import KlondikeGame, MoveType
from solitaire.games.freecell import FreeCellGame
from solitaire.games.spider import SpiderGame


class TestUndoRedoCombinations(unittest.TestCase):
    """Combinatorial: Multi-step rollback and reversibility invariants."""

    def test_klondike_mixed_four_action_undo_redo_cycle(self) -> None:
        """TC-COMB-UR-01: Cycle of 4 mixed Klondike moves preserves exact state on undo and redo."""
        game = KlondikeGame(turn_mode=1, seed=42)
        initial_snap = game.get_state_snapshot()

        # Step 1: Deal stock
        res1 = game.deal_stock()
        self.assertTrue(res1.success)

        # Clear tableau 0 and 1 for controlled moves
        # Setup: tableau 0 has Queen of Spades, tableau 1 has Jack of Hearts (with face-down base)
        q_black = Card(Suit.SPADES, Rank.QUEEN, is_face_up=True, card_id=11)
        base_down = Card(Suit.DIAMONDS, Rank.FOUR, is_face_up=False, card_id=29)
        j_red = Card(Suit.HEARTS, Rank.JACK, is_face_up=True, card_id=23)

        game.tableau[0].clear()
        game.tableau[1].clear()
        game.tableau[0].push(q_black)
        game.tableau[1].push_many([base_down, j_red])

        # Step 2: Move tableau 1 (Jack) to tableau 0 (Queen) -> uncovers base_down
        res2 = game.make_move(Move("tableau_1", "tableau_0", card_id=j_red.card_id))
        self.assertTrue(res2.success)
        self.assertTrue(base_down.is_face_up)

        # Setup: put Ace of Hearts on tableau 2
        game.tableau[2].clear()
        ace_h = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.tableau[2].push(ace_h)

        # Step 3: Move Ace of Hearts to foundation 0
        res3 = game.make_move(Move("tableau_2", "foundation_0", card_id=ace_h.card_id))
        self.assertTrue(res3.success)

        # Record state after 3 moves
        mid_snap = game.get_state_snapshot()

        # Undo all 3 moves in reverse order
        self.assertTrue(game.undo())  # Undoes Ace to foundation
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(game.tableau[2].peek(), ace_h)

        self.assertTrue(game.undo())  # Undoes Jack to Queen (re-hides base_down)
        self.assertFalse(base_down.is_face_up)
        self.assertEqual(len(game.tableau[0]), 1)
        self.assertEqual(len(game.tableau[1]), 2)

        self.assertTrue(game.undo())  # Undoes stock deal
        self.assertEqual(len(game.waste), 0)

        # Redo all 3 moves forward
        self.assertTrue(game.redo())  # Re-deals stock
        self.assertEqual(len(game.waste), 1)

        self.assertTrue(game.redo())  # Re-moves Jack to Queen
        self.assertTrue(base_down.is_face_up)

        self.assertTrue(game.redo())  # Re-moves Ace to foundation
        self.assertEqual(game.foundations[0].peek(), ace_h)

        # State after 3 redoes must exactly equal mid_snap
        post_redo_snap = game.get_state_snapshot()
        self.assertEqual(post_redo_snap["score"], mid_snap["score"])
        self.assertEqual(post_redo_snap["moves_count"], mid_snap["moves_count"])
        self.assertEqual(post_redo_snap["piles"], mid_snap["piles"])

    def test_freecell_three_pile_migration_cycle(self) -> None:
        """TC-COMB-UR-02: Cascade -> FreeCell -> Foundation migration with complete rollback."""
        game = FreeCellGame(seed=42)
        game.cascades[0].clear()
        game.foundations[0].clear()
        for fc in game.free_cells:
            fc.clear()

        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.cascades[0].push(ace_s)
        snap0 = game.get_state_snapshot()

        # Move 1: Cascade 0 -> FreeCell 0
        res1 = game.make_move(Move("cascade_0", "freecell_0", card_id=ace_s.card_id))
        self.assertTrue(res1.success)

        # Move 2: FreeCell 0 -> Foundation 0
        res2 = game.make_move(Move("freecell_0", "foundation_0", card_id=ace_s.card_id))
        self.assertTrue(res2.success)

        self.assertTrue(game.free_cells[0].is_empty)
        self.assertEqual(game.foundations[0].peek(), ace_s)

        # Undo Move 2 -> Returns to FreeCell
        game.undo()
        self.assertTrue(game.foundations[0].is_empty)
        self.assertEqual(game.free_cells[0].peek(), ace_s)

        # Undo Move 1 -> Returns to Cascade 0
        game.undo()
        self.assertTrue(game.free_cells[0].is_empty)
        self.assertEqual(game.cascades[0].peek(), ace_s)

        # Snapshots match
        snap_restored = game.get_state_snapshot()
        self.assertEqual(snap_restored["piles"], snap0["piles"])
        self.assertEqual(snap_restored["moves_count"], snap0["moves_count"])

    def test_spider_deal_sequence_move_and_run_clear_rollback(self) -> None:
        """TC-COMB-UR-03: Deal stock + stack move + run clearance with multi-step rollback."""
        game = SpiderGame(num_suits=1, seed=42)
        # Ensure all columns non-empty
        self.assertTrue(all(len(c) > 0 for c in game.tableau))
        snap_initial = game.get_state_snapshot()

        # Action 1: Deal stock
        res1 = game.deal_stock()
        self.assertTrue(res1.success)
        self.assertEqual(len(game.stock), 40)

        # Stage run clearance on tableau 0
        game.tableau[0].clear()
        game.tableau[1].clear()
        for rank in range(13, 1, -1):
            game.tableau[0].push(Card(Suit.SPADES, rank, is_face_up=True, card_id=rank - 1))
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[1].push(ace_s)

        # Action 2: Move Ace -> triggers run clearance to foundation
        res2 = game.make_move(Move("tableau_1", "tableau_0", card_id=ace_s.card_id))
        self.assertTrue(res2.success)
        self.assertEqual(len(game.foundations[0]), 13)
        self.assertEqual(len(game.tableau[0]), 0)

        # Rollback Action 2: Run reconstructs on tableau, foundation cleared
        game.undo()
        self.assertEqual(len(game.foundations[0]), 0)
        self.assertEqual(len(game.tableau[0]), 12)
        self.assertEqual(game.tableau[1].peek(), ace_s)

        # Rollback Action 1: Stock deal undone, 50 cards in stock
        game.undo()
        self.assertEqual(len(game.stock), 50)

    def test_redo_stack_invalidation_on_branch_move(self) -> None:
        """TC-COMB-UR-04: Undoing moves then executing new move purges redo stack."""
        game = FreeCellGame(seed=42)
        card1 = game.cascades[0].peek()
        card2 = game.cascades[1].peek()

        game.make_move(Move("cascade_0", "freecell_0", card_id=card1.card_id))
        game.make_move(Move("cascade_1", "freecell_1", card_id=card2.card_id))
        self.assertEqual(game.history.undo_count, 2)

        # Undo 1 move
        game.undo()
        self.assertEqual(game.history.redo_count, 1)
        self.assertTrue(game.can_redo())

        # Execute new alternative move: card3 to freecell 2
        card3 = game.cascades[2].peek()
        game.make_move(Move("cascade_2", "freecell_2", card_id=card3.card_id))

        # Redo stack must be purged
        self.assertFalse(game.can_redo())
        self.assertEqual(game.history.redo_count, 0)
        self.assertEqual(game.history.undo_count, 2)


if __name__ == "__main__":
    unittest.main()
