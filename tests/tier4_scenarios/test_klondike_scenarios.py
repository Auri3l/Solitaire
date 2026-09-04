"""Tier 4 Scenarios: Deterministic Klondike Gameplay and Full Victory Sequences.

Verifies end-to-end scenarios:
- Complete victory playout moving last 4 cards to foundations.
- AutoFinishController full fast-forward resolution to victory.
- Seed-based deterministic multi-turn opening playout.
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move, GameStatus
from solitaire.games.klondike import KlondikeGame
from solitaire.ai.auto_finish import AutoFinishController
from solitaire.ai.hint_engine import HintEngine


class TestKlondikeScenarios(unittest.TestCase):
    """Tier 4: Real-world deterministic Klondike scenarios."""

    def test_complete_endgame_victory_sequence(self) -> None:
        """TC-SCEN-KLON-01: Execute final moves to achieve 100% win in Klondike."""
        game = KlondikeGame(seed=42)
        # Clear all piles
        for p in game.piles.values():
            p.clear()

        # 48 cards already placed in foundations (A through Q for all 4 suits)
        card_id = 0
        for f_idx, suit in enumerate([Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]):
            for r in range(1, 13):  # Ace through Queen
                game.foundations[f_idx].push(Card(suit, r, is_face_up=True, card_id=card_id))
                card_id += 1

        self.assertEqual(sum(len(f) for f in game.foundations), 48)
        self.assertFalse(game.is_won())

        # Remaining 4 Kings placed in tableau columns 0, 1, 2, 3
        k_s = Card(Suit.SPADES, Rank.KING, is_face_up=True, card_id=48)
        k_h = Card(Suit.HEARTS, Rank.KING, is_face_up=True, card_id=49)
        k_d = Card(Suit.DIAMONDS, Rank.KING, is_face_up=True, card_id=50)
        k_c = Card(Suit.CLUBS, Rank.KING, is_face_up=True, card_id=51)

        game.tableau[0].push(k_s)
        game.tableau[1].push(k_h)
        game.tableau[2].push(k_d)
        game.tableau[3].push(k_c)

        # Move each King to its respective foundation
        kings = [(0, k_s, "foundation_0"), (1, k_h, "foundation_1"), (2, k_d, "foundation_2"), (3, k_c, "foundation_3")]
        for col_idx, k_card, f_id in kings:
            res = game.make_move(Move(f"tableau_{col_idx}", f_id, card_id=k_card.card_id))
            self.assertTrue(res.success, f"Failed moving King {k_card} to {f_id}")

        # Victory achieved!
        self.assertTrue(game.is_won())
        self.assertEqual(game.game_status, GameStatus.WON)
        self.assertEqual(sum(len(f) for f in game.foundations), 52)

    def test_auto_finish_full_board_fast_forward(self) -> None:
        """TC-SCEN-KLON-02: AutoFinishController runs staged board to 100% victory."""
        game = KlondikeGame(seed=42)
        for p in game.piles.values():
            p.clear()

        # Place 40 cards in foundations (Ace through 10 in all 4 suits)
        card_id = 0
        for f_idx, suit in enumerate([Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]):
            for r in range(1, 11):
                game.foundations[f_idx].push(Card(suit, r, is_face_up=True, card_id=card_id))
                card_id += 1

        # Place remaining court cards (J, Q, K) across tableau columns
        col = 0
        for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
            for r in (Rank.JACK, Rank.QUEEN, Rank.KING):
                game.tableau[col % 7].push(Card(suit, r, is_face_up=True, card_id=card_id))
                card_id += 1
                col += 1

        self.assertEqual(card_id, 52)
        self.assertTrue(game.can_auto_finish())

        # Run auto-finish to completion
        steps, is_won = AutoFinishController.run_to_completion(game, max_steps=50)
        self.assertTrue(is_won)
        self.assertTrue(game.is_won())
        self.assertEqual(sum(len(f) for f in game.foundations), 52)

    def test_multi_turn_deterministic_playout(self) -> None:
        """TC-SCEN-KLON-03: Execute 5 consecutive deterministic legal moves on seeded board."""
        game = KlondikeGame(turn_mode=1, seed=12345)
        moves_executed = 0

        for _ in range(5):
            legal_moves = game.get_legal_moves()
            if legal_moves:
                res = game.make_move(legal_moves[0])
                self.assertTrue(res.success)
                moves_executed += 1
            else:
                res = game.deal_stock()
                if res.success:
                    moves_executed += 1
                else:
                    break

        self.assertEqual(game.moves_count, moves_executed)
        self.assertGreaterEqual(moves_executed, 1)


if __name__ == "__main__":
    unittest.main()
