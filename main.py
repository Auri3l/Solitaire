"""Solitaire Suite — Native Desktop Application Entry Point.

Supports interactive desktop GUI execution, headless test execution,
and automated smoke validation via CLI arguments.
"""

import argparse
import json
import os
import sys
from typing import Dict, Any

if sys.platform == "win32":
    try:
        import ctypes
        # Attach to parent console if invoked from terminal
        ctypes.windll.kernel32.AttachConsole(-1)
    except Exception:
        pass


def run_smoke_tests() -> int:
    """Executes headless automated smoke tests across all Solitaire variants."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    from solitaire.gui.app import SolitaireApp
    from solitaire.ai.hint_engine import HintEngine
    from solitaire.core.card import Suit, Rank

    print("[SMOKE] Starting Solitaire Suite Headless Verification...")
    results: Dict[str, Any] = {
        "modes_tested": [],
        "all_passed": True,
        "details": {}
    }

    modes = ["klondike1", "klondike3", "freecell", "spider1", "spider2", "spider4"]

    try:
        app = SolitaireApp(mode="klondike1", seed=100, headless=True)

        for mode_key in modes:
            print(f"[SMOKE] Testing mode: {mode_key}...")
            app.switch_mode(mode_key, seed=200)

            # 1. Check layout geometry
            unique_piles = set(app.game.piles.values())
            card_count = sum(len(p.cards) for p in unique_piles)
            expected_min = 52 if "spider" not in mode_key else 104
            assert card_count == expected_min, f"Expected {expected_min} cards, found {card_count}"

            # 2. Render test frame
            app._update(0.016)
            app._draw()

            # 3. Test legal moves and hints
            legal_moves = app.game.get_legal_moves()
            hint = HintEngine.get_hint(app.game)

            # 4. Test move execution & Undo/Redo invariance if moves exist
            moved = False
            if legal_moves:
                test_move = legal_moves[0]
                res = app.game.make_move(test_move)
                if res.success:
                    moved = True
                    # Verify undo
                    assert app.game.can_undo(), "Undo should be available after move"
                    app.game.undo()
                    # Verify redo
                    assert app.game.can_redo(), "Redo should be available after undo"
                    app.game.redo()
                    app.game.undo()

            results["modes_tested"].append(mode_key)
            results["details"][mode_key] = {
                "card_count": card_count,
                "legal_moves_found": len(legal_moves),
                "hint_generated": hint is not None,
                "move_and_undo_verified": moved,
                "status": "PASS"
            }
            print(f"[SMOKE] Mode {mode_key} passed: {len(legal_moves)} legal moves, hint OK={hint is not None}")

        print("\n[SMOKE] All Solitaire Suite modes verified successfully!")
        print(json.dumps(results, indent=2))
        return 0

    except Exception as exc:
        print(f"[SMOKE ERROR] Exception during verification: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main() -> int:
    """Application CLI parser and launcher."""
    parser = argparse.ArgumentParser(
        description="Solitaire Suite — Offline Native Desktop Application"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without creating a display window"
    )
    parser.add_argument(
        "--test-ui-smoke",
        action="store_true",
        help="Execute automated UI and game mode smoke verification"
    )
    parser.add_argument(
        "--mode",
        choices=["klondike1", "klondike3", "freecell", "spider1", "spider2", "spider4"],
        default="klondike1",
        help="Initial game mode (default: klondike1)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Deterministic deal seed"
    )

    args = parser.parse_args()

    if args.test_ui_smoke or (args.headless and not args.mode):
        return run_smoke_tests()

    from solitaire.gui.app import SolitaireApp
    app = SolitaireApp(mode=args.mode, seed=args.seed, headless=args.headless)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
