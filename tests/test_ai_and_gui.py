"""Unit and smoke verification for AI solver, GUI renderer, layout, and interaction controllers."""

import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from solitaire.core.card import Card, Suit, Rank
from solitaire.games.klondike import KlondikeGame
from solitaire.games.freecell import FreeCellGame
from solitaire.games.spider import SpiderGame
from solitaire.ai.hint_engine import HintEngine
from solitaire.ai.auto_finish import AutoFinishController
from solitaire.gui.card_renderer import CardRenderer
from solitaire.gui.layout import LayoutManager
from solitaire.gui.interaction import InteractionController
from solitaire.gui.celebration import CelebrationController
from solitaire.gui.app import SolitaireApp


class TestAiAndGuiSuite(unittest.TestCase):
    """Verifies AI and GUI layer functionality."""

    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        pygame.font.init()

    def test_hint_engine_all_modes(self) -> None:
        """Verifies HintEngine produces meaningful hints across all game modes."""
        k1 = KlondikeGame(turn_mode=1, seed=42)
        k1.start_new_game(seed=42)
        h1 = HintEngine.get_hint(k1)
        self.assertIsNotNone(h1)
        self.assertIn("Column", h1.description)

        fc = FreeCellGame(seed=42)
        fc.start_new_game(seed=42)
        h_fc = HintEngine.get_hint(fc)
        self.assertIsNotNone(h_fc)
        self.assertTrue(len(h_fc.description) > 5)

        sp = SpiderGame(num_suits=1, seed=42)
        sp.start_new_game(seed=42)
        h_sp = HintEngine.get_hint(sp)
        self.assertIsNotNone(h_sp)

    def test_auto_finish_controller(self) -> None:
        """Verifies AutoFinishController contracts."""
        k1 = KlondikeGame(turn_mode=1, seed=42)
        k1.start_new_game(seed=42)
        self.assertFalse(AutoFinishController.can_auto_finish(k1))
        res = AutoFinishController.step(k1)
        self.assertIsNone(res)

    def test_card_renderer(self) -> None:
        """Verifies procedural vector card drawing without external files."""
        renderer = CardRenderer()
        # All 4 suits and various ranks
        for suit in Suit:
            for rank in (1, 7, 11, 12, 13):
                c = Card(suit=suit, rank=rank, face_up=True)
                surf = renderer.get_card_surface(c, 80, 112)
                self.assertEqual(surf.get_size(), (80, 112))

        # Face down card back
        c_down = Card(suit=Suit.SPADES, rank=1, face_up=False)
        surf_back = renderer.get_card_surface(c_down, 80, 112)
        self.assertEqual(surf_back.get_size(), (80, 112))

        # Empty pile outlines
        surf_empty_f = renderer.get_empty_pile_surface("foundation", Suit.HEARTS, 80, 112)
        self.assertEqual(surf_empty_f.get_size(), (80, 112))
        surf_empty_c = renderer.get_empty_pile_surface("freecell", None, 80, 112)
        self.assertEqual(surf_empty_c.get_size(), (80, 112))
        surf_empty_s = renderer.get_empty_pile_surface("stock", None, 80, 112)
        self.assertEqual(surf_empty_s.get_size(), (80, 112))

    def test_layout_manager(self) -> None:
        """Verifies responsive layout positioning and hit testing."""
        layout = LayoutManager()
        game = KlondikeGame(turn_mode=1, seed=1)
        game.start_new_game(seed=1)

        layout.update_layout(game, 1200, 800)
        self.assertIn("stock", layout.pile_rects)
        self.assertIn("waste", layout.pile_rects)
        self.assertIn("foundation_0", layout.pile_rects)
        self.assertIn("tableau_0", layout.pile_rects)

        # Hit test stock
        stock_rect = layout.pile_rects["stock"]
        pile_id, card_idx, card = layout.hit_test(stock_rect.centerx, stock_rect.centery, game)
        self.assertEqual(pile_id, "stock")

    def test_interaction_controller(self) -> None:
        """Verifies interaction controller drag initiation and smart clicks."""
        controller = InteractionController()
        layout = LayoutManager()
        game = KlondikeGame(turn_mode=1, seed=1)
        game.start_new_game(seed=1)
        layout.update_layout(game, 1200, 800)

        # Click stock
        stock_rect = layout.pile_rects["stock"]
        res = controller.handle_mouse_down((stock_rect.centerx, stock_rect.centery), game, layout)
        self.assertIsNotNone(res)
        self.assertTrue(res.success)
        self.assertEqual(len(game.get_pile("waste")), 1)

    def test_celebration_controller(self) -> None:
        """Verifies victory animation physics."""
        cel = CelebrationController()
        cel.start([], 1200, 800, 80, 112)
        self.assertTrue(cel.is_active)
        # Simulate 10 frames
        for _ in range(10):
            cel.update(0.05, 1200, 800, 80, 112)
        self.assertTrue(len(cel.bouncing_cards) > 0)
        cel.stop()
        self.assertFalse(cel.is_active)

    def test_solitaire_app_headless(self) -> None:
        """Verifies SolitaireApp desktop lifecycle and game mode switching."""
        app = SolitaireApp(mode="klondike1", seed=42, headless=True)
        self.assertIsNotNone(app.game)

        # Test switching to all modes
        for mode_key in ["klondike1", "klondike3", "freecell", "spider1", "spider2", "spider4"]:
            app.switch_mode(mode_key, seed=99)
            self.assertEqual(app.current_mode_key, mode_key)
            app._update(0.016)
            app._draw()

        # Test undo and redo through app
        legal_moves = app.game.get_legal_moves()
        if legal_moves:
            app.game.make_move(legal_moves[0])
            self.assertTrue(app.game.can_undo())
            app._do_undo()
            self.assertTrue(app.game.can_redo())
            app._do_redo()


if __name__ == "__main__":
    unittest.main()
