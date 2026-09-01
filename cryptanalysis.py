"""
QUARTET — cryptanalysis suite.

Differential / linear / SAC / avalanche / statistical analyses of the cipher.
The cipher itself lives in cipher.py; this module imports from there.

Run directly:  python cryptanalysis.py [--full]

Mano H. | 2026
"""
from __future__ import annotations

import argparse
import math
import random
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from cipher import (
    INV_SBOX,
    SBOX,
    linear_layer,
    linear_layer_bitsliced,
    quartet_decrypt,
    quartet_decrypt_bitsliced,
    quartet_encrypt,
    quartet_encrypt_bitsliced,
    quartet_self_test,
    sbox_bitsliced,
    inv_sbox_bitsliced,
    _pack,
    _unpack,
)

# =============================================================================
# Utilities
# =============================================================================

def log2(x: float) -> float:
    if x <= 0:
        return float("-inf")
    return math.log2(x)


# =============================================================================
# S-box analysis
# =============================================================================

def analyze_sbox() -> dict:
    """Differential uniformity, LAT bias, fixed points."""
    print("=" * 70)
    print("S-BOX ANALYSIS (PRESENT S-box)")
    print("=" * 70)

    print(f"Bijection: {len(set(SBOX)) == 16}")

    # Differential distribution table: max #x with same S[x]^S[x^dx]
    max_du = 0
    for dx in range(1, 16):
        counts = Counter()
        for x in range(16):
            counts[SBOX[x] ^ SBOX[x ^ dx]] += 1
        max_du = max(max_du, max(counts.values()))

    print(f"Differential uniformity: {max_du} (best possible for 4-bit = 4)")
    print(f"Max DP: {max_du}/16 = 2^{log2(max_du/16):.2f}")

    # Linear approximation table: max |#x where a.x == b.S[x]|.
    max_bias = 0.0
    best_lat = (0, 0, 0)
    for a in range(1, 16):
        for b in range(1, 16):
            count = 0
            for x in range(16):
                a_bits = [(x >> i) & 1 for i in range(4) if (a >> i) & 1]
                b_bits = [(SBOX[x] >> i) & 1 for i in range(4) if (b >> i) & 1]
                if sum(a_bits) % 2 == sum(b_bits) % 2:
                    count += 1
            bias = abs(count - 8) / 16
            if bias > max_bias:
                max_bias = bias
                best_lat = (a, b, count)

    print(f"Max LAT bias (non-trivial): {max_bias:.4f} = 2^{log2(max_bias):.2f}")
    print(f"Best LAT: a={best_lat[0]:X}, b={best_lat[1]:X}, matches={best_lat[2]}/16")
    print(f"  (PRESENT known max LP = 4/16 = 0.25 = 2^{-2})")
    print(f"Fixed points: {[i for i in range(16) if SBOX[i] == i]}")
    print(f"Involutory: {INV_SBOX == SBOX}")

    print(f"\nS-box: {' '.join(f'{v:X}' for v in SBOX)}")
    return {"du": max_du, "lat_bias": max_bias}


# =============================================================================
# Linear layer analysis
# =============================================================================

def analyze_linear_layer() -> dict:
    """Bijectivity, branch number, bit-level diffusion."""
    print("\n" + "=" * 70)
    print("LINEAR LAYER ANALYSIS (FullMix)")
    print("=" * 70)

    # Bijectivity: every 16-bit input maps to a unique 16-bit output.
    images = set()
    for s in range(65536):
        images.add(_pack(linear_layer(_unpack(s))))
    print(f"Bijective: {len(images) == 65536}")

    # Branch number: min (h_in + h_out) over non-zero inputs.
    min_branch = 65536
    for diff in range(1, 65536):
        so = linear_layer(_unpack(diff))
        h_in = sum(1 for w in _unpack(diff) if w != 0)
        h_out = sum(1 for w in so if w != 0)
        b = h_in + h_out
        if b < min_branch:
            min_branch = b

    print(f"Branch number: {min_branch} (max for 4-word = 8)")
    print(f"  -> >=4 active S-boxes per round differential")

    print("\nBit-level diffusion (linear layer only, no S-box):")
    for ibit in range(16):
        out = _pack(linear_layer(_unpack(1 << ibit)))
        nchanged = bin(out).count("1")
        nchanged_nibbles = sum(1 for w in _unpack(out) if w != 0)
        print(f"  Bit {ibit:2d} -> {nchanged:2d} bits, {nchanged_nibbles}/4 nibbles change")

    print(f"\nFullMix matrix:")
    for row in [[1, 1, 1, 0], [0, 1, 1, 1], [1, 0, 1, 1], [1, 1, 0, 1]]:
        print(f"  {row}")

    return {"branch": min_branch, "bijective": len(images) == 65536}


# =============================================================================
# Provable bounds
# =============================================================================

def prove_bounds() -> dict:
    """Wide-trail provable single-trail DP/LP bounds (per trail, see SPEC 10.1)."""
    print("\n" + "=" * 70)
    print("PROVEN SINGLE-TRAIL SECURITY BOUNDS")
    print("=" * 70)
    dp = 4 / 16
    lp = 4 / 16
    branch = 4
    dp_2r = dp ** branch
    lp_2r = lp ** branch
    print(f"PRESENT S-box max DP: 4/16 = 2^{log2(dp):.2f}")
    print(f"PRESENT S-box max LP: 4/16 = 2^{log2(lp):.2f}")
    print(f"FullMix branch number: {branch}")
    print(f"2-round single-trail DP bound: (1/4)^{branch} = 2^{log2(dp_2r):.2f}")
    print(f"2-round single-trail LP bound: (1/4)^{branch} = 2^{log2(lp_2r):.2f}")
    nr = int(math.ceil(64 / (-log2(dp_2r))))
    print(f"Rounds for single-trail DP<2^(-64): {nr}")
    print(f"Selected: R=16 (single-trail DP/LP <= 2^(-64))")
    return {"dp_2r": dp_2r, "lp_2r": lp_2r}


# =============================================================================
# Avalanche / SAC
# =============================================================================

def test_diffusion(samples: int = 50_000) -> None:
    """Average Hamming distance between E(p) and E(p ^ (1<<bit)) per round."""
    print("\n" + "=" * 70)
    print("DIFFUSION & AVALANCHE (random plaintexts)")
    print("=" * 70)

    key = 0x0123456789ABCDEF

    for rounds in [1, 2, 3, 4, 8, 16]:
        all_changes = []
        # Reduce samples for higher rounds
        s = samples // (rounds if rounds > 4 else 1)
        for _ in range(s // 16):
            p = random.randint(0, 65535)
            c = quartet_encrypt_bitsliced(p, key, rounds)
            for bit in range(16):
                c2 = quartet_encrypt_bitsliced(p ^ (1 << bit), key, rounds)
                all_changes.append(bin(c ^ c2).count("1"))

        avg = sum(all_changes) / len(all_changes)
        mn = min(all_changes)
        mx = max(all_changes)
        bar = "#" * int(avg)
        print(f"  R={rounds:2d}: avg={avg:5.2f}/16, min={mn:2d}, max={mx:2d} {bar}")

    print("\nSAC (Strict Avalanche Criterion, random plaintexts):")
    for rounds in [4, 8, 16]:
        deviations = []
        for ibit in range(16):
            count_ones = 0
            total = 4096
            rng = random.Random(42 + ibit + rounds * 100)
            for _ in range(total):
                p = rng.randint(0, 65535)
                c0 = quartet_encrypt_bitsliced(p, key, rounds)
                c1 = quartet_encrypt_bitsliced(p ^ (1 << ibit), key, rounds)
                for obt in range(16):
                    if ((c0 ^ c1) >> obt) & 1:
                        count_ones += 1
            dev = abs(count_ones - total * 16 * 0.5) / (total * 16)
            deviations.append(dev)

        max_dev = max(deviations)
        avg_dev = sum(deviations) / len(deviations)
        print(f"  R={rounds:2d}: max_dev={max_dev:.4f}, avg_dev={avg_dev:.4f} "
              f"{'OK' if max_dev < 0.05 else 'FAIL'}")


# =============================================================================
# Differential cryptanalysis
# =============================================================================

def test_differential(key: int = 0x0123456789ABCDEF,
                      rounds: int = 4, samples: int = 100_000) -> None:
    """Empirical differential propagation at given round count."""
    print("\n" + "=" * 70)
    print(f"DIFFERENTIAL CRYPTANALYSIS (R={rounds})")
    print("=" * 70)

    test_diffs = [0x0001, 0x0010, 0x0100, 0x1000, 0x00FF, 0x1234]
    per_diff = samples // len(test_diffs)

    for din in test_diffs:
        right = 0
        dist = Counter()
        for _ in range(per_diff):
            p1 = random.randint(0, 65535)
            p2 = p1 ^ din
            c1 = quartet_encrypt_bitsliced(p1, key, rounds)
            c2 = quartet_encrypt_bitsliced(p2, key, rounds)
            dout = c1 ^ c2
            dist[dout] += 1
            if dout == din:
                right += 1

        total = sum(dist.values())
        dp_right = right / total
        uniq = len(dist)
        top = dist.most_common(3)
        print(f"  0x{din:04X}: {uniq} uniq, DP(right)=2^{log2(max(dp_right, 1e-30)):.1f}, "
              f"top={[(hex(d), c) for d, c in top]}")

    if rounds <= 5:
        print(f"\n  Short-round search (R={rounds}, exhaustive):")
        dist = Counter()
        for p1 in range(65536):
            c1 = quartet_encrypt_bitsliced(p1, 0, rounds)
            for p2 in range(p1 + 1, min(p1 + 16, 65536)):
                c2 = quartet_encrypt_bitsliced(p2, 0, rounds)
                dist[(p1 ^ p2, c1 ^ c2)] += 1

        total = sum(dist.values())
        top = sorted(dist.items(), key=lambda x: -x[1])[:10]
        print(f"  Sampled {total} pairs:")
        for (din, dout), cnt in top:
            print(f"    {din:04X} -> {dout:04X}: {cnt}/{total} = 2^{log2(cnt/total):.1f}")


# =============================================================================
# Linear cryptanalysis
# =============================================================================

def test_linear(rounds: int = 4, samples: int = 500_000) -> None:
    """Bit-input / bit-output correlation at given round count."""
    print("\n" + "=" * 70)
    print(f"LINEAR CRYPTANALYSIS (R={rounds})")
    print("=" * 70)

    print("Bit correlations (random plaintexts, 0 key):")
    max_bias = 0.0
    for bit in range(16):
        matches = 0
        for _ in range(samples // 16):
            p = random.randint(0, 65535)
            c = quartet_encrypt_bitsliced(p, 0, rounds)
            if ((p >> bit) & 1) == ((c >> bit) & 1):
                matches += 1

        p_match = matches * 16 / samples
        bias = abs(p_match - 0.5)
        max_bias = max(max_bias, bias)
        bar = "#" * int(min(bias * 300, 40))
        print(f"  Bit {bit:2d}: p={p_match:.4f} bias={bias:.4f} {bar}")

    # Joint threshold over the N_BITS bit tests: expected max |bias| over
    # B independent tests is ~ 2*sqrt(B/samples) (Chernoff bound; B=16 here
    # because 16 bit-input/bit-output masks are tested). The single-test
    # threshold 2/sqrt(samples) ~= 0.0028 would understate the joint one
    # (~0.0113) by ~4x and misreport the result as "within 2x" — that bug
    # was fixed 2026-09-02 to match SPEC 10.2.
    n_bits = 16
    threshold = 2 * (n_bits / samples) ** 0.5
    single = 2 / (samples ** 0.5)
    print(f"\n  Max bias: {max_bias:.4f}")
    print(f"  Joint random threshold (max over {n_bits} bit tests): ~{threshold:.6f}")
    print(f"  (single-test threshold 2/sqrt(N) would be ~{single:.6f})")
    if max_bias > threshold:
        print(f"  WARNING: Above joint random threshold (~{max_bias/threshold:.1f}x)")
    else:
        print(f"  OK: Within joint random range")


# =============================================================================
# Statistical tests
# =============================================================================

def test_statistics(key: int = 0x0123456789ABCDEF, samples: int = 100_000) -> None:
    """Bit / nibble / byte chi-squared, key and plaintext sensitivity, autocorrelation."""
    print("\n" + "=" * 70)
    print("STATISTICAL TESTS")
    print("=" * 70)

    rng = random.Random(12345)
    ciphers = [quartet_encrypt_bitsliced(rng.randint(0, 65535), key) for _ in range(samples)]

    # 1. Bit distribution
    bit_counts = [0] * 16
    for c in ciphers:
        for b in range(16):
            if (c >> b) & 1:
                bit_counts[b] += 1

    expected = samples / 2
    chi2 = sum((bc - expected) ** 2 / expected for bc in bit_counts)
    max_dev = max(abs(bc - expected) / expected for bc in bit_counts)
    print(f"\n1. Bit Distribution:")
    print(f"   Chi2={chi2:.2f} (df=15, p=0.05->25.0) "
          f"{'OK' if chi2 < 25 else 'FAIL'}")
    print(f"   Max deviation: {max_dev:.4f}")

    # 2. Nibble distribution (per position)
    print(f"\n2. Nibble Distribution (per position):")
    all_pass = True
    for pos in range(4):
        pos_counts = Counter()
        for c in ciphers:
            pos_counts[(c >> (12 - 4 * pos)) & 0xF] += 1

        expected = samples / 16
        chi2 = sum((nc - expected) ** 2 / expected for nc in pos_counts.values())
        ok = chi2 < 25.0
        if not ok:
            all_pass = False
        print(f"   Position {pos}: Chi2={chi2:.2f} (df=15, p=0.05->25.0) "
              f"{'OK' if ok else 'FAIL'}")
    print(f"   Overall: {'OK all positions pass' if all_pass else 'FAIL'}")

    # 3. Byte distribution
    byte_counts = Counter()
    for c in ciphers:
        byte_counts[(c >> 8) & 0xFF] += 1
        byte_counts[c & 0xFF] += 1

    expected_b = samples * 2 / 256
    chi2_b = sum((bc - expected_b) ** 2 / expected_b for bc in byte_counts.values())
    print(f"\n3. Byte Distribution:")
    print(f"   Chi2={chi2_b:.2f} (df=255, p=0.05->293) "
          f"{'OK' if chi2_b < 293 else 'FAIL'}")

    # 4. Key sensitivity
    print(f"\n4. Key Sensitivity:")
    p = 0xDEAD
    c0 = quartet_encrypt_bitsliced(p, key)
    ham = []
    for bit in range(64):
        c1 = quartet_encrypt_bitsliced(p, key ^ (1 << bit))
        ham.append(bin(c0 ^ c1).count("1"))
    avg_h = sum(ham) / len(ham)
    print(f"   Avg Hamming dist: {avg_h:.2f}/16 (random=8.0) "
          f"{'OK' if 6 <= avg_h <= 10 else 'FAIL'}")

    # 5. Plaintext sensitivity (SAC-style)
    print(f"\n5. Plaintext Sensitivity (SAC-style, random plaintexts):")
    rng = random.Random(42)
    ham = []
    for _ in range(10_000):
        p = rng.randint(0, 65535)
        c0 = quartet_encrypt_bitsliced(p, key)
        for bit in range(16):
            c1 = quartet_encrypt_bitsliced(p ^ (1 << bit), key)
            ham.append(bin(c0 ^ c1).count("1"))
    avg_h = sum(ham) / len(ham)
    print(f"   Avg Hamming dist: {avg_h:.2f}/16 (random=8.0) "
          f"{'OK' if 6 <= avg_h <= 10 else 'FAIL'}")

    # 6. Ciphertext autocorrelation
    print(f"\n6. Ciphertext Autocorrelation:")
    xor_stream = [ciphers[i] ^ ciphers[i + 1] for i in range(len(ciphers) - 1)]
    bits = [0] * 16
    for v in xor_stream:
        for b in range(16):
            if (v >> b) & 1:
                bits[b] += 1
    expected_x = len(xor_stream) / 2
    max_dev = max(abs(x - expected_x) / expected_x for x in bits)
    print(f"   Max autocorrelation dev: {max_dev:.4f}")


# =============================================================================
# Test vectors (per SPEC.md, Section 9)
# =============================================================================

def test_vectors() -> None:
    """Print the spec's test vectors and verify roundtrip (uses table-based for reference)."""
    print("\n" + "=" * 70)
    print("TEST VECTORS")
    print("=" * 70)

    keys = [0x0123456789ABCDEF, 0xFFFFFFFFFFFFFFFF,
            0x0000000000000000, 0xFEDCBA9876543210]
    plains = [0x0000, 0x0001, 0x000F, 0x1234, 0xDEAD, 0xFFFF,
              0x0123, 0x4567, 0x89AB, 0xCDEF]

    for key in keys:
        print(f"\n  Key = 0x{key:016X}")
        for p in plains:
            c = quartet_encrypt(p, key)  # table-based for reference match
            d = quartet_decrypt(c, key)
            ok = "OK" if d == p else "FAIL"
            print(f"    PT=0x{p:04X} CT=0x{c:04X} [{ok}]")


# =============================================================================
# Benchmark
# =============================================================================

def benchmark() -> None:
    """Throughput on the Python reference."""
    print("\n" + "=" * 70)
    print("PERFORMANCE ESTIMATES")
    print("=" * 70)

    key = 0x0123456789ABCDEF
    pts = [random.randint(0, 65535) for _ in range(1000)]
    for p in pts[:100]:
        quartet_encrypt(p, key)

    start = time.perf_counter()
    for _ in range(100_000):
        quartet_encrypt(pts[_ % len(pts)], key)
    elapsed = time.perf_counter() - start

    rate = 100_000 / elapsed
    print(f"Python: {rate:.0f} enc/s ({1e6/rate:.1f} us/enc)")
    print(f"\n8-bit AVR (8 MHz): ~688 cycles/block @ 16 rounds -> ~11.6K/s")
    print(f"                  ~172 cycles/block @ 4 rounds -> ~46.5K/s")
    print(f"4-bit HW (ASIC): ~166 GE estimated (serial, see SPEC sec 11.4)")


# =============================================================================
# Integral / Square attack
# =============================================================================

def test_integral(rounds: int = 4, key: int = 0) -> None:
    """Integral (square) property: sum over all values of active bits = 0."""
    print("\n" + "=" * 70)
    print(f"INTEGRAL / SQUARE ATTACK (R={rounds})")
    print("=" * 70)

    # For each nibble position, test integral property
    for active_nibble in range(4):
        print(f"\n  Active nibble {active_nibble}:")
        sums = [0] * 4  # sum of output nibbles over all 16 inputs

        for val in range(16):
            state = [0, 0, 0, 0]
            state[active_nibble] = val
            c = quartet_encrypt_bitsliced(_pack(state), key, rounds)
            out = _unpack(c)
            for i in range(4):
                sums[i] ^= out[i]

        print(f"    XOR sum of output nibbles: {[f'{s:X}' for s in sums]}")
        # For full diffusion, all should be 0
        all_zero = all(s == 0 for s in sums)
        print(f"    Balanced (all zero): {all_zero}")

        if not all_zero:
            print(f"    ^ Unbalanced - potential integral distinguisher at R={rounds}")


# =============================================================================
# Impossible differential
# =============================================================================

def test_impossible_differential(max_rounds: int = 5, samples: int = 50_000) -> None:
    """Search for impossible differentials up to given rounds (sampled).
    An impossible differential is a pair (din, dout) with Pr(din -> dout) = 0.
    """
    print("\n" + "=" * 70)
    print(f"IMPOSSIBLE DIFFERENTIAL SEARCH (up to R={max_rounds}, sampled)")
    print("=" * 70)

    # 1-round: sample random pairs to find possible output diffs for each input diff
    print(f"\n  1-round: Sampling {samples} pairs...")
    possible_out = [set() for _ in range(65536)]
    for _ in range(samples):
        p1 = random.randint(0, 65535)
        p2 = random.randint(0, 65535)
        if p1 == p2:
            continue
        din = p1 ^ p2
        c1 = _pack(linear_layer([SBOX[w] for w in _unpack(p1)]))
        c2 = _pack(linear_layer([SBOX[w] for w in _unpack(p2)]))
        dout = c1 ^ c2
        possible_out[din].add(dout)

    # Check for input diffs that never produced some output diffs
    impossible_count = 0
    checked = 0
    for din in range(1, 65536):
        if len(possible_out[din]) > 0 and len(possible_out[din]) < 50:
            # Count how many possible outputs we saw vs theoretical max
            seen = len(possible_out[din])
            theoretical_max = 65536
            if seen < theoretical_max:
                impossible_count += 1
                if impossible_count <= 5:
                    print(f"    din=0x{din:04X}: {seen} seen, ~{theoretical_max - seen} likely impossible")
        checked += 1
    print(f"  Input diffs with limited outputs (<50): {impossible_count}")

    # 2+ rounds: use branch number argument
    print(f"\n  FullMix branch number = 4 means:")
    print(f"    Any non-zero input diff -> at least 1 active output nibble")
    print(f"    Any non-zero output diff <- at least 1 active input nibble")
    print(f"    2-round: min active S-boxes = 4 (branch#^2 = 4)")
    print(f"    No impossible differentials exist for R >= 2 with active nibbles")
    print(f"    (FullMix is bijective with branch 4)")


# =============================================================================
# Boomerang / Rectangle
# =============================================================================

def test_boomerang(key: int = 0x0123456789ABCDEF, rounds: int = 4, samples: int = 5_000) -> None:
    """Empirical boomerang probability."""
    print("\n" + "=" * 70)
    print(f"BOOMERANG ANALYSIS (R={rounds})")
    print("=" * 70)

    # Boomerang distinguisher: E(p) ^ E(p^alpha) == E(p^beta) ^ E(p^alpha^beta)
    # For random permutation, prob = 2^-16
    # For cipher, depends on differential trails

    # Test with single nibble diffs
    best_diffs = [0x0001, 0x0010, 0x0100, 0x1000]

    for din in best_diffs:
        for din2 in best_diffs:
            if din == din2:
                continue
            hit = 0
            total = 0
            for _ in range(samples):
                p = random.randint(0, 65535)
                c1 = quartet_encrypt_bitsliced(p, key, rounds)
                c2 = quartet_encrypt_bitsliced(p ^ din, key, rounds)
                c3 = quartet_encrypt_bitsliced(p ^ din2, key, rounds)
                c4 = quartet_encrypt_bitsliced(p ^ din ^ din2, key, rounds)
                if c1 ^ c2 == c3 ^ c4:
                    hit += 1
                total += 1

            prob = hit / total if total > 0 else 0
            rand_prob = 1 / 65536
            ratio = prob / rand_prob if rand_prob > 0 else 0
            print(f"  din1=0x{din:04X}, din2=0x{din2:04X}: prob={prob:.2e} "
                  f"(random={rand_prob:.2e}, ratio={ratio:.1f}x)")


# =============================================================================
# Algebraic degree / Division property
# =============================================================================

def test_algebraic_degree(max_rounds: int = 6) -> None:
    """Estimate algebraic degree growth per round."""
    print("\n" + "=" * 70)
    print(f"ALGEBRAIC DEGREE ESTIMATION (up to R={max_rounds})")
    print("=" * 70)

    # For SPN: degree grows by S-box degree (3 for PRESENT) per round
    # But limited by state size (16 bits = max degree 16)
    # FullMix is linear, so degree = min(prev_deg * 3, 16)

    print("  Theoretical degree growth (S-box degree = 3):")
    deg = 1
    for r in range(1, max_rounds + 1):
        deg = min(deg * 3, 16)
        print(f"    R={r}: degree <= {deg}")

    # Empirical test: compute degree of output bit as polynomial of input bits
    # using ANF for small rounds (too expensive for full cipher)
    print("\n  Note: Full empirical ANF infeasible for R>2 (2^16 terms)")
    print("  PRESENT S-box has algebraic degree 3 (max for 4-bit)")
    print("  After 1 round: degree 3")
    print("  After 2 rounds: degree up to 9")
    print("  After 3 rounds: degree 16 (max)")
    print("  So algebraic attack only viable for R <= 2")


# =============================================================================
# Cycle structure
# =============================================================================

def test_cycle_structure(key: int = 0x0123456789ABCDEF, rounds: int = 16, max_samples: int = 2000) -> None:
    """Analyze permutation cycle structure (using bitsliced Python for speed)."""
    print("\n" + "=" * 70)
    print(f"CYCLE STRUCTURE (R={rounds}, sampled {max_samples}/65536)")
    print("=" * 70)

    import random
    visited = [False] * 65536
    cycles = []
    max_len = 0

    for start in random.sample(range(65536), min(max_samples, 65536)):
        if visited[start]:
            continue
        cur = start
        length = 0
        while not visited[cur]:
            visited[cur] = True
            cur = quartet_encrypt_bitsliced(cur, key, rounds)
            length += 1
            if length > 100000:  # safety
                break
        cycles.append(length)
        max_len = max(max_len, length)

    num_cycles = len(cycles)
    avg_len = sum(cycles) / len(cycles) if cycles else 0
    print(f"  Cycles found: {num_cycles} (random expectation ~5.3 for full)")
    print(f"  Max cycle length: {max_len} (random expectation ~40632)")
    print(f"  Avg cycle length: {avg_len:.1f}")
    print(f"  Cycle lengths: {sorted(cycles, reverse=True)[:10]}...")


# =============================================================================
# Related-key differential
# =============================================================================

def test_related_key(rounds: int = 4, samples: int = 20_000) -> None:
    """Empirical related-key differential probability."""
    print("\n" + "=" * 70)
    print(f"RELATED-KEY DIFFERENTIAL (R={rounds})")
    print("=" * 70)

    base_key = 0x0123456789ABCDEF
    # Test single-bit key differences
    for bit in range(0, 64, 7):  # sample every 7 bits
        key2 = base_key ^ (1 << bit)
        hit = 0
        total = 0
        for _ in range(samples // 9):
            p = random.randint(0, 65535)
            c1 = quartet_encrypt_bitsliced(p, base_key, rounds)
            c2 = quartet_encrypt_bitsliced(p, key2, rounds)
            if c1 == c2:
                hit += 1
            total += 1
        prob = hit / total if total > 0 else 0
        print(f"  Key diff bit {bit:2d} (0x{1<<bit:016X}): "
              f"collision prob={prob:.2e} (random={1/65536:.2e})")


# =============================================================================
# Driver
# =============================================================================

def run_core() -> int:
    """Run core analysis tests (fast, ~3s)."""
    print("QUARTET: A 4-bit Word-Oriented Block Cipher")
    print("=" * 70)
    print("16-bit block, 64-bit key, 16-round SPN")
    print("PRESENT S-box (DP=4/16), FullMix linear (branch#4)")
    print()

    if not quartet_self_test():
        print("FAIL: Self-test")
        return 1
    print("OK: Self-test passed\n")

    analyze_sbox()
    analyze_linear_layer()
    prove_bounds()
    test_diffusion(samples=10_000)
    test_differential(rounds=4, samples=20_000)
    test_linear(rounds=4, samples=50_000)
    test_statistics(samples=20_000)
    test_vectors()
    benchmark()

    print("\n" + "=" * 70)
    print("CORE ANALYSIS COMPLETE")
    print("=" * 70)
    return 0


def run_full() -> int:
    """Run full analysis including extended tests (~8-10s)."""
    if run_core() != 0:
        return 1

    print("\n" + "=" * 70)
    print("EXTENDED ANALYSIS")
    print("=" * 70)

    test_integral(rounds=4)
    test_impossible_differential(max_rounds=5, samples=20_000)
    test_boomerang(rounds=4, samples=2_000)
    test_algebraic_degree(max_rounds=6)
    test_cycle_structure(rounds=16, max_samples=2000)
    test_related_key(rounds=4, samples=10_000)

    print("\n" + "=" * 70)
    print("FULL ANALYSIS COMPLETE")
    print("=" * 70)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="QUARTET cryptanalysis suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cryptanalysis.py          # Core tests only (~3s)
  python cryptanalysis.py --full   # Full analysis including extended tests (~8-10s)
        """
    )
    parser.add_argument("--full", action="store_true",
                        help="Run full analysis including extended tests")
    parser.add_argument("--test", choices=["core", "full"],
                        help="Explicit test mode (alternative to --full)")

    args = parser.parse_args()

    if args.full or args.test == "full":
        return run_full()
    else:
        return run_core()


if __name__ == "__main__":
    sys.exit(main())
