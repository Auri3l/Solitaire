# Project: Solitaire Game Suite

## Architecture

The Solitaire Game Suite is an offline native desktop application built with Python 3.12, Pygame-ce 2.5.8, and packaged into a standalone single-file Windows executable (`.exe`) using PyInstaller.

The system is organized into decoupled layers:
1. **Core Domain Layer (`solitaire.core`)**:
   - Card models (`Card`, `Suit`, `Rank`, `Color`), Card Collections (`Pile`, `Deck`).
   - Reversible Command Pattern (`MoveCommand`, `CommandHistory`) with inverse deltas $\Delta^{-1}$ guaranteeing exact state and fog-of-war restoration for unlimited multi-step undo/redo.
   - Base game state interface and shared scoring/timing structures.
2. **Game Rules Layer (`solitaire.games`)**:
   - `KlondikeGame`: Turn 1 and Turn 3 dealing, cyclic stock recycling, alternating color tableau builds, partial cascade moves, King-to-empty, foundation stacking (A to K).
   - `FreeCellGame`: 8 cascades, 4 free cells, 4 foundations, exact inductive supermove calculations $(1+N)\cdot 2^K$ (to tableau) and $(1+N)\cdot 2^{K-1}$ (to empty column).
   - `SpiderGame`: 1-suit (104 ♠), 2-suit (52 ♠, 52 ♥), 4-suit (26 ♠, 26 ♥, 26 ♦, 26 ♣), 10 tableau columns, 5 stock deals of 10 with empty column guards, any-suit placement vs same-suit sequence moving, atomic 13-card King-to-Ace foundation clearance.
3. **Solver & Assistance Layer (`solitaire.ai`)**:
   - Hint engine evaluating legal moves with prioritized utility matrices.
   - Safe auto-play to foundations.
   - Auto-finish fast-forward detection when all cards are face up and stock is cleared.
4. **GUI & Rendering Layer (`solitaire.gui`)**:
   - `CardRenderer`: 100% offline procedural vector rendering of suits, pips, court cards (J, Q, K), and ornamental card backs cached to offscreen surfaces.
   - `LayoutManager`: Parametric responsive geometry for Klondike, FreeCell, and Spider with adaptive vertical cascade compression.
   - `InteractionController`: Drag-and-drop with physics, elevation shadows, magnetism, and spring return; click-to-move auto-routing.
   - `AppView`: HUD toolbar, game switcher, new game, restart, undo/redo, score/timer, bouncing cards win celebration animation, and victory modal.
   - `HeadlessController`: CLI flags (`--headless`, `--test-ui-smoke`, `--mode`, `--seed`) for automated CI testing and verification.
5. **Packaging Pipeline (`build_standalone.py` / PyInstaller)**:
   - Standalone single-file Windows PE binary `SolitaireSuite.exe` in project root with zero external runtime dependencies.

---

## Feature Inventory

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Standard Card & Deck Model | 52-card standard deck, suits (♠, ♥, ♦, ♣), ranks (A, 2-10, J, Q, K), card colors, face-up/face-down state | M1 | Survey 1 §2.1 |
| 2 | Multi-Deck Spider Model | 104-card deck supporting 1-suit, 2-suit, and 4-suit configurations with unique instance IDs | M2 | Survey 1 §2.3 |
| 3 | Reversible Command Delta Engine | Undo/Redo history tracking move deltas, uncovered cards, score deltas, allowing unlimited multi-step rollback | M1 | Survey 1 §5 |
| 4 | Klondike Turn-1 Deal | Stock deal 1 card face-up to waste pile; waste top card playable | M1 | Survey 1 §2.1 |
| 5 | Klondike Turn-3 Deal | Stock deal up to 3 cards fanned to waste pile; top card playable | M1 | Survey 1 §2.1 |
| 6 | Klondike Stock Recycling | Reset waste back to stock face-down when stock exhausts; configurable pass limits | M1 | Survey 1 §2.1 |
| 7 | Klondike Tableau Building | Alternating colors (red on black, black on red), descending ranks (K down to A) | M1 | Survey 1 §2.1 |
| 8 | Klondike Partial Sequence Move | Moving any face-up sub-sequence between tableau cascades | M1 | Survey 1 §2.1 |
| 9 | Klondike King to Empty | Only Kings (or sequences starting with King) allowed in empty tableau columns | M1 | Survey 1 §2.1 |
| 10 | Klondike Foundation Stacking | 4 piles by suit, Ace ascending through King | M1 | Survey 1 §2.1 |
| 11 | FreeCell Initial Deal | 52 cards face-up into 8 columns (4 of 7 cards, 4 of 6 cards) | M2 | Survey 1 §2.2 |
| 12 | FreeCell Cell Management | 4 open free cells holding at most 1 card each | M2 | Survey 1 §2.2 |
| 13 | FreeCell Foundation Stacking | 4 suit piles ascending Ace to King | M2 | Survey 1 §2.2 |
| 14 | FreeCell Supermove Formula | Inductive $(1+N)\cdot 2^K$ (to cascade) and $(1+N)\cdot 2^{K-1}$ (to empty column) multi-card validation | M2 | Survey 1 §3 |
| 15 | Spider Initial Deal & Stock | 10 columns (54 cards initial), 50 stock cards in 5 rounds of 10 | M2 | Survey 1 §2.3 |
| 16 | Spider Tableau Building | Any suit placed on rank + 1 | M2 | Survey 1 §2.3 |
| 17 | Spider Sequence Moving | Only descending sequences of the SAME suit can be moved as a stack | M2 | Survey 1 §2.3 |
| 18 | Spider 13-Card Run Clearing | Atomic removal of complete K-to-A same-suit run to foundations (+100 pts) | M2 | Survey 1 §2.3 |
| 19 | Spider Stock Deal Guard | Block stock dealing if any column is empty | M2 | Survey 1 §2.3 |
| 20 | Spider Empty Column Movement | Any card or valid same-suit sequence can be moved to empty column | M2 | Survey 1 §2.3 |
| 21 | Move Validation & Rejection | Strict rejection of illegal moves without corrupting game state | M1, M2 | Survey 1 §4 |
| 22 | Hint Engine | Prioritized legal move generator and evaluator for all game modes | M3 | Survey 1 §6 |
| 23 | Safe Foundation Auto-Play | Automatic progression of safe cards to foundations | M3 | Survey 1 §6 |
| 24 | Auto-Finish Solver | Fast-forward solution when tableau cards are all face up and stock is cleared | M3 | Survey 1 §7 |
| 25 | Win Condition Detection | Immediate trigger of victory state when all cards reach foundations / runs cleared | M1, M2, M3 | Survey 1 §2 |
| 26 | Procedural Card Vector Renderer | Offline 100% self-contained rendering of suits, pips, court cards, and card backs | M4 | Survey 3 §1 |
| 27 | High-DPI Windows Scaling | SetProcessDpiAwareness to ensure crisp rendering on scaled displays | M4 | Survey 3 §1 |
| 28 | Parametric Responsive Layout | Dynamic resizing for Klondike, FreeCell, Spider with adaptive cascade compression | M4 | Survey 3 §2 |
| 29 | Drag-and-Drop Interaction | Card picking, stack trailing, elevation shadows, magnetism, cubic spring bounce-back | M5 | Survey 3 §3 |
| 30 | Smart Click-to-Move | Auto-routing single/double clicks to best legal target (Foundation -> Tableau -> Cell) | M5 | Survey 3 §3 |
| 31 | In-Game Controls & Toolbar | New Game, Restart, Undo, Redo, Hint, Auto-Finish, Game Mode Selector | M5 | Survey 3 §5 |
| 32 | Victory Celebration | Classic ballistic bouncing cards cascade animation + victory dialog | M5 | Survey 3 §5 |
| 33 | Headless Automation CLI | `--headless`, `--test-ui-smoke`, `--seed`, `--mode` with exit code 0 and JSON report | M5 | Survey 3 §6 |
| 34 | Standalone Single-File Binary | Self-contained Windows PE `.exe` (`SolitaireSuite.exe`) via PyInstaller | M6 | Survey 2 §1, §3 |
| 35 | E2E Test Infrastructure & Suite | Comprehensive opaque-box test runner covering Tiers 1-5 passing 100% | E2E_TRACK | Survey 1 & 2 |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Requirement-driven opaque-box test infrastructure & test suites (Tiers 1-4) | none | IN_PROGRESS |
| M1 | M1_CORE_ENGINE | Card models, deck, piles, Klondike rules (Turn 1 & 3), stock recycle, undo/redo delta engine | none | DONE |
| M2 | M2_FREECELL_SPIDER | FreeCell engine (8 cascades, cells, supermove formula) & Spider engine (1/2/4 suits, run clearing, deal guards) | M1 | IN_PROGRESS |
| M3 | M3_HINTS_AUTOPLAY | Hint engine, safe foundation auto-moves, auto-finish solver, win condition detection | M1, M2 | PLANNED |
| M4 | M4_GUI_RENDERER | Pygame-ce window, DPI awareness, offline procedural vector card renderer, responsive board layouts | M1, M2 | PLANNED |
| M5 | M5_UX_INTERACTION | Drag-and-drop, click-to-move, toolbar HUD, game switcher, win cascade animation, CLI headless sanity | M3, M4 | PLANNED |
| M6 | M6_PACKAGING_FINAL | Standalone `.exe` packaging (`SolitaireSuite.exe`), 100% E2E test pass (Tiers 1-4) + Tier 5 adversarial hardening | E2E, M1-M5 | PLANNED |

---

## Interface Contracts

### `solitaire.core` ↔ `solitaire.games`
- `Card(suit: Suit, rank: int, face_up: bool, id: int)`: Immutable or copyable representation.
- `MoveResult`: `dataclass(success: bool, command: Optional[Command], error_message: str)`
- `GameState`: Base abstract class defining:
  - `get_legal_moves() -> List[Move]`
  - `make_move(move: Move) -> MoveResult`
  - `undo_move() -> bool`
  - `redo_move() -> bool`
  - `is_won() -> bool`
  - `can_auto_finish() -> bool`
  - `get_hint() -> Optional[Move]`
  - `restart()`
  - `get_state_snapshot() -> dict`

### `solitaire.games` ↔ `solitaire.gui`
- `LayoutManager.calculate_positions(game_state: GameState, window_width: int, window_height: int) -> LayoutGeometry`
  - Returns bounding boxes for all piles (stock, waste, foundations, cells, cascades) and card vertical offsets.
- `InteractionController.handle_click(pos: Tuple[int, int], game_state: GameState) -> Optional[MoveResult]`
- `InteractionController.handle_drag_start(pos: Tuple[int, int], game_state: GameState) -> Optional[DragContext]`
- `InteractionController.handle_drag_drop(pos: Tuple[int, int], drag_ctx: DragContext, game_state: GameState) -> MoveResult`

### CLI & Automation Contract
- `python -m solitaire --headless --test-ui-smoke --mode [klondike1|klondike3|freecell|spider1|spider2|spider4]`
  - Sets `SDL_VIDEODRIVER=dummy`, initializes engine, simulates card moves, verifies undo/redo, checks win detection, outputs structured JSON to stdout, returns exit code 0 on success.

---

## Code Layout

```
c:/İşler/agrav/Solitaire/
├── SolitaireSuite.exe              # Final standalone single-file Windows executable
├── main.py                         # Application entry point (GUI or CLI flags)
├── build_standalone.py             # Packaging script invoking PyInstaller with proper flags
├── solitaire/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── card.py                 # Suit, Rank, Card, Deck, Pile
│   │   ├── commands.py             # Command deltas, inverse operators, UndoHistory
│   │   └── base_game.py            # Abstract GameState interface
│   ├── games/
│   │   ├── __init__.py
│   │   ├── klondike.py             # Klondike Turn 1 & 3 rules engine
│   │   ├── freecell.py             # FreeCell rules engine & supermove calculator
│   │   └── spider.py               # Spider 1, 2, 4 suits rules engine & run cleaner
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── hint_engine.py          # Heuristic legal move ranker
│   │   └── auto_finish.py          # Fast-forward solver when all cards are face up
│   └── gui/
│       ├── __init__.py
│       ├── card_renderer.py        # 100% offline procedural vector rendering of cards
│       ├── layout.py               # Parametric geometry & adaptive cascade compression
│       ├── interaction.py         # Drag-and-drop physics & smart click-to-move routing
│       ├── app.py                  # Main Pygame-ce desktop application event loop & HUD
│       └── celebration.py          # Ballistic bouncing cards win cascade animation
└── tests/
    ├── __init__.py
    ├── runner.py                   # Unified test runner executing all tiers
    ├── tier1_features/             # Tier 1: Isolated feature verification tests
    ├── tier2_boundaries/           # Tier 2: Boundary value and edge case tests
    ├── tier3_combinations/         # Tier 3: Pairwise and multi-feature interaction tests
    ├── tier4_scenarios/            # Tier 4: Real-world solvable game scenarios
    └── test_headless_smoke.py      # Headless launch and GUI sanity check
```
