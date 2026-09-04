# 🃏 Solitaire Suite

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Pygame-ce](https://img.shields.io/badge/pygame--ce-2.5.8-green.svg)](https://pyga.me/)
[![Platform Windows](https://img.shields.io/badge/platform-Windows%20x64-lightgrey.svg)]()
[![Tests 437/437 Passed](https://img.shields.io/badge/tests-437%2F437%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A fully offline, native desktop Solitaire game suite packaged as a single standalone Windows executable (`SolitaireSuite.exe`). Features the complete core classics: **Klondike** (Turn 1 & Turn 3), **FreeCell**, and **Spider** (1, 2, and 4 suits), rendered with 100% offline procedural vector graphics.

---

## 📥 Download Standalone Game

You can download the ready-to-run Windows executable from the [Releases](https://github.com/Auri3l/Solitaire/releases) tab:

- 🎮 **Download**: [`SolitaireSuite.exe`](https://github.com/Auri3l/Solitaire/releases/latest/download/SolitaireSuite.exe) (~83.6 MB)
- **Zero Installation**: Single self-contained Windows executable. No Python, no installers, and no network connection required. Just download and double-click to play!

---

## 🎮 Included Game Modes

| Mode | Variants | Key Rules & Mechanics |
|---|---|---|
| **Klondike** | Turn 1 & Turn 3 | Alternating color descending tableau builds, cyclic stock recycling, King-to-empty, suit foundations (Ace to King). |
| **FreeCell** | 8 Cascades, 4 Free Cells, 4 Foundations | Mathematical multi-card supermove capacity calculation `(1 + N) * 2^K`, auto-foundation routing, safe cascade moves. |
| **Spider** | 1 Suit (Easy)<br>2 Suits (Medium)<br>4 Suits (Hard) | 104-card deck, 10 columns, stock deals with empty column guards, descending sequence building, atomic 13-card King-to-Ace clearance to foundation (+100 pts). |

---

## ✨ Features

- **Procedural Vector Card Renderer**:
  - High-DPI crisp card faces, suits (♠, ♥, ♦, ♣), ranks, court cards (J, Q, K), and ornamental card backs drawn entirely via vector geometry.
  - Zero external image files or fonts required; 100% self-contained and offline.
- **Fluid Desktop Physics & Controls**:
  - **Drag & Drop**: Multi-card dragging with elevation soft drop shadows, magnetism, and smooth spring-back.
  - **Smart Click-to-Move**: Click cards to auto-route them to the best legal destination (Foundation $\to$ Tableau $\to$ Free Cell), or click stock to deal.
- **In-Game HUD Toolbar**:
  - In-game Mode Selector dropdown allowing seamless switching between all 6 modes anytime.
  - **New Game** & **Restart Deal**: Deal fresh random/seeded boards or retry the current deal.
  - **Unlimited Undo (`Ctrl+Z`) / Redo (`Ctrl+Y`)**: Reversible delta command history with exact fog-of-war invariance.
  - **Heuristic Hint Engine (`H`)**: Highlights legal moves with animated gold/cyan visual glow.
  - **Auto-Finish Solver (`F`)**: Fast-forwards safe cards to foundations once the game reaches a deterministic win state.
  - Live HUD Stats: Timer (`MM:SS`), Move counter, and Live Score.
- **Classic Victory Animation**:
  - Ballistic bouncing card cascade celebration across floor and walls (the iconic Windows Solitaire effect), followed by a victory stats dialog.

---

## ⌨️ Controls & Shortcuts

- **Mouse Drag**: Drag single cards or valid sequences between piles.
- **Single Click**: Smart click-to-move (auto-places card on foundation or best cascade). Click stock to deal.
- **Z** or **Ctrl+Z**: Undo last move
- **Y** or **Ctrl+Y**: Redo move
- **H**: Get Hint
- **N**: New Game
- **R**: Restart Current Deal
- **F**: Auto-Finish
- **1 – 6**: Quick switch between modes:
  - `1`: Klondike (Turn 1)
  - `2`: Klondike (Turn 3)
  - `3`: FreeCell
  - `4`: Spider (1 Suit)
  - `5`: Spider (2 Suits)
  - `6`: Spider (4 Suits)
- **Esc**: Close menus / clear hint

---

## 🛠️ Running from Source

### Prerequisites
- Python 3.10+ (tested with Python 3.12)
- `pygame-ce` (Community Edition):
  ```bash
  pip install pygame-ce
  ```

### Launch
```bash
# Interactive GUI window
python main.py

# Or package launch
python -m solitaire

# Launch directly in a specific mode
python main.py --mode freecell --seed 42
```

---

## 🧪 Automated Testing & Verification

The suite includes an extensive test harness covering game rules, boundary cases, adversarial invariant fuzzing, AI hint engine, and headless GUI smoke testing:

```bash
# Run all 437 unit & invariant tests
python -m unittest discover -s tests -v

# Run the unified multi-tier test runner (195 tests)
python tests/runner.py

# Run automated headless smoke verification across all 6 modes
python -m solitaire --headless --test-ui-smoke
```

---

## 📦 Building the Standalone Executable

To compile `SolitaireSuite.exe` from source:

```bash
# Install PyInstaller
pip install pyinstaller

# Run packaging pipeline
python build_standalone.py
```

The self-contained binary `SolitaireSuite.exe` will be generated in the project root directory.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
