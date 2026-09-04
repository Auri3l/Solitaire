"""Unified Multi-Tier Test Runner for Solitaire Suite.

Executes and coordinates opaque-box test suites across Tiers 1-4:
- Tier 1: Feature Coverage (tests/tier1_features)
- Tier 2: Boundary Value Analysis (tests/tier2_boundaries)
- Tier 3: Cross-Feature Combinations (tests/tier3_combinations)
- Tier 4: Real-World Solvable Scenarios (tests/tier4_scenarios)

CLI Usage:
    python tests/runner.py
    python tests/runner.py --tier 1
    python tests/runner.py --tier 2
    python tests/runner.py --tier 3
    python tests/runner.py --tier 4
    python tests/runner.py -k supermove
    python tests/runner.py -v
    python tests/runner.py --json
"""

import argparse
import io
import json
import os
import sys
import time
import unittest
from typing import Dict, List, Any, Optional, Tuple

# Ensure project root is in sys.path so modules can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Enable headless SDL video driver for automated testing
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Determine terminal color support
USE_COLOR = sys.stdout.isatty() or os.environ.get("FORCE_COLOR") == "1"


def _color(text: str, code: str) -> str:
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def green(text: str) -> str:
    return _color(text, "92")


def red(text: str) -> str:
    return _color(text, "91")


def yellow(text: str) -> str:
    return _color(text, "93")


def cyan(text: str) -> str:
    return _color(text, "96")


def bold(text: str) -> str:
    return _color(text, "1")


class TierResult:
    """Stores execution metrics for a test tier."""

    def __init__(self, tier_id: str, name: str) -> None:
        self.tier_id = tier_id
        self.name = name
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.skipped = 0
        self.duration = 0.0
        self.failure_details: List[str] = []

    @property
    def is_success(self) -> bool:
        return self.failed == 0 and self.errors == 0


def filter_suite(suite: unittest.TestSuite, pattern: str) -> unittest.TestSuite:
    """Recursively filters test cases matching substring pattern."""
    filtered = unittest.TestSuite()
    pattern_lower = pattern.lower()
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            sub = filter_suite(item, pattern)
            if sub.countTestCases() > 0:
                filtered.addTest(sub)
        elif isinstance(item, unittest.TestCase):
            test_id = item.id().lower()
            if pattern_lower in test_id:
                filtered.addTest(item)
    return filtered


def run_tier(
    tier_id: str,
    tier_name: str,
    tier_dir: str,
    pattern: Optional[str] = None,
    verbose: bool = False
) -> TierResult:
    """Discovers and runs test cases within a tier directory."""
    result_data = TierResult(tier_id, tier_name)
    loader = unittest.TestLoader()

    # Discover tests in target directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(base_dir, tier_dir)
    if not os.path.exists(target_path):
        result_data.errors += 1
        result_data.failure_details.append(f"Directory not found: {target_path}")
        return result_data

    suite = loader.discover(target_path, pattern="test_*.py")

    if pattern:
        suite = filter_suite(suite, pattern)

    result_data.total = suite.countTestCases()
    if result_data.total == 0:
        return result_data

    stream = io.StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2 if verbose else 1,
        resultclass=unittest.TextTestResult
    )

    start_time = time.time()
    test_res = runner.run(suite)
    result_data.duration = time.time() - start_time

    result_data.failed = len(test_res.failures)
    result_data.errors = len(test_res.errors)
    result_data.skipped = len(test_res.skipped)
    result_data.passed = (
        result_data.total - result_data.failed - result_data.errors - result_data.skipped
    )

    for test_case, trace in test_res.failures:
        result_data.failure_details.append(f"[FAIL] {test_case.id()}:\n{trace}")

    for test_case, trace in test_res.errors:
        result_data.failure_details.append(f"[ERROR] {test_case.id()}:\n{trace}")

    return result_data


def print_summary_table(results: List[TierResult], total_duration: float) -> None:
    """Renders formatted multi-tier summary table to stdout."""
    print("\n" + bold(cyan("=" * 80)))
    print(bold(cyan("           SOLITAIRE SUITE — MULTI-TIER E2E TEST EXECUTION SUMMARY")))
    print(bold(cyan("=" * 80)))

    header = f"{'Tier':<8} | {'Description':<32} | {'Tests':<6} | {'Pass':<6} | {'Fail':<6} | {'Time':<8} | {'Status'}"
    print(bold(header))
    print("-" * 80)

    grand_total = sum(r.total for r in results)
    grand_passed = sum(r.passed for r in results)
    grand_failed = sum(r.failed for r in results)
    grand_errors = sum(r.errors for r in results)

    for r in results:
        status_str = green("PASS") if r.is_success and r.total > 0 else (yellow("NO TESTS") if r.total == 0 else red("FAIL"))
        print(
            f"{r.tier_id:<8} | {r.name:<32} | {r.total:<6} | {r.passed:<6} | {r.failed + r.errors:<6} | {r.duration:5.3f}s   | {status_str}"
        )

    print("-" * 80)
    total_status = green("PASS (100%)") if (grand_failed == 0 and grand_errors == 0 and grand_total > 0) else red("FAILED")
    print(
        f"{'TOTAL':<8} | {'All Tiers Combined':<32} | {grand_total:<6} | {grand_passed:<6} | {grand_failed + grand_errors:<6} | {total_duration:5.3f}s   | {bold(total_status)}"
    )
    print(bold(cyan("=" * 80)))

    # Print failures if any
    all_failures = []
    for r in results:
        for f in r.failure_details:
            all_failures.append((r.tier_id, f))

    if all_failures:
        print("\n" + bold(red(f"FAILURE DETAILS ({len(all_failures)} failure(s) detected):")))
        for tier_id, trace in all_failures:
            print(bold(red(f"\n--- [{tier_id}] ---")))
            print(trace)
    else:
        print("\n" + bold(green(">> ALL EXECUTED TIERS PASSED WITH 100% SUCCESS RATE! <<")))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified Multi-Tier Test Runner for Solitaire Suite"
    )
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "4", "all"],
        default="all",
        help="Select specific tier to execute (default: all)"
    )
    parser.add_argument(
        "-k", "--pattern",
        type=str,
        default=None,
        help="Filter tests by substring match on name/id"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON summary report"
    )

    args = parser.parse_args()

    tier_specs = [
        ("Tier 1", "Feature Coverage", "tier1_features"),
        ("Tier 2", "Boundary Value Analysis", "tier2_boundaries"),
        ("Tier 3", "Combinations & Interactions", "tier3_combinations"),
        ("Tier 4", "Real-World Scenarios", "tier4_scenarios"),
    ]

    selected_tiers = tier_specs
    if args.tier != "all":
        tier_num = int(args.tier)
        selected_tiers = [tier_specs[tier_num - 1]]

    if not args.json:
        print(bold(cyan(f"\n[RUNNER] Launching Solitaire Suite Test Runner ({args.tier.upper()})...")))
        if args.pattern:
            print(f"[RUNNER] Filter pattern: '{args.pattern}'")

    results: List[TierResult] = []
    start_all = time.time()

    for tier_id, name, dir_name in selected_tiers:
        if not args.json:
            print(f"[RUNNER] Executing {tier_id}: {name}...", end="", flush=True)
        res = run_tier(tier_id, name, dir_name, pattern=args.pattern, verbose=args.verbose)
        results.append(res)
        if not args.json:
            status_tag = green("OK") if res.is_success else red("FAILED")
            print(f" -> {res.total} tests ({res.passed} passed, {res.failed + res.errors} failed) in {res.duration:.3f}s [{status_tag}]")

    total_duration = time.time() - start_all

    all_passed = all(r.is_success for r in results) and sum(r.total for r in results) > 0

    if args.json:
        report_data = {
            "all_passed": all_passed,
            "total_duration_sec": total_duration,
            "grand_total": sum(r.total for r in results),
            "grand_passed": sum(r.passed for r in results),
            "grand_failed": sum(r.failed for r in results),
            "grand_errors": sum(r.errors for r in results),
            "tiers": [
                {
                    "tier_id": r.tier_id,
                    "name": r.name,
                    "total": r.total,
                    "passed": r.passed,
                    "failed": r.failed,
                    "errors": r.errors,
                    "duration_sec": r.duration,
                    "is_success": r.is_success,
                }
                for r in results
            ]
        }
        print(json.dumps(report_data, indent=2))
    else:
        print_summary_table(results, total_duration)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
