"""
Generate Coq file proving Camellia-s1 does NOT satisfy Fourier vanishing.

Strategy: 
  - Only ONE nonzero Fourier coefficient suffices to disprove vanishing
  - Hardcode just ONE DDT row (dx=1, dy=0..255) to minimize Coq computation
  - Compute hat_S(1) using only that row — show it's nonzero
  - If even that's too expensive, try dx=1, chi=2 (smaller numbers)
"""
import sys
sys.path.insert(0, 'python')

from hull_bound_general import CAMELLIA_S1, build_ddt, popcount, chi_sign

def camellia_sbox(x):
    return CAMELLIA_S1[x]

# Build the full DDT
ddt = build_ddt(CAMELLIA_S1)

# Find chi values with largest nonzero coefficients
nonzero_coeffs = []
for chi in range(1, 256):
    coeff = 0
    for dx in range(256):
        for dy in range(256):
            val = ddt[dx][dy]
            if val > 0:
                coeff += val * chi_sign(chi, dy)
    if coeff != 0:
        nonzero_coeffs.append((chi, abs(coeff)))

nonzero_coeffs.sort(key=lambda x: -x[1])

print("Top 10 nonzero Fourier coefficients:")
for chi, mag in nonzero_coeffs[:10]:
    print(f"  chi={chi:04x} ({chi}): |coeff| = {mag}")
    # Also print the DDT row stats for dx=1
    row = [ddt[1][dy] for dy in range(256)]
    nonzero_entries = [(dy, ddt[1][dy]) for dy in range(256) if ddt[1][dy] > 0]
    print(f"    dx=1 row: {len(nonzero_entries)} nonzero entries")
    print(f"    Row nonzero sample (first 5): {nonzero_entries[:5]}")

# Pick the smallest chi with largest magnitude (fastest to prove in Coq)
best_chi = nonzero_coeffs[0][0]
print(f"\nRecommended chi to check in Coq: {best_chi} (0x{best_chi:04x})")
print(f"Coefficient magnitude: {nonzero_coeffs[0][1]}")
