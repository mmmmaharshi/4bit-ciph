"""Diagnostics for complementation property in QUARTET."""
from __future__ import annotations
import sys
sys.path.insert(0, "python")

from cipher import quartet_encrypt, _expand_key, SBOX
import random

# --- Part A: Verify complementation theorem on 200 random key pairs ---
print("PART A: Complementation theorem on 200 random K / (~K) pairs")
print("=" * 70)
fail_count = 0
for trial in range(200):
    k = random.randint(0, (1 << 64) - 1)
    kc = k ^ 0xFFFFFFFFFFFFFFFF  # bitwise complement
    ek_k = _expand_key(k, 17)
    ek_kc = _expand_key(kc, 17)
    for r in range(16):
        if (ek_kc[r] ^ ek_k[r]) != 0xF:
            fail_count += 1
            break
print(f"Result: {200 - fail_count}/200 pass, {fail_count}/200 fail")

# --- Part B: Block-level test on specific keys ---
print("\nPART B: Block-level E_~K(~P) == ~E_K(P)?")
print("=" * 70)

test_keys = [
    0x0,
    0x123456789ABCDEF0,
    random.randint(0, (1 << 64) - 1),
    0xAAAA,
]

for k in test_keys:
    kc = k ^ 0xFFFFFFFFFFFFFFFF
    p = 0x1234
    neg_p = (~p) & 0xFFFF
    c1 = quartet_encrypt(p, k, 16)
    c2 = quartet_encrypt(neg_p, kc, 16)
    neg_c1 = (~c1) & 0xFFFF
    match = (c2 == neg_c1)
    
    # Check round key deltas
    ek_k = _expand_key(k, 17)
    ek_kc = _expand_key(kc, 17)
    rk_uniform = all((ek_kc[r] ^ ek_k[r]) == 0xF for r in range(16))
    
    print(f"  Key={k:016X}")
    print(f"    ~K     ={kc:016X}")
    print(f"    rk delta uniform=0xF? {rk_uniform}")
    print(f"    E_k(P)      = {c1:04X}")
    print(f"    E_~K(~P)    = {c2:04X}")
    print(f"    ~E_k(P)     = {neg_c1:04X}")
    print(f"    E_~K(~P)==~E_k(P)? {match}")
    print()

# --- Part C: Understand WHY random keys fail ---
print("PART C: Why do random keys fail?")
print("=" * 70)
# Show actual deltas for a failing key
k_fail = random.randint(0, (1 << 64) - 1)
kc_fail = k_fail ^ 0xFFFFFFFFFFFFFFFF
ek_fail = _expand_key(k_fail, 17)
ek_kcf = _expand_key(kc_fail, 17)
deltas_fail = [ek_kcf[r] ^ ek_fail[r] for r in range(16)]
print(f"  Sample failing key: {k_fail:016X}")
print(f"  ~K                : {kc_fail:016X}")
print(f"  Delta RK values   : {[hex(d) for d in deltas_fail]}")
print(f"  Non-zero deltas   : {sum(1 for d in deltas_fail if d != 0xF)}")

# Show hex representation details
k_bytes = k_fail.to_bytes(8, byteorder='big')
print(f"  Key bytes (hex)   : {k_fail:016X}")
print(f"  Nibbles           : {' '.join(f'{((k_fail >> (4*i)) & 0xF):X}' for i in range(15, -1, -1))}")
print(f"  ~K nibbles        : {' '.join(f'{((kc_fail >> (4*i)) & 0xF):X}' for i in range(15, -1, -1))}")

# Manual check for r=0
def rk_manual(k_val, r):
    kn = [(k_val >> (4 * j)) & 0xF for j in range(16)]
    rk = kn[r % 16]
    for j in range(16):
        rk ^= SBOX[(kn[j] ^ (r + j + 1)) & 0xF]
    return rk & 0xF

print(f"\n  Manual rk_check for r=0:")
print(f"    _expand_key: {hex(ek_fail[0])}, manual: {hex(rk_manual(k_fail, 0))}")
print(f"    Matches? {_expand_key(k_fail, 17)[0] == rk_manual(k_fail, 0)}")
