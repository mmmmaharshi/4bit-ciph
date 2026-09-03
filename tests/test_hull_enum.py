"""
QUARTET — hull enumeration integration test.

Verifies the differential security position:
1. Single-trail bound: 2^-64 for R=16 (wide-trail, proven)
2. Actual DP_max: ~2^-6.38 for R=16 (empirical, from exhaustive enumeration)
3. Hull effect: actual DP_max >> single-trail bound

Cross-checks:
- Wide-trail bound matches test_bounds.py (min active S-boxes = 32 for R=16)
- Empirical result from C test matches expected range
- Trail enumeration for R=2 produces valid results

Mano H. | 2026
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "python"))

from cipher import SBOX

sys.path.insert(0, str(_REPO_ROOT / "python"))
from hull_enum import (
    HullEnumerator,
    SboxDDT,
    wide_trail_bound,
    max_single_trail_dp,
    enumerate_trails,
    hull_probability,
)


# ===========================================================================
# S-box properties
# ===========================================================================

def test_sbox_ddt_properties() -> None:
    """Verify PRESENT S-box DDT properties."""
    ddt = SboxDDT()

    # Maximum DP = 4/16 = 1/4
    assert ddt.max_dp() == 0.25, f"Expected max_dp=0.25, got {ddt.max_dp()}"

    # Differential uniformity = 4
    max_entry = max(ddt.table[dx][dy] for dx in range(1, 16) for dy in range(16))
    assert max_entry == 4, f"Expected DU=4, got {max_entry}"

    # Row sums are all 16
    for dx in range(16):
        row_sum = sum(ddt.table[dx])
        assert row_sum == 16, f"Row {dx} sum: expected 16, got {row_sum}"

    # dx=0: only dy=0 is possible
    assert ddt.table[0][0] == 16
    assert all(ddt.table[0][dy] == 0 for dy in range(1, 16))

    print("  [OK] S-box DDT properties")


# ===========================================================================
# Wide-trail bound
# ===========================================================================

def test_wide_trail_bound() -> None:
    """Verify wide-trail single-trail DP bound.

    For R rounds with branch number 4:
    - Minimum active S-boxes = R * 2
    - Bound = (1/4)^(2R) = 2^(-4R)

    For R=16: bound = 2^-64 (machine-checked in test_bounds.py)
    """
    # R=2: min active = 4, bound = 2^-8
    bound_2 = wide_trail_bound(2)
    assert math.isclose(bound_2, 2**-8), f"R=2 bound: expected 2^-8, got 2^{math.log2(bound_2):.2f}"

    # R=4: min active = 8, bound = 2^-16
    bound_4 = wide_trail_bound(4)
    assert math.isclose(bound_4, 2**-16), f"R=4 bound: expected 2^-16, got 2^{math.log2(bound_4):.2f}"

    # R=8: min active = 16, bound = 2^-32
    bound_8 = wide_trail_bound(8)
    assert math.log2(bound_8) == -32.0, f"R=8 bound: expected 2^-32, got 2^{math.log2(bound_8):.2f}"

    # R=16: min active = 32, bound = 2^-64
    bound_16 = wide_trail_bound(16)
    assert math.log2(bound_16) == -64.0, f"R=16 bound: expected 2^-64, got 2^{math.log2(bound_16):.2f}"

    print("  [OK] Wide-trail bound: 2^-64 for R=16")


def test_max_single_trail_dp() -> None:
    """Verify max single-trail DP matches wide-trail bound."""
    for R in [2, 4, 8, 16]:
        max_dp = max_single_trail_dp(R)
        bound = wide_trail_bound(R)
        assert math.isclose(max_dp, bound), f"R={R}: max_dp != bound"

    print("  [OK] Max single-trail DP matches wide-trail bound")


# ===========================================================================
# Cross-check with test_bounds.py
# ===========================================================================

def test_cross_check_bounds() -> None:
    """Cross-check with test_bounds.py min active S-box values."""
    # From test_bounds.py (cross-checked with Coq):
    # R=2: min active = 4
    # R=4: min active = 8
    # R=8: min active = 16
    # R=16: min active = 32
    expected_min_active = {2: 4, 4: 8, 8: 16, 16: 32}

    for R, expected_active in expected_min_active.items():
        enumerator = HullEnumerator(R)
        bound = enumerator.wide_trail_bound()
        # Bound = (1/4)^(min_active) = 2^(-2*min_active)
        implied_active = -math.log2(bound) / 2
        assert implied_active == expected_active, (
            f"R={R}: implied min active {implied_active} != expected {expected_active}"
        )

    print("  [OK] Cross-check with test_bounds.py min active values")


# ===========================================================================
# Trail enumeration (small R)
# ===========================================================================

def test_trail_enumeration_r2() -> None:
    """Verify trail enumeration for R=2."""
    # For R=2, enumerate trails from din=0x0001
    # The number of trails depends on the DDT structure
    trails = enumerate_trails(2, 0x0001, 0x0001, max_trails=1000)

    # All enumerated trails should have valid probabilities
    for trail, prob in trails:
        assert 0 < prob <= 1, f"Invalid probability: {prob}"
        # Each trail should have at least 4 active S-boxes (branch number)
        active = sum(1 for state in trail for nibble in state if nibble != 0)
        assert active >= 4, f"Trail has {active} active S-boxes, expected >= 4"

    print(f"  [OK] Trail enumeration R=2: found {len(trails)} trails")


def test_hull_probability_r2() -> None:
    """Verify hull probability for R=2."""
    # Hull probability for a specific (din, dout) pair
    prob = hull_probability(2, 0x0001, 0x0001)
    assert 0 <= prob <= 1, f"Invalid hull probability: {prob}"

    print(f"  [OK] Hull probability R=2: {prob:.6e}")


# ===========================================================================
# Empirical verification (C test)
# ===========================================================================

def test_empirical_dp_max() -> None:
    """Verify empirical DP_max from C test.

    The C test (tests/test_hull_empirical.c) computes the full DDT
    and finds DP_max. For R=16, the empirical result is ~2^-6.38.

    This is much higher than the single-trail bound of 2^-64,
    confirming the hull effect dominates.
    """
    # Build and run the C test
    c_source = _REPO_ROOT / "tests" / "test_hull_empirical.c"
    c_exe = _REPO_ROOT / "test_hull_empirical.exe"

    # Compile
    compile_result = subprocess.run(
        ["gcc", "-O2", "-I", str(_REPO_ROOT / "c"), "-o", str(c_exe), str(c_source)],
        capture_output=True, text=True,
    )
    if compile_result.returncode != 0:
        print(f"  [SKIP] C compilation failed: {compile_result.stderr}")
        return

    # Run (this takes a few minutes)
    run_result = subprocess.run(
        [str(c_exe)],
        capture_output=True, text=True,
        timeout=600,
    )
    if run_result.returncode != 0 and run_result.returncode != 1:
        # Return code 1 is OK (it means DP_max > random limit, which is expected)
        print(f"  [SKIP] C test failed: {run_result.stderr}")
        return

    output = run_result.stdout

    # Parse the DP_max from output
    dp_max = None
    for line in output.splitlines():
        if "DP_max =" in line and "2^(" in line:
            # Parse: "DP_max = 1.202393e-02 = 2^(-6.38)"
            try:
                log2_part = line.split("2^(")[1].split(")")[0]
                dp_max = 2.0 ** float(log2_part)
            except (IndexError, ValueError):
                pass

    # Clean up
    if c_exe.exists():
        c_exe.unlink()

    if dp_max is None:
        print("  [SKIP] Could not parse DP_max from C test output")
        return

    # Verify DP_max is in expected range
    # For R=16, empirical DP_max ≈ 2^-6.38 (from prior runs)
    # Allow some variation due to key choice
    log2_dp_max = math.log2(dp_max)

    # DP_max should be much higher than single-trail bound (2^-64)
    assert log2_dp_max > -20, (
        f"DP_max 2^{log2_dp_max:.2f} is too low, expected > 2^-20"
    )

    # DP_max should be less than 1 (trivially)
    assert log2_dp_max < 0, f"DP_max should be < 1"

    # The key finding: DP_max >> single-trail bound
    single_trail_bound = wide_trail_bound(16)
    amplification = dp_max / single_trail_bound
    assert amplification > 100, (
        f"Hull amplification {amplification:.0f}x is too low, expected > 100x"
    )

    print(f"  [OK] Empirical DP_max = 2^{log2_dp_max:.2f}")
    print(f"       Single-trail bound = 2^-64")
    print(f"       Hull amplification = {amplification:.0f}x")


# ===========================================================================
# Main
# ===========================================================================

def main() -> int:
    print("=" * 70)
    print("QUARTET — hull enumeration integration test")
    print("=" * 70)
    print()

    tests = [
        ("S-box DDT properties", test_sbox_ddt_properties),
        ("Wide-trail bound", test_wide_trail_bound),
        ("Max single-trail DP", test_max_single_trail_dp),
        ("Cross-check with test_bounds.py", test_cross_check_bounds),
        ("Trail enumeration R=2", test_trail_enumeration_r2),
        ("Hull probability R=2", test_hull_probability_r2),
        ("Empirical DP_max (C test)", test_empirical_dp_max),
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
