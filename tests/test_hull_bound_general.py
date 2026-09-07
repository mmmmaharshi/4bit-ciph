"""
Tests for the general spectral hull bound checker.

Tests that the Fourier vanishing property holds for multiple S-boxes
from the literature.

Mano H. | 2026
"""
import math
import sys

sys.path.insert(0, "python")

from hull_bound_general import (
    AES_SBOX,
    CAMELLIA_S1,
    GIFT_SBOX,
    HIGHT_SBOX,
    LBLOCK_S0,
    LED_SBOX,
    PICCOLO_SBOX,
    PRESENT_SBOX,
    PRINCE_SBOX,
    RECTANGLE_SBOX,
    SERPENT_S0,
    SKINNY_SBOX,
    TWINE_SBOX,
    analyze_sbox,
    build_ddt,
    check_fourier_vanishing,
    compute_fourier_coefficients,
)


def test_ddt_properties():
    """Test DDT construction for various S-boxes."""
    for name, sbox in [("PRESENT", PRESENT_SBOX), ("GIFT", GIFT_SBOX), ("AES", AES_SBOX)]:
        n = len(sbox)
        ddt = build_ddt(sbox)

        # DDT dimensions
        assert len(ddt) == n, f"{name}: DDT should have {n} rows"
        assert all(len(row) == n for row in ddt), f"{name}: DDT should have {n} columns"

        # Row sums should equal n
        for dx in range(n):
            assert sum(ddt[dx]) == n, f"{name}: Row {dx} should sum to {n}"

        # DDT[0][0] = n (identity)
        assert ddt[0][0] == n, f"{name}: DDT[0][0] should be {n}"

        # DDT[0][dy] = 0 for dy != 0
        for dy in range(1, n):
            assert ddt[0][dy] == 0, f"{name}: DDT[0][{dy}] should be 0"


def test_fourier_vanishing_present():
    """Test Fourier vanishing for PRESENT S-box."""
    result = check_fourier_vanishing(PRESENT_SBOX)

    assert result['applies'], "PRESENT S-box should have vanishing Fourier coefficients"
    assert abs(result['normalization'] - 1.0) < 1e-10, "Normalization should be 1"
    assert result['max_nontrivial'] < 1e-10, "Max non-trivial coefficient should be 0"


def test_fourier_vanishing_gift():
    """Test Fourier vanishing for GIFT-64 S-box."""
    result = check_fourier_vanishing(GIFT_SBOX)

    assert result['applies'], "GIFT S-box should have vanishing Fourier coefficients"
    assert abs(result['normalization'] - 1.0) < 1e-10, "Normalization should be 1"
    assert result['max_nontrivial'] < 1e-10, "Max non-trivial coefficient should be 0"


def test_fourier_vanishing_prince():
    """Test Fourier vanishing for PRINCE S-box."""
    result = check_fourier_vanishing(PRINCE_SBOX)

    assert result['applies'], "PRINCE S-box should have vanishing Fourier coefficients"
    assert abs(result['normalization'] - 1.0) < 1e-10, "Normalization should be 1"
    assert result['max_nontrivial'] < 1e-10, "Max non-trivial coefficient should be 0"


def test_fourier_vanishing_piccolo():
    """Test Fourier vanishing for Piccolo S-box."""
    result = check_fourier_vanishing(PICCOLO_SBOX)

    assert result['applies'], "Piccolo S-box should have vanishing Fourier coefficients"
    assert abs(result['normalization'] - 1.0) < 1e-10, "Normalization should be 1"
    assert result['max_nontrivial'] < 1e-10, "Max non-trivial coefficient should be 0"


def test_fourier_vanishing_twine():
    """Test Fourier vanishing for TWINE S-box."""
    result = check_fourier_vanishing(TWINE_SBOX)

    assert result['applies'], "TWINE S-box should have vanishing Fourier coefficients"
    assert abs(result['normalization'] - 1.0) < 1e-10, "Normalization should be 1"
    assert result['max_nontrivial'] < 1e-10, "Max non-trivial coefficient should be 0"


def test_fourier_vanishing_aes():
    """Test Fourier vanishing for AES S-box."""
    result = check_fourier_vanishing(AES_SBOX)

    assert result['applies'], "AES S-box should have vanishing Fourier coefficients"
    assert abs(result['normalization'] - 1.0) < 1e-10, "Normalization should be 1"
    assert result['max_nontrivial'] < 1e-10, "Max non-trivial coefficient should be 0"


def test_fourier_vanishing_led():
    """Test Fourier vanishing for LED S-box."""
    result = check_fourier_vanishing(LED_SBOX)
    assert result['applies'], "LED S-box should have vanishing Fourier coefficients"


def test_fourier_vanishing_skinny():
    """Test Fourier vanishing for SKINNY-64 S-box."""
    result = check_fourier_vanishing(SKINNY_SBOX)
    assert result['applies'], "SKINNY S-box should have vanishing Fourier coefficients"


def test_fourier_vanishing_rectangle():
    """Test Fourier vanishing for Rectangle S-box."""
    result = check_fourier_vanishing(RECTANGLE_SBOX)
    assert result['applies'], "Rectangle S-box should have vanishing Fourier coefficients"


def test_fourier_vanishing_lblock():
    """Test Fourier vanishing for LBlock-S0 S-box."""
    result = check_fourier_vanishing(LBLOCK_S0)
    assert result['applies'], "LBlock S-box should have vanishing Fourier coefficients"


def test_fourier_vanishing_serpent():
    """Test Fourier vanishing for Serpent-S0 S-box."""
    result = check_fourier_vanishing(SERPENT_S0)
    assert result['applies'], "Serpent S-box should have vanishing Fourier coefficients"


def test_fourier_vanishing_hight():
    """Test Fourier vanishing for HIGHT S-box."""
    result = check_fourier_vanishing(HIGHT_SBOX)
    assert result['applies'], "HIGHT S-box should have vanishing Fourier coefficients"


def test_camellia_fails_vanishing():
    """Test that Camellia S-box does NOT have Fourier vanishing.

    This is important: it shows the hull bound is non-trivial and doesn't
    apply to all S-boxes.
    """
    result = check_fourier_vanishing(CAMELLIA_S1)
    assert not result['applies'], "Camellia S-box should NOT have vanishing Fourier coefficients"
    assert result['max_nontrivial'] > 1e-10, "Camellia should have non-zero coefficients"


def test_all_sboxes_applicable():
    """Test that all tested S-boxes (except Camellia) have the hull bound property."""
    sboxes = [
        ("PRESENT", PRESENT_SBOX),
        ("GIFT-64", GIFT_SBOX),
        ("PRINCE", PRINCE_SBOX),
        ("Piccolo", PICCOLO_SBOX),
        ("TWINE", TWINE_SBOX),
        ("LED", LED_SBOX),
        ("SKINNY-64", SKINNY_SBOX),
        ("Rectangle", RECTANGLE_SBOX),
        ("LBlock-S0", LBLOCK_S0),
        ("Serpent-S0", SERPENT_S0),
        ("HIGHT", HIGHT_SBOX),
        ("AES", AES_SBOX),
    ]

    for name, sbox in sboxes:
        result = check_fourier_vanishing(sbox)
        assert result['applies'], f"{name} S-box should have vanishing Fourier coefficients"


def test_hull_bound_values():
    """Test that hull bound values are correct."""
    # For 4-bit S-boxes: bound = 2^{-4/2} = 2^{-2} per S-box layer
    for name, sbox in [("PRESENT", PRESENT_SBOX), ("GIFT", GIFT_SBOX)]:
        result = analyze_sbox(sbox, name)
        n = len(sbox)
        expected_bound = 2.0 ** (-n / 2)
        assert result['bound'] == expected_bound, f"{name}: Hull bound should be 2^{-n/2}"
        assert result['log2_bound'] == -n / 2, f"{name}: log2 bound should be {-n/2}"

    # For 8-bit S-box (AES): bound = 2^{-8/2} = 2^{-4} per S-box layer
    result = analyze_sbox(AES_SBOX, "AES")
    n = len(AES_SBOX)
    expected_bound = 2.0 ** (-n / 2)
    assert result['bound'] == expected_bound, f"AES: Hull bound should be 2^{-n/2}"
    assert result['log2_bound'] == -n / 2, f"AES: log2 bound should be {-n/2}"


def test_fourier_coefficients_structure():
    """Test the structure of Fourier coefficients."""
    for sbox in [PRESENT_SBOX, GIFT_SBOX]:
        coeffs = compute_fourier_coefficients(sbox)
        n = len(sbox)

        # Should have n coefficients
        assert len(coeffs) == n

        # chi=0 should give 1
        assert abs(coeffs[0] - 1.0) < 1e-10

        # All other coefficients should be 0
        for chi in range(1, n):
            assert abs(coeffs[chi]) < 1e-10, f"chi={chi}: coefficient should be 0"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
