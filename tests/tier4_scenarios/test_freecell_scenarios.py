"""Tier 4 Scenarios: Deterministic FreeCell Gameplay and Full Victory Sequences.

Verifies end-to-end FreeCell scenarios:
- Complete victory playout moving remaining cards to foundations.
- AutoFinishController full board resolution to 100% win.
- Microsoft FreeCell Game deal execution.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move, GameStatus
from solitaire.games.freecell import FreeCellGame
from solitaire.ai.auto_finish import AutoFinishController


class TestFreeCellScenarios(unittest.TestCase):
    """Tier 4: Real-world deterministic FreeCell scenarios."""

    def test_complete_freecell_victory_playout(self) -> None:
        """TC-SCEN-FC-01: Execute final sequence of moves to achieve 100% FreeCell victory."""
        game = FreeCellGame(seed=42)
        for p in game.piles.values():
            p.clear()

        # 48 cards already placed in foundations (A..Q in all 4 suits)
        card_id = 0
        for f_idx, suit in enumerate([Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]):
            for r in range(1, 13):
                game.foundations[f_idx].push(Card(suit, r, is_face_up=True, card_id=card_id))
                card_id += 1

        self.assertFalse(game.is_won())

        # Place the 4 Kings in FreeCells 0, 1, 2, 3
        k_s = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=48)
        k_h = Card(Suit.HEARTS, Rank.KING, is_face_up=True, card_id=49)
        k_d = Card(Suit.DIAMONDS, Rank.KING, is_face_up=True, card_id=50)
        k_c = Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=51)

        game.free_cells[0].push(k_s)
        game.free_cells[1].push(k_h)
        game.free_cells[2].push(k_d)
        game.free_cells[3].push(k_c)

        # Move Kings from FreeCells to respective foundations
        moves = [
            (0, k_s, "foundation_0"),
            (1, k_h, "foundation_1"),
            (2, k_d, "foundation_2"),
            (3, k_c, "foundation_3"),
        ]
        for cell_idx, card, f_id in moves:
            res = game.make_move(Move(f"freecell_{cell_idx}", f_id, card_id=card.card_id))
            self.assertTrue(res.success)

        self.assertTrue(game.is_won())
        self.assertEqual(game.game_status, GameStatus.WON)
        self.assertEqual(sum(len(f) for f in game.foundations), 52)
        self.assertTrue(all(fc.is_empty for fc in game.free_cells))

    def test_auto_finish_full_freecell_resolution(self) -> None:
        """TC-SCEN-FC-02: AutoFinishController steps FreeCell board to victory."""
        game = FreeCellGame(seed=42)
        for p in game.piles.values():
            p.clear()

        # Place 40 cards in foundations (Ace through 10 in all 4 suits)
        card_id = 0
        for f_idx, suit in enumerate([Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]):
            for r in range(1, 11):
                game.foundations[f_idx].push(Card(suit, r, is_face_up=True, card_id=card_id))
                card_id += 1

        # Place remaining court cards (K at base, then Q, then J at top) so J is accessible
        col = 0
        for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
            for r in (Rank.KING, Rank.QUEEN, Rank.JACK):
                game.cascades[col % 8].push(Card(suit, r, is_face_up=True, card_id=card_id))
                card_id += 1
            col += 1

        steps, is_won = AutoFinishController.run_to_completion(game, max_steps=50)
        self.assertTrue(is_won)
        self.assertTrue(game.is_won())
        self.assertEqual(sum(len(f) for f in game.foundations), 52)

    def test_microsoft_freecell_deal_playout(self) -> None:
        """TC-SCEN-FC-03: Microsoft Deal #1 opening moves simulation."""
        game = FreeCellGame(ms_game_number=1)
        self.assertEqual(sum(len(c) for c in game.cascades), 52)

        # Execute opening moves available
        legal_moves = game.get_legal_moves()
        self.assertGreater(len(legal_moves), 0)

        # Play up to 3 legal moves
        for _ in range(3):
            moves = game.get_legal_moves()
            if not moves:
                break
            res = game.make_move(moves[0])
            self.assertTrue(res.success)

        self.assertGreaterEqual(game.moves_count, 1)


if __name__ == "__main__":
    unittest.main()
