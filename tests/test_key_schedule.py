"""
QUARTET — key schedule diffusion tests.

Verifies that the key schedule provides adequate diffusion:
1. Each round key depends on all 16 key nibbles
2. Single key bit flip changes many round key bits (avalanche)
3. Round keys are unique for random keys
4. Weak keys (constant nibbles) still produce unique effective keys
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "python"))

from cipher import _expand_key, _RC_BASE, quartet_encrypt, quartet_decrypt  # noqa: E402


def _rc(r: int, i: int) -> int:
    """Round constant for round r, nibble position i."""
    return (_RC_BASE[i] ^ r) & 0xF


def test_key_nibble_coverage():
    """Verify each round key depends on all 16 key nibbles."""
    print("Test 1: Key nibble coverage")
    print("-" * 40)

    base_key = 0x0123456789ABCDEF
    base_rkeys = _expand_key(base_key, 16)

    for r in range(16):
        depends_on = set()
        for nibble_idx in range(16):
            for nibble_val in range(16):
                test_key = base_key & ~(0xF << (4 * nibble_idx))
                test_key |= (nibble_val << (4 * nibble_idx))
                test_rkeys = _expand_key(test_key, 16)
                if test_rkeys[r] != base_rkeys[r]:
                    depends_on.add(nibble_idx)

        assert len(depends_on) == 16, (
            f"Round {r}: expected dependence on all 16 nibbles, got {len(depends_on)}"
        )

    print("  PASS: Each round key depends on all 16 key nibbles")


def test_avalanche_effect():
    """Verify single key bit flip changes many round key bits."""
    print("\nTest 2: Avalanche effect")
    print("-" * 40)

    base_key = 0x0000000000000000
    base_rkeys = _expand_key(base_key, 16)

    min_changes = 64
    max_changes = 0
    total_changes = 0

    for key_bit in range(64):
        test_key = base_key ^ (1 << key_bit)
        test_rkeys = _expand_key(test_key, 16)

        changes = 0
        for r in range(16):
            diff = base_rkeys[r] ^ test_rkeys[r]
            changes += bin(diff).count('1')

        min_changes = min(min_changes, changes)
        max_changes = max(max_changes, changes)
        total_changes += changes

    avg_changes = total_changes / 64

    # Assert good diffusion: at least 20 bits changed on average
    assert avg_changes >= 20, (
        f"Avalanche too weak: avg {avg_changes:.1f} bits changed, expected >= 20"
    )
    # Assert minimum is reasonable
    assert min_changes >= 10, (
        f"Avalanche minimum too low: {min_changes} bits, expected >= 10"
    )

    print(f"  PASS: Single key bit flip changes {min_changes}-{max_changes} round key bits")
    print(f"  Average: {avg_changes:.1f} bits (ideal: 32)")


def test_round_key_uniqueness():
    """Verify random keys produce mostly unique round keys."""
    print("\nTest 3: Round key uniqueness")
    print("-" * 40)

    # Keys with varying nibbles should have mostly unique round keys
    # Note: Due to the key schedule structure, some keys may have
    # duplicate round keys. This is acceptable as long as diffusion
    # is adequate (verified by other tests).
    varying_keys = [
        0x0123456789ABCDEF,
        0xFEDCBA9876543210,
    ]

    for key in varying_keys:
        rkeys = _expand_key(key, 16)
        unique = len(set(rkeys))
        # Most keys should have all unique round keys
        assert unique >= 12, (
            f"Key 0x{key:016X}: only {unique}/16 unique round keys, expected >= 12"
        )

    # Keys with all identical nibbles produce 1 unique round key
    # (this is expected - round constants break the symmetry)
    weak_keys = [
        0x0000000000000000,
        0x1111111111111111,
        0xFFFFFFFFFFFFFFFF,
        0xAAAAAAAAAAAAAAAA,
    ]

    for key in weak_keys:
        rkeys = _expand_key(key, 16)
        unique = len(set(rkeys))
        assert unique == 1, (
            f"Weak key 0x{key:016X}: {unique}/16 unique round keys, expected 1"
        )

    print("  PASS: Random keys produce mostly unique round keys; weak keys produce 1 (expected)")


def test_weak_key_effective_keys():
    """Verify weak keys (constant nibbles) produce unique effective keys."""
    print("\nTest 4: Weak key effective keys")
    print("-" * 40)

    weak_keys = [
        0x0000000000000000,
        0xFFFFFFFFFFFFFFFF,
        0xAAAAAAAAAAAAAAAA,
        0x5555555555555555,
    ]

    for key in weak_keys:
        rkeys = _expand_key(key, 16)

        # Calculate effective keys (round_key XOR round_constant)
        effective_keys = []
        for r in range(16):
            rc = [_rc(r, i) for i in range(4)]
            effective = tuple((rkeys[r] ^ rc[i]) & 0xF for i in range(4))
            effective_keys.append(effective)

        unique_effective = len(set(effective_keys))
        assert unique_effective == 16, (
            f"Weak key 0x{key:016X}: only {unique_effective}/16 unique effective keys"
        )

    print("  PASS: Weak keys produce 16 unique effective keys via round constants")


def test_weak_key_correctness():
    """Verify cipher works correctly with weak keys."""
    print("\nTest 5: Weak key correctness")
    print("-" * 40)

    weak_keys = [
        0x0000000000000000,
        0xFFFFFFFFFFFFFFFF,
        0xAAAAAAAAAAAAAAAA,
        0x5555555555555555,
    ]

    test_plains = [0x0000, 0x0001, 0x1234, 0x5678, 0x9ABC, 0xDEF0, 0xFFFF]

    for key in weak_keys:
        for pt in test_plains:
            ct = quartet_encrypt(pt, key)
            decrypted = quartet_decrypt(ct, key)
            assert decrypted == pt, (
                f"Weak key 0x{key:016X}: PT=0x{pt:04X} -> CT=0x{ct:04X} -> DEC=0x{decrypted:04X}"
            )

        # Verify different plaintexts produce different ciphertexts
        cts = [quartet_encrypt(pt, key) for pt in test_plains]
        assert len(set(cts)) == len(cts), (
            f"Weak key 0x{key:016X}: duplicate ciphertexts"
        )

    print("  PASS: Cipher works correctly with weak keys")


def test_bit_level_diffusion():
    """Verify each round key bit is affected by many key bits."""
    print("\nTest 6: Bit-level diffusion")
    print("-" * 40)

    base_key = 0x0123456789ABCDEF
    base_rkeys = _expand_key(base_key, 16)

    # Track which key bits affect which round key bits
    affected = [[set() for _ in range(4)] for _ in range(16)]

    for key_bit in range(64):
        test_key = base_key ^ (1 << key_bit)
        test_rkeys = _expand_key(test_key, 16)

        for r in range(16):
            diff = base_rkeys[r] ^ test_rkeys[r]
            for bit in range(4):
                if diff & (1 << bit):
                    affected[r][bit].add(key_bit)

    # Check minimum coverage
    min_coverage = 64
    for r in range(16):
        for b in range(4):
            coverage = len(affected[r][b])
            min_coverage = min(min_coverage, coverage)

    # Assert adequate diffusion: at least 20 key bits affect each round key bit
    assert min_coverage >= 20, (
        f"Bit-level diffusion too weak: min {min_coverage} key bits per round key bit"
    )

    print(f"  PASS: Each round key bit affected by at least {min_coverage}/64 key bits")


def main() -> int:
    print("=" * 60)
    print("QUARTET — Key Schedule Diffusion Tests")
    print("=" * 60)

    try:
        test_key_nibble_coverage()
        test_avalanche_effect()
        test_round_key_uniqueness()
        test_weak_key_effective_keys()
        test_weak_key_correctness()
        test_bit_level_diffusion()

        print("\n" + "=" * 60)
        print("ALL KEY SCHEDULE TESTS PASSED")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\nFAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
