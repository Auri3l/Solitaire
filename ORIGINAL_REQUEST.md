# Original User Request

## Initial Request — 2026-09-03T17:08:10+03:00

Build an offline native desktop Solitaire game suite packaged as a single standalone Windows executable, featuring the core Solitaire classics: Klondike (Turn 1 and Turn 3), FreeCell, and Spider (1, 2, and 4 suits).

Working directory: c:/İşler/agrav/Solitaire
Integrity mode: development

## Requirements

### R1. Core Solitaire Game Modes & Rules
Implement full game logic and rule enforcement for the three core Solitaire game types:
- **Klondike**: Support both Turn 1 and Turn 3 dealing from the stock, standard tableau building (descending alternating colors), and foundation building (Ace to King by suit).
- **FreeCell**: Standard 8-column layout, 4 free cells, and 4 foundation piles, enforcing max moveable cards based on empty free cells and cascade columns.
- **Spider**: Support 1-suit (Beginner), 2-suit (Intermediate), and 4-suit (Advanced) variants, dealing rows, tableau sequencing, and completed King-to-Ace runs moving to foundation.

### R2. Desktop Graphical User Interface
Provide a smooth, responsive graphical user interface that runs locally without a web browser:
- Visual card rendering with distinct suits, ranks, and card backs.
- Intuitive card interactions (drag-and-drop and/or click-to-move).
- In-game controls: game mode selector / new game, restart deal, multi-step undo, hint / auto-finish where applicable, and win celebration / game-over dialogs.
- Entirely offline operation with zero internet or remote service dependencies.

### R3. Standalone Single-File Windows Executable
Deliver a self-contained, single-file Windows executable (`.exe`) that runs directly without requiring the user to manually install external runtimes, interpreters, or dependencies.

### R4. Automated Verification Suite
Provide an automated test suite covering:
- Rule validation and legal/illegal move enforcement for Klondike, FreeCell, and Spider.
- State management and undo/redo correctness.
- Automated headless sanity check verifying clean launch and state initialization.

## Acceptance Criteria

### Game Rules & Mechanics
- [ ] Klondike mode correctly enforces Turn-1 and Turn-3 rules, tableau alternation, and foundation stacking.
- [ ] FreeCell mode correctly calculates allowable multi-card movement based on available free cells and cascades.
- [ ] Spider mode correctly supports 1, 2, and 4 suit configurations and cleans full 13-card sequences to foundations.
- [ ] Illegal moves are strictly rejected in all modes without corrupting game state.
- [ ] Multi-step undo correctly restores previous board configurations and scores.

### User Interface & Experience
- [ ] Desktop window displays responsive card layout, smoothly rendering card movements and animations.
- [ ] Players can seamlessly start new games or switch between Klondike, FreeCell, and Spider modes from within the application.
- [ ] Detects win conditions and presents a victory screen or prompt.

### Packaging & Offline Execution
- [ ] Produces a single `.exe` file in the project directory that executes out-of-the-box on Windows.
- [ ] Application launches and plays completely disconnected from the network (no external HTTP calls or assets fetched at runtime).

### Test Suite & Verification
- [ ] Automated rule tests pass 100% with no failures.
- [ ] Automated build script outputs the single executable without compilation or bundling errors.
