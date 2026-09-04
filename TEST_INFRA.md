# Solitaire Suite — E2E Test Infrastructure Specification

## 1. Overview & Testing Philosophy

The Solitaire Game Suite testing infrastructure implements a strict, requirement-driven, opaque-box verification framework. The test architecture is structured to validate all functional, non-functional, and invariant requirements established in `ORIGINAL_REQUEST.md` and `PROJECT.md` across Klondike (Turn 1 & 3), FreeCell, and Spider (1, 2, and 4 suits).

### Core Testing Principles
1. **Opaque-Box Verification**: Tests interact strictly through public interfaces, game actions (`make_move`, `deal_stock`, `undo`, `redo`, `start_new_game`), and observable game states (`get_legal_moves`, `is_won`, `get_state_snapshot`, `can_undo`, `can_redo`).
2. **Deterministic Independence**: Every test case initializes its own state, seeds RNG explicitly where randomness is involved, does not rely on execution order, and operates with zero shared mutable fixtures.
3. **Reversibility Invariant Enforcement**: Every state mutation is validated against the fundamental command delta theorem:
   $$\text{Apply}(\Delta^{-1}, \text{Apply}(\Delta, S)) \equiv S$$
   guaranteeing zero drift in pile arrangements, card visibility (fog-of-war), move counters, and scores.
4. **Authoritative Ground-Truth Oracles**: Expected outputs are derived directly from mathematical theorems (e.g. FreeCell supermove combinatorial formulas $(1+N)\cdot 2^K$) and official Solitaire rulebooks rather than implementation internals.

---

## 2. Multi-Tier Test Suite Architecture

The test suite is partitioned into four progressive tiers:

```
tests/
├── runner.py                     # Unified multi-tier test runner CLI
├── tier1_features/               # Tier 1: Feature Coverage (>=5 tests per feature)
│   ├── test_core_features.py
│   ├── test_klondike_features.py
│   ├── test_freecell_features.py
│   ├── test_spider_features.py
│   └── test_solver_features.py
├── tier2_boundaries/             # Tier 2: Boundary Value Analysis (BVA & limits)
│   ├── test_pile_boundaries.py
│   ├── test_supermove_boundaries.py
│   ├── test_dealing_guard_boundaries.py
│   ├── test_rank_sequence_boundaries.py
│   └── test_spider_run_boundaries.py
├── tier3_combinations/           # Tier 3: Combinations & Cross-Feature Interactions
│   ├── test_undo_redo_combinations.py
│   ├── test_stock_tableau_interactions.py
│   ├── test_cross_pile_combinations.py
│   ├── test_spider_multisuit_interactions.py
│   └── test_scoring_and_metrics_invariants.py
└── tier4_scenarios/              # Tier 4: Real-World Solvable Scenarios
    ├── test_klondike_scenarios.py
    ├── test_freecell_scenarios.py
    ├── test_spider_scenarios.py
    └── test_cli_smoke_scenario.py
```

### Tier Descriptions & Acceptance Criteria

| Tier | Focus | Target Scope | Minimum Threshold |
|------|-------|--------------|-------------------|
| **Tier 1: Feature Coverage** | Happy paths and primary rule contracts | All core card models, piles, command deltas, Klondike rules, FreeCell rules, Spider rules, hint engine, win detection | $\ge 5$ tests per feature, 100% pass |
| **Tier 2: Boundary Value Analysis** | Edge cases, extremal values, limits | Empty/full piles, supermove upper/lower bounds, dealing guards, sequence rank bounds, run completion boundaries | $\ge 5$ tests per feature, 100% pass |
| **Tier 3: Combinations & Interactions** | Cross-feature interactions and invariants | Multi-move undo/redo sequences, stock recycling interleaved with tableau building, cross-pile migrations, multi-suit Spider | Pairwise & multi-step sequences, 100% pass |
| **Tier 4: Real-World Scenarios** | End-to-end solvable gameplay & systems | Full deterministic winnable games, auto-finish fast-forward to victory, CLI headless automated smoke test | Complete scenario execution, 100% pass |

---

## 3. Feature Inventory Mapping

| Feature # | Feature Name | Primary Tier 1 Test File | Boundary & Edge Cases (Tier 2/3/4) |
|---|---|---|---|
| 1 | Standard Card & Deck Model | `tier1_features/test_core_features.py` | `tier2_boundaries/test_rank_sequence_boundaries.py` |
| 2 | Multi-Deck Spider Model | `tier1_features/test_core_features.py` | `tier2_boundaries/test_dealing_guard_boundaries.py` |
| 3 | Reversible Command Delta Engine | `tier1_features/test_core_features.py` | `tier3_combinations/test_undo_redo_combinations.py` |
| 4 | Klondike Turn-1 Deal | `tier1_features/test_klondike_features.py` | `tier2_boundaries/test_dealing_guard_boundaries.py` |
| 5 | Klondike Turn-3 Deal | `tier1_features/test_klondike_features.py` | `tier2_boundaries/test_dealing_guard_boundaries.py` |
| 6 | Klondike Stock Recycling | `tier1_features/test_klondike_features.py` | `tier3_combinations/test_stock_tableau_interactions.py` |
| 7 | Klondike Tableau Building | `tier1_features/test_klondike_features.py` | `tier2_boundaries/test_rank_sequence_boundaries.py` |
| 8 | Klondike Partial Sequence Move | `tier1_features/test_klondike_features.py` | `tier3_combinations/test_cross_pile_combinations.py` |
| 9 | Klondike King to Empty | `tier1_features/test_klondike_features.py` | `tier2_boundaries/test_rank_sequence_boundaries.py` |
| 10 | Klondike Foundation Stacking | `tier1_features/test_klondike_features.py` | `tier4_scenarios/test_klondike_scenarios.py` |
| 11 | FreeCell Initial Deal | `tier1_features/test_freecell_features.py` | `tier4_scenarios/test_freecell_scenarios.py` |
| 12 | FreeCell Cell Management | `tier1_features/test_freecell_features.py` | `tier2_boundaries/test_pile_boundaries.py` |
| 13 | FreeCell Foundation Stacking | `tier1_features/test_freecell_features.py` | `tier4_scenarios/test_freecell_scenarios.py` |
| 14 | FreeCell Supermove Formula | `tier1_features/test_freecell_features.py` | `tier2_boundaries/test_supermove_boundaries.py` |
| 15 | Spider Initial Deal & Stock | `tier1_features/test_spider_features.py` | `tier2_boundaries/test_dealing_guard_boundaries.py` |
| 16 | Spider Tableau Building | `tier1_features/test_spider_features.py` | `tier3_combinations/test_spider_multisuit_interactions.py` |
| 17 | Spider Sequence Moving | `tier1_features/test_spider_features.py` | `tier2_boundaries/test_spider_run_boundaries.py` |
| 18 | Spider 13-Card Run Clearing | `tier1_features/test_spider_features.py` | `tier2_boundaries/test_spider_run_boundaries.py` |
| 19 | Spider Stock Deal Guard | `tier1_features/test_spider_features.py` | `tier2_boundaries/test_dealing_guard_boundaries.py` |
| 20 | Spider Empty Column Movement | `tier1_features/test_spider_features.py` | `tier2_boundaries/test_rank_sequence_boundaries.py` |
| 21 | Move Validation & Rejection | All `test_*_features.py` | All `tier2_boundaries/` test files |
| 22 | Hint Engine | `tier1_features/test_solver_features.py` | `tier3_combinations/test_cross_pile_combinations.py` |
| 23 | Safe Foundation Auto-Play | `tier1_features/test_solver_features.py` | `tier4_scenarios/test_freecell_scenarios.py` |
| 24 | Auto-Finish Solver | `tier1_features/test_solver_features.py` | `tier4_scenarios/test_klondike_scenarios.py` |
| 25 | Win Condition Detection | `tier1_features/test_solver_features.py` | `tier4_scenarios/` (all files) |
| 33 | Headless Automation CLI | `tier4_scenarios/test_cli_smoke_scenario.py` | `tier4_scenarios/test_cli_smoke_scenario.py` |

---

## 4. Test Runner Specification (`tests/runner.py`)

The unified test runner supports flexible CLI execution modes:

```bash
# Run all test tiers (Tiers 1-4)
python tests/runner.py

# Run a specific tier
python tests/runner.py --tier 1
python tests/runner.py --tier 2
python tests/runner.py --tier 3
python tests/runner.py --tier 4

# Filter tests by substring / pattern
python tests/runner.py -k supermove
python tests/runner.py --pattern test_klondike*

# Verbose execution with full test names
python tests/runner.py -v

# Output JSON report for automated integration
python tests/runner.py --json
```

### Exit Code Contracts
- Exit code `0`: All executed tests passed without errors or failures.
- Exit code `1`: One or more tests failed or encountered an error.

---

## 5. Verification & Acceptance Thresholds

1. **Pass Rate**: 100% pass across all tiers. Zero expected failures.
2. **Execution Time**: The complete test suite across Tiers 1-4 must execute in under 15 seconds.
3. **No Mocks Policy**: All tests exercise real domain classes (`Card`, `Pile`, `KlondikeGame`, `FreeCellGame`, `SpiderGame`, `HintEngine`, `AutoFinishController`, `SolitaireApp`). Mocking or monkey-patching game rules is strictly prohibited.
