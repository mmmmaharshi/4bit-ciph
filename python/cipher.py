"""
QUARTET: A 4-bit Word-Oriented Block Cipher — Python reference.

Single source of truth for the cipher in Python. Test harnesses and the
cryptanalysis suite both import from here.

Design: 16-bit block, 64-bit key, 16-round SPN.
        PRESENT S-box (DP=4/16), FullMix linear layer (branch#4, order 4, M^4=I).
        Round constants per-nibble break invariant subspaces (Leander et al., FSE 2011).

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

# Round constants: C_r[i] = base[i] ^ r, breaks {x,x,x,x} and other
# structural invariant subspaces (Leander et al., FSE 2011).
_RC_BASE: list[int] = [0x0, 0x5, 0xA, 0xF]


def _rc(r: int, i: int) -> int:
    return (_RC_BASE[i] ^ r) & 0xF


def _unpack(v: int) -> list[int]:
    return [(v >> (12 - 4 * i)) & 0xF for i in range(4)]


def _pack(state: list[int]) -> int:
    return (state[0] << 12) | (state[1] << 8) | (state[2] << 4) | state[3]


# FullMix linear layer: [[1,1,1,0],[0,1,1,1],[1,0,1,1],[1,1,0,1]] over GF(2).
# Order 4: M^2 = swap halves, M^4 = I. So M^{-1} = M^3 = [[1,0,1,1],[1,1,0,1],[1,1,1,0],[0,1,1,1]]
def linear_layer(state: list[int]) -> list[int]:
    w0, w1, w2, w3 = state
    return [w0 ^ w1 ^ w2, w1 ^ w2 ^ w3, w2 ^ w3 ^ w0, w3 ^ w0 ^ w1]


def inv_linear_layer(state: list[int]) -> list[int]:
    w0, w1, w2, w3 = state
    return [w0 ^ w2 ^ w3, w0 ^ w1 ^ w3, w0 ^ w1 ^ w2, w1 ^ w2 ^ w3]


INV_LINEAR_LAYER = inv_linear_layer


# Bitsliced S-box (constant-time, no table lookups).
# Operates on 16-bit state with 4 nibbles packed as n0 | n1<<4 | n2<<8 | n3<<12.
# Returns 16-bit state with 4 S-box outputs in same layout.
def sbox_bitsliced(state: int) -> int:
    # Extract bit planes: each holds bit i of all 4 nibbles at positions 0,4,8,12
    x0 = state & 0x1111
    x1 = (state >> 1) & 0x1111
    x2 = (state >> 2) & 0x1111
    x3 = (state >> 3) & 0x1111

    # Shared subexpressions (ANF of PRESENT S-box)
    t1 = x0 & x1          # x0x1
    t2 = x0 & x2          # x0x2
    t3 = x0 & x3          # x0x3
    t4 = x1 & x2          # x1x2
    t5 = x1 & x3          # x1x3
    t6 = x2 & x3          # x2x3
    t7 = t1 & x2          # x0x1x2
    t8 = t1 & x3          # x0x1x3
    t9 = t2 & x3          # x0x2x3

    # Output bits (ANF)
    y0 = x0 ^ x2 ^ t4 ^ x3
    y1 = x1 ^ x3 ^ t5 ^ t6 ^ t7 ^ t8 ^ t9
    y2 = 0x1111 ^ x2 ^ x3 ^ t1 ^ t3 ^ t5 ^ t8 ^ t9
    y3 = 0x1111 ^ x0 ^ x1 ^ x3 ^ t4 ^ t7 ^ t8 ^ t9

    # Reassemble
    return y0 | (y1 << 1) | (y2 << 2) | (y3 << 3)


def inv_sbox_bitsliced(state: int) -> int:
    x0 = state & 0x1111
    x1 = (state >> 1) & 0x1111
    x2 = (state >> 2) & 0x1111
    x3 = (state >> 3) & 0x1111

    # Shared subexpressions (ANF of inverse PRESENT S-box)
    t1 = x0 & x1          # x0x1
    t2 = x0 & x2          # x0x2
    t3 = x1 & x2          # x1x2
    t4 = t1 & x2          # x0x1x2
    t5 = x1 & x3          # x1x3
    t6 = x2 & x3          # x2x3
    t7 = x0 & x3          # x0x3
    t8 = t1 & x3          # x0x1x3
    t9 = t2 & x3          # x0x2x3

    y0 = 0x1111 ^ x0 ^ x2 ^ t5
    y1 = x0 ^ x1 ^ t2 ^ t4 ^ x3 ^ t5 ^ t8 ^ t6 ^ t9
    y2 = 0x1111 ^ t1 ^ t2 ^ t3 ^ t4 ^ x3 ^ t7 ^ t5 ^ t8 ^ t9
    y3 = x0 ^ x1 ^ t1 ^ x2 ^ t4 ^ x3 ^ t9

    return y0 | (y1 << 1) | (y2 << 2) | (y3 << 3)


def _round_bitsliced(state: int, rk: int, r: int) -> int:
    c = 0
    for i in range(4):
        c |= ((_RC_BASE[i] ^ r) & 0xF) << (12 - 4 * i)
    state = sbox_bitsliced(state ^ c)
    state ^= c
    state ^= rk * 0x1111
    return linear_layer_bitsliced(state)


def _inv_round_bitsliced(state: int, rk: int, r: int) -> int:
    c = 0
    for i in range(4):
        c |= ((_RC_BASE[i] ^ r) & 0xF) << (12 - 4 * i)
    state = inv_linear_layer_bitsliced(state)
    state ^= c
    state ^= rk * 0x1111
    state = inv_sbox_bitsliced(state)
    state ^= c
    return state


def linear_layer_bitsliced(state: int) -> int:
    # FullMix is just XORs - already constant-time.
    # Unpack nibbles, apply linear_layer, repack.
    w0 = (state >> 12) & 0xF
    w1 = (state >> 8)  & 0xF
    w2 = (state >> 4)  & 0xF
    w3 = state & 0xF
    out = linear_layer([w0, w1, w2, w3])
    return (out[0] << 12) | (out[1] << 8) | (out[2] << 4) | out[3]


def quartet_encrypt_bitsliced(plaintext: int, key: int, rounds: int = 16) -> int:
    if not (0 <= plaintext < (1 << 16)):
        raise ValueError("plaintext must be 0..65535")
    if not (0 <= key < (1 << 64)):
        raise ValueError("key must be 0..2^64-1")
    state = plaintext
    rk_list = _expand_key(key, rounds)
    for r in range(rounds):
        state = _round_bitsliced(state, rk_list[r], r)
    return state


def quartet_decrypt_bitsliced(ciphertext: int, key: int, rounds: int = 16) -> int:
    if not (0 <= ciphertext < (1 << 16)):
        raise ValueError("ciphertext must be 0..65535")
    if not (0 <= key < (1 << 64)):
        raise ValueError("key must be 0..2^64-1")
    state = ciphertext
    rk_list = _expand_key(key, rounds)
    for r in range(rounds - 1, -1, -1):
        state = _inv_round_bitsliced(state, rk_list[r], r)
    return state


def _round(state: list[int], rk: int, r: int) -> list[int]:
    c0 = _rc(r, 0); c1 = _rc(r, 1); c2 = _rc(r, 2); c3 = _rc(r, 3)
    s0 = SBOX[state[0] ^ c0]; s1 = SBOX[state[1] ^ c1]
    s2 = SBOX[state[2] ^ c2]; s3 = SBOX[state[3] ^ c3]
    return linear_layer([s0 ^ c0 ^ rk, s1 ^ c1 ^ rk,
                         s2 ^ c2 ^ rk, s3 ^ c3 ^ rk])


def _inv_round(state: list[int], rk: int, r: int) -> list[int]:
    c0 = _rc(r, 0); c1 = _rc(r, 1); c2 = _rc(r, 2); c3 = _rc(r, 3)
    im = inv_linear_layer(state)
    o0 = INV_SBOX[im[0] ^ c0 ^ rk]; o1 = INV_SBOX[im[1] ^ c1 ^ rk]
    o2 = INV_SBOX[im[2] ^ c2 ^ rk]; o3 = INV_SBOX[im[3] ^ c3 ^ rk]
    return [o0 ^ c0, o1 ^ c1, o2 ^ c2, o3 ^ c3]


def inv_linear_layer_bitsliced(state: int) -> int:
    w0 = (state >> 12) & 0xF
    w1 = (state >> 8)  & 0xF
    w2 = (state >> 4)  & 0xF
    w3 = state & 0xF
    out = inv_linear_layer([w0, w1, w2, w3])
    return (out[0] << 12) | (out[1] << 8) | (out[2] << 4) | out[3]


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
    rk_list = _expand_key(key, rounds)
    for r in range(rounds):
        state = _round(state, rk_list[r], r)
    return _pack(state)


def quartet_decrypt(ciphertext: int, key: int, rounds: int = 16) -> int:
    if not (0 <= ciphertext < (1 << 16)):
        raise ValueError("ciphertext must be 0..65535")
    if not (0 <= key < (1 << 64)):
        raise ValueError("key must be 0..2^64-1")
    state = _unpack(ciphertext)
    rk_list = _expand_key(key, rounds)
    for r in range(rounds - 1, -1, -1):
        state = _inv_round(state, rk_list[r], r)
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
