"""Tier 4 Scenarios: CLI Automation, Headless Smoke Test, and App Lifecycle.

Verifies end-to-end integration scenarios:
- main.py run_smoke_tests() headless verification across all 6 modes.
- SolitaireApp mode switching and event loop lifecycle.
- State snapshot export/inspection integrity across all Solitaire variants.
"""

import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"

from main import run_smoke_tests
from solitaire.gui.app import SolitaireApp
from solitaire.games.klondike import KlondikeGame
from solitaire.games.freecell import FreeCellGame
from solitaire.games.spider import SpiderGame


class TestCliSmokeScenario(unittest.TestCase):
    """Tier 4: CLI automation and application integration scenarios."""

    def test_run_smoke_tests_all_modes_pass(self) -> None:
        """TC-SCEN-CLI-01: main.run_smoke_tests() executes clean headless verification with exit code 0."""
        exit_code = run_smoke_tests()
        self.assertEqual(exit_code, 0)

    def test_solitaire_app_mode_switching(self) -> None:
        """TC-SCEN-CLI-02: SolitaireApp dynamically switches across all 6 game modes."""
        app = SolitaireApp(mode="klondike1", seed=42, headless=True)
        modes = ["klondike1", "klondike3", "freecell", "spider1", "spider2", "spider4"]

        for mode_key in modes:
            app.switch_mode(mode_key, seed=100)
            self.assertEqual(app.current_mode_key, mode_key)
            self.assertIsNotNone(app.game)
            # Update frame
            app._update(0.016)
            app._draw()

    def test_state_snapshot_schema_integrity_all_modes(self) -> None:
        """TC-SCEN-CLI-03: get_state_snapshot() returns valid schema across Klondike, FreeCell, Spider."""
        k = KlondikeGame(seed=1)
        fc = FreeCellGame(seed=2)
        sp = SpiderGame(num_suits=1, seed=3)

        for g in (k, fc, sp):
            snap = g.get_state_snapshot()
            self.assertIn("mode_name", snap)
            self.assertIn("score", snap)
            self.assertIn("moves_count", snap)
            self.assertIn("is_won", snap)
            self.assertIn("piles", snap)
            self.assertIsInstance(snap["piles"], dict)
            self.assertGreater(len(snap["piles"]), 0)


if __name__ == "__main__":
    unittest.main()
