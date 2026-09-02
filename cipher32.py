"""
QUARTET-32: 32-bit block adapter over QUARTET-16.

Thin adapter - imports cipher.py, no S-box duplication.
32-bit plaintext = hi16 || lo16, each encrypted with independent 64-bit subkey.
Reuses PRESENT S-box, FullMix optimality (16 matrices wt12), and wide-trail bound.

Block: 32 bits (8 nibbles), Key: 128 bits (2×64), Rounds: 16 (same as base)
"""
from __future__ import annotations
import cipher as q16

def quartet32_encrypt(plaintext: int, key: int, rounds: int = 16) -> int:
    if not (0 <= plaintext < (1 << 32)):
        raise ValueError("plaintext must be 0..2^32-1")
    if not (0 <= key < (1 << 128)):
        raise ValueError("key must be 0..2^128-1")
    hi = (plaintext >> 16) & 0xFFFF
    lo = plaintext & 0xFFFF
    k_hi = (key >> 64) & ((1 << 64) - 1)
    k_lo = key & ((1 << 64) - 1)
    c_hi = q16.quartet_encrypt(hi, k_hi, rounds)
    c_lo = q16.quartet_encrypt(lo, k_lo, rounds)
    return (c_hi << 16) | c_lo

def quartet32_decrypt(ciphertext: int, key: int, rounds: int = 16) -> int:
    if not (0 <= ciphertext < (1 << 32)):
        raise ValueError("ciphertext must be 0..2^32-1")
    if not (0 <= key < (1 << 128)):
        raise ValueError("key must be 0..2^128-1")
    hi = (ciphertext >> 16) & 0xFFFF
    lo = ciphertext & 0xFFFF
    k_hi = (key >> 64) & ((1 << 64) - 1)
    k_lo = key & ((1 << 64) - 1)
    p_hi = q16.quartet_decrypt(hi, k_hi, rounds)
    p_lo = q16.quartet_decrypt(lo, k_lo, rounds)
    return (p_hi << 16) | p_lo

def quartet32_encrypt_bitsliced(plaintext: int, key: int, rounds: int = 16) -> int:
    hi = (plaintext >> 16) & 0xFFFF
    lo = plaintext & 0xFFFF
    k_hi = (key >> 64) & ((1 << 64) - 1)
    k_lo = key & ((1 << 64) - 1)
    c_hi = q16.quartet_encrypt_bitsliced(hi, k_hi, rounds)
    c_lo = q16.quartet_encrypt_bitsliced(lo, k_lo, rounds)
    return (c_hi << 16) | c_lo

def quartet32_self_test() -> bool:
    keys = [0x0123456789ABCDEF0123456789ABCDEF, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 0x0]
    plains = [0x00000000, 0x12345678, 0xFFFFFFFF, 0xDEADBEEF]
    for k in keys:
        for p in plains:
            if quartet32_decrypt(quartet32_encrypt(p, k), k) != p:
                return False
            if quartet32_decrypt(quartet32_encrypt(p, k, 4), k, 4) != p:
                return False
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if quartet32_self_test() else 1)
