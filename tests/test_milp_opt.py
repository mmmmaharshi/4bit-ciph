"""
QUARTET — Optimal trail verification tests.

Verifies that the minimum active S-box count for R rounds is 2R
(by constructing explicit tight trails), and that hull probability
bounds are consistent.

Cross-checks with:
- tests/test_bounds.py (proven min active S-boxes)
- coq/present_wide_trail.v (machine-checked bounds)

Mano H. | 2026
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "python"))

from milp_hull import (
    SboxDDT,
    compute_hull_bounds,
    count_active,
    find_tight_trail,
    verify_optimal,
)


# ===========================================================================
# S-box DDT tests
# ===========================================================================

def test_ddt_properties() -> None:
    """Verify PRESENT S-box DDT properties."""
    ddt = SboxDDT()

    # Differential uniformity = 4
    max_entry = max(ddt.table[dx][dy] for dx in range(1, 16) for dy in range(16))
    assert max_entry == 4, f"Expected DU=4, got {max_entry}"

    # Row sums = 16
    for dx in range(16):
        assert sum(ddt.table[dx]) == 16, f"Row {dx} sum != 16"

    print("  [OK] S-box DDT: DU=4, row sums=16")


def test_transitions() -> None:
    """Verify DDT transitions."""
    ddt = SboxDDT()

    # dx=0: only dy=0
    assert ddt.transitions(0) == [(0, 16)]

    # dx!=0: at least one transition
    for dx in range(1, 16):
        trans = ddt.transitions(dx)
        assert len(trans) > 0, f"dx={dx} has no transitions"
        assert all(count > 0 for _, count in trans)

    print("  [OK] DDT transitions valid")


# ===========================================================================
# Optimal trail tests
# ===========================================================================

def test_min_active_count() -> None:
    """Verify minimum active S-box count = 2R for various R."""
    for R in [2, 4, 6, 8]:
        result = verify_optimal(R)
        expected_min = 2 * R
        assert result['min_active'] == expected_min, \
            f"R={R}: expected min active {expected_min}, got {result['min_active']}"

    print("  [OK] Min active = 2R for R=2,4,6,8")


def test_tight_trails_exist() -> None:
    """Verify that tight trails exist for R=8."""
    result = verify_optimal(8)
    assert result['tight_trails_found'] > 0, "No tight trails found for R=8"

    # Verify each trail has correct active count
    for r in result['results']:
        trail = r['trail']
        total_active = sum(count_active(d) for d in trail[:-1])
        assert total_active == 16, \
            f"Trail has {total_active} active, expected 16"

    print(f"  [OK] Tight trails exist for R=8 ({result['tight_trails_found']} found)")


def test_hull_bounds() -> None:
    """Verify hull probability bounds are consistent."""
    for R in [2, 4, 6, 8]:
        bounds = compute_hull_bounds(R)

        # Lower bound should be > 0
        assert bounds['lower_bound'] > 0, \
            f"R={R}: lower bound <= 0"

        # Upper bound should match wide-trail bound (per-trail max)
        wide_trail = (0.25) ** (2 * R)
        assert math.isclose(bounds['upper_bound'], wide_trail), \
            f"R={R}: upper bound != wide-trail bound"

        # Note: lower bound CAN exceed wide-trail bound because
        # wide-trail is per-trail, while hull sums over all trails

    print("  [OK] Hull bounds consistent")


def test_r8_lower_bound() -> None:
    """Verify R=8 lower bound."""
    bounds = compute_hull_bounds(8)

    # With 28 tight trails each with prob (1/4)^16 = 2^-32
    # Total lower bound = 28 * 2^-32 = 2^-27.19
    assert bounds['log2_lower'] < -20, \
        f"R=8 lower bound 2^{bounds['log2_lower']:.2f} too high"

    print(f"  [OK] R=8 lower bound: 2^{bounds['log2_lower']:.2f}")


# ===========================================================================
# Cross-check with test_bounds.py
# ===========================================================================

def test_cross_check_wide_trail() -> None:
    """Cross-check with test_bounds.py min active values."""
    # From test_bounds.py (proven):
    expected_min_active = {2: 4, 4: 8, 8: 16}

    for R, expected in expected_min_active.items():
        result = verify_optimal(R)
        assert result['min_active'] == expected, \
            f"R={R}: min active {result['min_active']} != expected {expected}"

    print("  [OK] Cross-check with test_bounds.py min active values")


# ===========================================================================
# Main
# ===========================================================================

def main() -> int:
    print("=" * 70)
    print("QUARTET — Optimal Trail Verification Tests")
    print("=" * 70)
    print()

    tests = [
        ("S-box DDT properties", test_ddt_properties),
        ("DDT transitions", test_transitions),
        ("Min active count", test_min_active_count),
        ("Tight trails exist", test_tight_trails_exist),
        ("Hull bounds", test_hull_bounds),
        ("R=8 lower bound", test_r8_lower_bound),
        ("Cross-check wide-trail", test_cross_check_wide_trail),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"[TEST] {name}")
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
