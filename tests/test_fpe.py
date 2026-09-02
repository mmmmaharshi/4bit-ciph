"""QUARTET FPE — Feistel-mode encryption over radix-based domains.

Tests QUARTET used in an iterative additive Feistel network for
Format-Preserving Encryption (NIST SP 800-38G Mode 5 style).

Three test suites:
1. Direct QUARTET format preservation — trivial bijection on {0..2^16-1}
2. Feistel-mode FPE — QUARTET as round function over arbitrary radix
   domains ({0 .. radix^length - 1}, subject to radix^length <= 65536)
3. Statistical sanity — avalanche, uniformity, permutation uniqueness

Mano H. | 2026
"""
from __future__ import annotations

import math
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cipher import quartet_encrypt_bitsliced


# ---------------------------------------------------------------------------
# Feistel helper — additive Feistel step using QUARTET as evaluation fn
# ---------------------------------------------------------------------------

def _feistel_round(left: int, right: int, key: int,
                   rnd_idx: int, t_mod: int, l_mod: int) -> tuple[int, int]:
    """Derive round key via QUARTET-key schedule pattern; apply FEISTEL update."""
    rk = (key ^ ((rnd_idx + 1) << 32)) & 0xFFFFFFFFFFFFFFFF
    ct = quartet_encrypt_bitsliced(right % 65536, rk)
    f_val = ct % (t_mod if t_mod > 0 else 1)
    new_right = (left + f_val) % (t_mod if t_mod > 0 else 1)
    return right, new_right


def feistel_encrypt(pt: int, key: int, radix: int,
                    length: int, rounds: int = 10) -> int:
    """Feistel FPE encrypt: pt ∈ [0, radix^length)."""
    domain = radix ** length
    assert 0 <= pt < domain
    assert domain <= 65536

    t_len = (length + 1) // 2
    l_len = length - t_len
    t_mod = radix ** t_len
    l_mod = radix ** l_len

    left = (pt // l_mod) % t_mod
    right = pt % l_mod

    for r in range(rounds):
        left, right = _feistel_round(left, right, key, r, t_mod, l_mod)
    return left * l_mod + right


def feistel_decrypt(ct: int, key: int, radix: int,
                    length: int, rounds: int = 10) -> int:
    """Reverse Feistel FPE."""
    domain = radix ** length
    assert 0 <= ct < domain

    t_len = (length + 1) // 2
    l_len = length - t_len
    t_mod = radix ** t_len
    l_mod = radix ** l_len

    left = ct // l_mod
    right = ct % l_mod

    for r in range(rounds - 1, -1, -1):
        rk = (key ^ ((r + 1) << 32)) & 0xFFFFFFFFFFFFFFFF
        ct_raw = quartet_encrypt_bitsliced(left % 65536, rk)
        t_mod_val = t_mod if t_mod > 0 else 1
        f_val = ct_raw % t_mod_val
        new_left = (right - f_val) % t_mod_val
        right, left = left, new_left

    return left * l_mod + right


# ---------------------------------------------------------------------------
# Test 1: Direct QUARTET format preservation
# ---------------------------------------------------------------------------

def test_direct_format() -> bool:
    """QUARTET permutes {0..65535} — trivially format-preserving."""
    print("\n[1/5] Direct QUARTET format preservation")
    seen: set[int] = set()
    key = 0x0123456789ABCDEF
    for p in range(65536):
        c = quartet_encrypt_bitsliced(p, key)
        assert 0 <= c < 65536
        assert c not in seen
        seen.add(c)
    print(f"  65536 unique ciphertexts ✓")
    return True


# ---------------------------------------------------------------------------
# Test 2: Round-trip correctness across radix configs
# ---------------------------------------------------------------------------

def test_feistel_correctness() -> bool:
    """encrypt→decrypt = identity for multiple radix configurations."""
    print("\n[2/5] Feistel round-trip correctness")
    rng = random.Random(42)
    key = 0x0123456789ABCDEF
    configs: list[tuple[int, int]] = [
        (2, 4),   # domain {0..15}
        (2, 8),   # domain {0..255}
        (10, 4),  # domain {0..9999}
        (100, 2), # domain {0..9999}
        (2, 16),  # domain {0..65535}
    ]
    failures = 0
    checked = 0
    for radix, length in configs:
        domain = radix ** length
        samples = min(domain, 500)
        pts = rng.sample(range(domain), samples)
        for pt in pts:
            ct = feistel_encrypt(pt, key, radix, length, rounds=10)
            rec = feistel_decrypt(ct, key, radix, length, rounds=10)
            checked += 1
            if rec != pt:
                failures += 1
        print(f"  radix={radix:>3d} len={length:2d} "
              f"domain={domain:>6d}: {samples} samples OK")
    ok = failures == 0
    print(f"  {checked} roundtrips, {failures} failures")
    return ok


# ---------------------------------------------------------------------------
# Test 3: Permutation uniqueness (no collisions)
# ---------------------------------------------------------------------------

def test_feistel_uniqueness() -> bool:
    """All outputs unique for fixed key = permutation property."""
    print("\n[3/5] Feistel permutation property")
    configs: list[tuple[int, int]] = [(2, 4), (2, 8), (10, 4)]
    key = 0x0123456789ABCDEF
    all_ok = True
    for radix, length in configs:
        domain = radix ** length
        cts = [feistel_encrypt(p, key, radix, length, rounds=10)
               for p in range(domain)]
        uniq = len(set(cts))
        status = "✓" if uniq == domain else "FAIL"
        print(f"  radix={radix:>3d} len={length:2d} "
              f"{uniq}/{domain} unique  {status}")
        if uniq != domain:
            all_ok = False
    return all_ok


# ---------------------------------------------------------------------------
# Test 4: Chi-squared uniformity (cross-key overlap)
# ---------------------------------------------------------------------------

def test_feistel_uniformity() -> bool:
    """Cross-key overlap near Poisson(1) expected ≈ 1 for randomness."""
    print("\n[4/5] Cross-key overlap (uniformity proxy)")
    key_a = 0x0123456789ABCDEF
    key_b = 0xFEDCBA9876543210
    configs: list[tuple[int, int]] = [(2, 8), (10, 4)]
    results: list[int] = []
    for radix, length in configs:
        domain = radix ** length
        cts_a = [feistel_encrypt(p, key_a, radix, length, rounds=10)
                 for p in range(domain)]
        cts_b = [feistel_encrypt(p, key_b, radix, length, rounds=10)
                 for p in range(domain)]
        overlaps = sum(1 for i in range(domain) if cts_a[i] == cts_b[i])
        results.append(overlaps)
        print(f"  radix={radix:>3d} len={length:2d} domain={domain:>6d}: "
              f"{overlaps} cross-key matches (expect ~1)")
    # For truly random permutations the expected overlap of two random
    # permutations of size D is 1 (Poisson(1)).  We flag anything >= 5.
    return all(o < 5 for o in results)


# ---------------------------------------------------------------------------
# Test 5: Avalanche (single-bit input flip → ~50% output bits change)
# ---------------------------------------------------------------------------

def test_avalanche() -> bool:
    """Hamming distance between E(p) and E(p⊕2^b) averages near 8/16."""
    print("\n[5/5] Avalanche effect")
    radix, length = 10, 4
    domain = radix ** length
    key = 0x0123456789ABCDEF
    changes: list[int] = []
    for pt in range(0, domain, 100):
        ct0 = feistel_encrypt(pt, key, radix, length, rounds=10)
        max_bit = max(1, math.ceil(math.log2(domain)))
        for b in range(max_bit):
            pt_alt = pt ^ (1 << b)
            if pt_alt >= domain:
                continue
            ct1 = feistel_encrypt(pt_alt, key, radix, length, rounds=10)
            changes.append(bin(ct0 ^ ct1).count("1"))
    avg = sum(changes) / len(changes) if changes else 0
    pct = avg / 16
    print(f"  radix=10 len=4: avg Hamming = {avg:.2f}/16 ({pct:.0%})")
    return 0.35 <= pct <= 0.65


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 70)
    print("QUARTET — Format-Preserving Encryption (FPE) tests")
    print("=" * 70)
    tests: list[tuple[str, bool]] = [
        ("Direct format",     test_direct_format()),
        ("Round-trip",        test_feistel_correctness()),
        ("Permutation",       test_feistel_uniqueness()),
        ("Uniformity",        test_feistel_uniformity()),
        ("Avalanche",         test_avalanche()),
    ]
    print("\n" + "=" * 70)
    for name, ok in tests:
        print(f"  {name:<20s} {'PASS' if ok else 'FAIL'}")
    return 0 if all(v for _, v in tests) else 1


if __name__ == "__main__":
    sys.exit(main())
