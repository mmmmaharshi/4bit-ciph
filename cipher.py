"""
QUARTET: A 4-bit Word-Oriented Block Cipher — Python reference.

Single source of truth for the cipher in Python. Test harnesses and the
cryptanalysis suite both import from here.

Design: 16-bit block, 64-bit key, 16-round SPN.
        PRESENT S-box (DP=4/16), FullMix linear layer (branch#4).
        FullMix is self-inverse over GF(2) — no inverse table needed.

Mano H. | 2026
"""
from __future__ import annotations

import sys

# PRESENT S-box. Source: Bogdanov et al., CHES 2007.
SBOX: list[int] = [
    0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD,
    0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2,
]
assert sorted(SBOX) == list(range(16)), "S-box must be a bijection"

INV_SBOX: list[int] = [0] * 16
for i, v in enumerate(SBOX):
    INV_SBOX[v] = i
assert all(INV_SBOX[SBOX[i]] == i for i in range(16))


def _unpack(v: int) -> list[int]:
    return [(v >> (12 - 4 * i)) & 0xF for i in range(4)]


def _pack(state: list[int]) -> int:
    return (state[0] << 12) | (state[1] << 8) | (state[2] << 4) | state[3]


# FullMix linear layer: [[1,1,1,0],[0,1,1,1],[1,0,1,1],[1,1,0,1]] over GF(2).
# Self-inverse: FullMix(FullMix(s)) == s for all 16-bit s.
def linear_layer(state: list[int]) -> list[int]:
    w0, w1, w2, w3 = state
    return [w0 ^ w1 ^ w2, w1 ^ w2 ^ w3, w2 ^ w3 ^ w0, w3 ^ w0 ^ w1]


INV_LINEAR_LAYER = linear_layer  # self-inverse


def _round(state: list[int], rk: int) -> list[int]:
    state = [SBOX[w] for w in state]
    state = [w ^ rk for w in state]
    return linear_layer(state)


def _inv_round(state: list[int], rk: int) -> list[int]:
    state = INV_LINEAR_LAYER(state)
    state = [w ^ rk for w in state]
    return [INV_SBOX[w] for w in state]


def _expand_key(key: int, rounds: int) -> list[int]:
    key_nibbles = [(key >> (4 * i)) & 0xF for i in range(16)]
    round_keys = []
    for r in range(rounds):
        rk = key_nibbles[r % 16]
        for j, k in enumerate(key_nibbles):
            rk ^= SBOX[(k ^ (r + j + 1)) & 0xF]
        round_keys.append(rk & 0xF)
    return round_keys


def quartet_encrypt(plaintext: int, key: int, rounds: int = 16) -> int:
    if not (0 <= plaintext < (1 << 16)):
        raise ValueError("plaintext must be 0..65535")
    if not (0 <= key < (1 << 64)):
        raise ValueError("key must be 0..2^64-1")
    state = _unpack(plaintext)
    for rk in _expand_key(key, rounds):
        state = _round(state, rk)
    return _pack(state)


def quartet_decrypt(ciphertext: int, key: int, rounds: int = 16) -> int:
    if not (0 <= ciphertext < (1 << 16)):
        raise ValueError("ciphertext must be 0..65535")
    if not (0 <= key < (1 << 64)):
        raise ValueError("key must be 0..2^64-1")
    state = _unpack(ciphertext)
    for rk in reversed(_expand_key(key, rounds)):
        state = _inv_round(state, rk)
    return _pack(state)


def quartet_self_test() -> bool:
    test_keys = [
        0x0123456789ABCDEF, 0xFFFFFFFFFFFFFFFF,
        0x0000000000000000, 0xFEDCBA9876543210,
        0xAAAAAAAAAAAAAAAA, 0x5555555555555555,
    ]
    test_plains = [0x0000, 0x0001, 0x1234, 0xFFFF, 0xDEAD,
                   0x0123, 0x4567, 0x89AB, 0xCDEF]
    for k in test_keys:
        for p in test_plains:
            c = quartet_encrypt(p, k)
            if quartet_decrypt(c, k) != p:
                return False
    return True


if __name__ == "__main__":
    sys.exit(0 if quartet_self_test() else 1)
