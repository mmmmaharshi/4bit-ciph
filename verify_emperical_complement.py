"""Verify complement propagation through QUARTET rounds."""
from python.cipher import quartet_encrypt, _expand_key

# Empirical test: Does E(~P, ~K) = ~E(P, K) hold?
print("Empirical complementation test on actual cipher:")
print("=" * 70)

import random

test_keys = [0, 0x0123456789ABCDEF, 0xDEADBEEFCAFEBABE]
plains = [0x0000, 0x1234, 0xFFFF]

for key in test_keys:
    kc = key ^ 0xFFFFFFFFFFFFFFFF
    ek_k = _expand_key(key, 17)
    ek_kc = _expand_key(kc, 17)
    uniform = all((ek_kc[r] ^ ek_k[r]) == 0xF for r in range(16))
    
    print(f"\nKey: {key:016X}  ~K: {kc:016X}")
    print(f"  Round-key delta uniform=0xF? {uniform}")
    
    for p in plains:
        np = (~p) & 0xFFFF
        c1 = quartet_encrypt(p, key, 16)
        c2 = quartet_encrypt(np, kc, 16)
        neg_c1 = (~c1) & 0xFFFF
        xor_diff = c2 ^ neg_c1
        
        marker = " ← MATCH!" if xor_diff == 0 else ""
        print(f"    P={p:04X}: E(P)={c1:04X}  E(~P)={c2:04X}  ~E(P)={neg_c1:04X}  XOR-diff={xor_diff:04X}{marker}")

# Also test many random keys
print("\nRandom FKDM test (200 random K/~K pairs):")
successes = 0
total = 200
for _ in range(total):
    k = random.randint(0, (1<<64)-1)
    kc = k ^ 0xFFFFFFFFFFFFFFFF
    c1 = quartet_encrypt(0x1234, k, 16)
    c2 = quartet_encrypt(0xEDCB, kc, 16)
    if c2 == (~c1) & 0xFFFF:
        successes += 1

print(f"  Complementation succeeds: {successes}/{total}")
print(f"  Fraction: {successes/total:.4f}%")
print(f"  Expected for random permutation: ~0%")
