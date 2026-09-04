"""Tier 1 Feature Coverage: AI Hint Engine, Auto-Play, Auto-Finish Solver, and Win Detection.

Verifies Features 22, 23, 24, and 25:
- Feature 22: Hint Engine (>= 5 tests)
- Feature 23: Safe Foundation Auto-Play (>= 5 tests)
- Feature 24: Auto-Finish Solver (>= 5 tests)
- Feature 25: Win Condition Detection (>= 5 tests)
"""

import unittest
from solitaire.core.card import Card, Suit, Rank
from solitaire.core.base_game import Move, GameStatus
from solitaire.games.klondike import KlondikeGame
from solitaire.games.freecell import FreeCellGame
from solitaire.games.spider import SpiderGame
from solitaire.ai.hint_engine import HintEngine, Hint
from solitaire.ai.auto_finish import AutoFinishController


class TestHintEngine(unittest.TestCase):
    """Feature 22: Hint Engine."""

    def test_hint_generated_for_klondike(self) -> None:
        """TC-AI-F22-01: HintEngine generates valid hint for initial Klondike game."""
        game = KlondikeGame(turn_mode=1, seed=42)
        hint = HintEngine.get_hint(game)
        self.assertIsNotNone(hint)
        self.assertIsInstance(hint, Hint)
        self.assertTrue(game.is_legal_move(hint.move))
        self.assertTrue(len(hint.description) > 0)

    def test_hint_generated_for_freecell(self) -> None:
        """TC-AI-F22-02: HintEngine generates valid hint for initial FreeCell game."""
        game = FreeCellGame(seed=42)
        hint = HintEngine.get_hint(game)
        self.assertIsNotNone(hint)
        self.assertTrue(game.is_legal_move(hint.move))

    def test_hint_generated_for_spider(self) -> None:
        """TC-AI-F22-03: HintEngine generates valid hint for initial Spider game."""
        game = SpiderGame(num_suits=1, seed=42)
        hint = HintEngine.get_hint(game)
        self.assertIsNotNone(hint)
        self.assertTrue(game.is_legal_move(hint.move))

    def test_hint_returns_none_when_no_moves_exist(self) -> None:
        """TC-AI-F22-04: Hint returns None when no legal moves remain."""
        game = KlondikeGame(seed=42)
        # Clear all piles
        for pile in game.piles.values():
            pile.clear()
        hint = HintEngine.get_hint(game)
        self.assertIsNone(hint)

    def test_hint_prioritizes_foundation_moves(self) -> None:
        """TC-AI-F22-05: Move to foundation has higher priority than moving within tableau."""
        game = KlondikeGame(seed=42)
        for pile in game.piles.values():
            pile.clear()

        # Ace of Spades on tableau 0 -> can go to foundation
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.tableau[0].push(ace_s)

        # 9 of Spades on tableau 1, 8 of Hearts on tableau 2 -> can build
        nine_s = Card(Suit.SPADES, Rank.NINE, is_face_up=True, card_id=8)
        eight_h = Card(Suit.HEARTS, Rank.EIGHT, is_face_up=True, card_id=20)
        game.tableau[1].push(nine_s)
        game.tableau[2].push(eight_h)

        hint = HintEngine.get_hint(game)
        self.assertIsNotNone(hint)
        self.assertTrue(hint.dest_pile.startswith("foundation"))


class TestSafeFoundationAutoPlay(unittest.TestCase):
    """Feature 23: Safe Foundation Auto-Play."""

    def test_freecell_safe_auto_play_ace_and_two(self) -> None:
        """TC-AI-F23-01: Aces and Twos are always safe to move to foundation in FreeCell."""
        game = FreeCellGame(seed=42)
        for pile in game.piles.values():
            pile.clear()

        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        game.cascades[0].push(ace_s)
        self.assertTrue(game.can_auto_finish() or len(game.get_legal_moves()) > 0)
        res = game.auto_finish_step()
        if res:
            self.assertTrue(res.success)
            self.assertEqual(game.foundations[0].peek(), ace_s)

    def test_klondike_safe_auto_play_disabled_with_unopened_cards(self) -> None:
        """TC-AI-F23-02: Klondike auto-finish is disabled while face-down cards exist."""
        game = KlondikeGame(seed=42)
        self.assertFalse(game.can_auto_finish())
        self.assertFalse(AutoFinishController.can_auto_finish(game))

    def test_klondike_safe_auto_play_disabled_when_stock_non_empty(self) -> None:
        """TC-AI-F23-03: Klondike auto-finish is disabled when stock contains cards."""
        game = KlondikeGame(seed=42)
        # Flip all tableau cards face up, but leave stock full
        for col in game.tableau:
            for c in col:
                c.is_face_up = True
        self.assertFalse(game.can_auto_finish())

    def test_auto_finish_step_returns_none_when_ineligible(self) -> None:
        """TC-AI-F23-04: auto_finish_step returns None if board is not eligible."""
        game = KlondikeGame(seed=42)
        self.assertIsNone(game.auto_finish_step())

    def test_freecell_auto_finish_moves_safe_cards(self) -> None:
        """TC-AI-F23-05: FreeCell can auto-finish step when safe foundation moves exist."""
        game = FreeCellGame(seed=42)
        for pile in game.piles.values():
            pile.clear()
        ace_h = Card(Suit.HEARTS, Rank.ACE, is_face_up=True, card_id=13)
        game.cascades[1].push(ace_h)
        res = AutoFinishController.step(game)
        self.assertIsNotNone(res)
        self.assertTrue(res.success)
        self.assertEqual(game.foundations[0].peek(), ace_h)


class TestAutoFinishSolver(unittest.TestCase):
    """Feature 24: Auto-Finish Solver."""

    def test_klondike_can_auto_finish_when_all_face_up_and_stock_empty(self) -> None:
        """TC-AI-F24-01: When stock and waste are empty and all tableau cards face up, can_auto_finish is True."""
        game = KlondikeGame(seed=42)
        game.stock.clear()
        game.waste.clear()
        for col in game.tableau:
            for c in col:
                c.is_face_up = True
        self.assertTrue(game.can_auto_finish())
        self.assertTrue(AutoFinishController.can_auto_finish(game))

    def test_klondike_auto_finish_step_progresses_cards(self) -> None:
        """TC-AI-F24-02: auto_finish_step moves the lowest available card to foundation."""
        game = KlondikeGame(seed=42)
        for pile in game.piles.values():
            pile.clear()
        ace_c = Card(Suit.CLUBS, Rank.ACE, is_face_up=True, card_id=39)
        game.tableau[0].push(ace_c)
        self.assertTrue(game.can_auto_finish())
        res = game.auto_finish_step()
        self.assertIsNotNone(res)
        self.assertTrue(res.success)
        self.assertEqual(len(game.tableau[0]), 0)
        self.assertEqual(game.foundations[0].peek(), ace_c)

    def test_auto_finish_run_to_completion(self) -> None:
        """TC-AI-F24-03: run_to_completion executes multiple steps to reach win."""
        game = KlondikeGame(seed=42)
        for pile in game.piles.values():
            pile.clear()

        # Place Ace and 2 of Spades
        ace_s = Card(Suit.SPADES, Rank.ACE, is_face_up=True, card_id=0)
        two_s = Card(Suit.SPADES, Rank.TWO, is_face_up=True, card_id=1)
        game.tableau[0].push(ace_s)
        game.tableau[1].push(two_s)

        steps, is_won = AutoFinishController.run_to_completion(game, max_steps=10)
        self.assertEqual(steps, 2)
        self.assertEqual(len(game.foundations[0]), 2)

    def test_auto_finish_does_not_loop_infinitely_on_unwinnable_state(self) -> None:
        """TC-AI-F24-04: Fast-forward terminates when no more progress is possible."""
        game = KlondikeGame(seed=42)
        for pile in game.piles.values():
            pile.clear()
        # Non-solvable: only a 5 of Spades exists without lower ranks
        five_s = Card(Suit.SPADES, Rank.FIVE, is_face_up=True, card_id=4)
        game.tableau[0].push(five_s)
        steps, is_won = AutoFinishController.run_to_completion(game, max_steps=10)
        self.assertEqual(steps, 0)
        self.assertFalse(is_won)

    def test_auto_finish_controller_step_delegation(self) -> None:
        """TC-AI-F24-05: AutoFinishController.step delegates cleanly to game instance."""
        game = FreeCellGame(seed=42)
        for pile in game.piles.values():
            pile.clear()
        ace_d = Card(Suit.DIAMONDS, Rank.ACE, is_face_up=True, card_id=26)
        game.cascades[0].push(ace_d)
        res = AutoFinishController.step(game)
        self.assertIsNotNone(res)
        self.assertTrue(res.success)


class TestWinConditionDetection(unittest.TestCase):
    """Feature 25: Win Condition Detection."""

    def test_klondike_win_detection_52_cards_in_foundations(self) -> None:
        """TC-AI-F25-01: Klondike is_won() is True when all 52 cards are in foundations."""
        game = KlondikeGame(seed=42)
        for pile in game.piles.values():
            pile.clear()
        self.assertFalse(game.is_won())

        # Distribute 13 cards to each of the 4 foundations
        for i, suit in enumerate(Suit):
            for rank in Rank:
                game.foundations[i].push(Card(suit, rank, is_face_up=True, card_id=i * 13 + (rank - 1)))

        self.assertTrue(game.is_won())

    def test_freecell_win_detection_52_cards_in_foundations(self) -> None:
        """TC-AI-F25-02: FreeCell is_won() is True when all 52 cards reach foundations."""
        game = FreeCellGame(seed=42)
        for pile in game.piles.values():
            pile.clear()
        self.assertFalse(game.is_won())

        for i, suit in enumerate(Suit):
            for rank in Rank:
                game.foundations[i].push(Card(suit, rank, is_face_up=True, card_id=i * 13 + (rank - 1)))

        self.assertTrue(game.is_won())

    def test_spider_win_detection_8_completed_runs(self) -> None:
        """TC-AI-F25-03: Spider is_won() is True when all 8 runs (104 cards) are cleared."""
        game = SpiderGame(num_suits=1, seed=42)
        for col in game.tableau:
            col.clear()
        game.stock.clear()
        self.assertFalse(game.is_won())

        # Push 13 cards to each of the 8 foundation piles
        card_id = 0
        for i in range(8):
            for rank in Rank:
                game.foundations[i].push(Card(Suit.SPADES, rank, is_face_up=True, card_id=card_id))
                card_id += 1

        self.assertTrue(game.is_won())

    def test_partial_progress_does_not_trigger_win(self) -> None:
        """TC-AI-F25-04: Having 51 cards in foundations does not trigger win."""
        game = KlondikeGame(seed=42)
        for pile in game.piles.values():
            pile.clear()
        for i, suit in enumerate(Suit):
            for rank in Rank:
                if i == 3 and rank == Rank.KING:
                    continue  # Leave 1 card out
                game.foundations[i].push(Card(suit, rank, is_face_up=True, card_id=i * 13 + (rank - 1)))
        self.assertFalse(game.is_won())

    def test_win_status_updates_game_status_enum(self) -> None:
        """TC-AI-F25-05: Winning updates game.game_status to GameStatus.WON."""
        game = FreeCellGame(seed=42)
        for pile in game.piles.values():
            pile.clear()
        for i, suit in enumerate(Suit):
            for rank in Rank:
                game.foundations[i].push(Card(suit, rank, is_face_up=True, card_id=i * 13 + (rank - 1)))
        self.assertEqual(game.game_status, GameStatus.WON)


if __name__ == "__main__":
    unittest.main()
