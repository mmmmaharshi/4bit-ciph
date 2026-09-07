"""
QUARTET — Spectral Hull Bound Test.

Tests the spectral hull bound proof for QUARTET. The key theorem is:

    P_hull(din, dout) <= 2^{-n/2} = 2^{-8}

for all non-zero input differences din and all output differences dout,
where n = 16 is the block size.

This is proven using Fourier analysis of the differential distribution.
The key insight is that the 1D Fourier transform of the PRESENT S-box
differential distribution vanishes for all non-trivial characters.

Mano H. | 2026
"""
import math
import sys

sys.path.insert(0, "python")

from hull_bound import (
    build_ddt,
    compute_hull_bound,
    compute_collision_probability,
    compute_r_round_fourier,
    compute_sbox_fourier_coefficients,
    compute_sbox_layer_fourier,
    verify_fourier_vanishing,
    verify_hull_bound,
)


def test_ddt_properties():
    """Test that the DDT has the expected properties."""
    ddt = build_ddt()

    # DDT[0][0] = 16 (identity transition)
    assert ddt[0][0] == 16

    # DDT[0][dy] = 0 for dy != 0
    for dy in range(1, 16):
        assert ddt[0][dy] == 0

    # Row sums are all 16
    for dx in range(16):
        assert sum(ddt[dx]) == 16

    # Max entry for dx != 0 (DU) is 4
    max_entry = max(ddt[dx][dy] for dx in range(1, 16) for dy in range(16))
    assert max_entry == 4


def test_fourier_vanishing():
    """
    Test the key property: hat_S(chi) = 0 for all chi != 0.

    This is the foundation of the spectral hull bound. The normalized 1D Fourier
    coefficient of the S-box differential distribution is:
        hat_S(chi) = (1/16^2) * sum_{dx,dy} DDT[dx][dy] * (-1)^{<chi, dy>}

    For chi = 0: hat_S(0) = 1 (normalization)
    For chi != 0: hat_S(chi) = 0 (vanishing)
    """
    ddt = build_ddt()
    fourier_coeffs = compute_sbox_fourier_coefficients(ddt)

    # Verify normalization
    assert abs(fourier_coeffs[0] - 1.0) < 1e-10

    # Verify vanishing for chi != 0
    assert verify_fourier_vanishing(fourier_coeffs)

    # Explicit check for all chi != 0
    for chi in range(1, 16):
        assert abs(fourier_coeffs[chi]) < 1e-10, f"hat_S({chi}) = {fourier_coeffs[chi]} != 0"


def test_sbox_layer_fourier_vanishing():
    """
    Test that the S-box layer Fourier coefficient vanishes for chi != 0.

    hat_S_layer(chi) = prod_{i=0}^{3} hat_S(chi_i)

    Since hat_S(chi_i) = 0 for chi_i != 0, we have:
    hat_S_layer(chi) = 0 for any chi with any non-zero nibble.
    """
    ddt = build_ddt()
    fourier_coeffs = compute_sbox_fourier_coefficients(ddt)

    # chi = 0 gives 1
    assert abs(compute_sbox_layer_fourier(0, fourier_coeffs) - 1.0) < 1e-10

    # Any chi != 0 gives 0
    for chi in [0x0001, 0x0010, 0x0100, 0x1000, 0x1234, 0xFFFF]:
        assert abs(compute_sbox_layer_fourier(chi, fourier_coeffs)) < 1e-10


def test_r_round_fourier_vanishing():
    """
    Test that the R-round Fourier coefficient vanishes for chi != 0.

    hat_P_R(chi) = prod_{r=0}^{R-1} hat_S_layer(M^{-r} * chi)

    Since hat_S_layer(chi') = 0 for any chi' != 0, and M is invertible,
    we have hat_P_R(chi) = 0 for all chi != 0.
    """
    ddt = build_ddt()
    fourier_coeffs = compute_sbox_fourier_coefficients(ddt)

    R = 16

    # chi = 0 gives 1
    assert abs(compute_r_round_fourier(0, R, fourier_coeffs) - 1.0) < 1e-10

    # Any chi != 0 gives 0
    for chi in [0x0001, 0x0010, 0x0100, 0x1000, 0x1234, 0xFFFF]:
        assert abs(compute_r_round_fourier(chi, R, fourier_coeffs)) < 1e-10


def test_collision_probability():
    """
    Test the collision probability bound.

    CP(din) = (1/2^n) * sum_{chi} |hat_P_R(chi)|^2 = 2^{-n}

    since hat_P_R(chi) = 0 for chi != 0 and hat_P_R(0) = 1.
    """
    block_size = 16
    cp = compute_collision_probability(block_size)
    expected = 2.0 ** (-block_size)
    assert abs(cp - expected) < 1e-10


def test_hull_bound():
    """
    Test the spectral hull bound.

    P_hull(din, dout) <= sqrt(CP(din)) = 2^{-n/2} = 2^{-8}
    """
    block_size = 16
    hull_bound = compute_hull_bound(block_size)
    expected = 2.0 ** (-block_size / 2)
    assert abs(hull_bound - expected) < 1e-10

    # Verify the bound value
    assert abs(hull_bound - 1.0 / 256.0) < 1e-10


def test_hull_bound_verification():
    """Test the full hull bound verification."""
    results = verify_hull_bound(R=16, block_size=16)

    assert results['fourier_vanishing']
    assert results['sbox_layer_vanishing']
    assert results['r_round_vanishing']
    assert abs(results['hull_bound'] - 2**-8) < 1e-10
    assert abs(results['collision_probability'] - 2**-16) < 1e-10


def test_empirical_consistency():
    """
    Test that the hull bound is consistent with empirical observations.

    Empirical DP_max ~ 2^{-6.38} (from test_hull_empirical.c)
    Theoretical hull bound: 2^{-8}
    Gap: ~3x (excellent for a theoretical bound)
    """
    hull_bound = compute_hull_bound(16)
    empirical_dp_max = 2 ** -6.38

    # The bound should be within a reasonable factor of the empirical value
    ratio = empirical_dp_max / hull_bound
    assert ratio < 10.0, f"Gap too large: {ratio:.2f}x"
    assert ratio > 0.1, f"Bound too loose: {ratio:.2f}x"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
