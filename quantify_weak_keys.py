"""Quantify which keys satisfy the complementation condition."""
from __future__ import annotations
import sys
sys.path.insert(0, "python")

from cipher import _expand_key, SBOX
import random

def has_uniform_delta(k):
    """Check if ALL round keys have delta=0xF relative to ~K."""
    kc = k ^ 0xFFFFFFFFFFFFFFFF
    ek_k = _expand_key(k, 17)
    ek_kc = _expand_key(kc, 17)
    return all((ek_kc[r] ^ ek_k[r]) == 0xF for r in range(16))

# Test structured keys
print("Structured key analysis:")
print("=" * 70)

# Keys where all 16 nibbles are {0,...,15} (permutation keys)
perm_keys = [
    0x0123456789ABCDEF,
    0xFEDCBA9876543210,
    0x0F1E2D3C4B5A6978,
    0x123456789ABCDEF0,
]

# Keys with repeated nibbles
repeated_keys = [
    0x0,
    0xFFFFFFFFFFFFFFFF,
    0x1111111111111111,
    0xAAAAAAAAAAAAAAAA,
    0x5555555555555555,
    0x1212121212121212,
    0xABCDEFABCDEFABCD,
]

for k in perm_keys:
    result = has_uniform_delta(k)
    print(f"  Key={k:016X}: uniform-delta? {result}")

print()
for k in repeated_keys[:5]:
    result = has_uniform_delta(k)
    print(f"  Key={k:016X}: uniform-delta? {result}")

# Random sampling
print("\nRandom key sampling (uniform-delta?):")
hits = []
for trial in range(10000):
    k = random.randint(0, (1<<64)-1)
    if has_uniform_delta(k):
        hits.append(k)

print(f"  Hits out of 10000 random keys: {len(hits)}")
if hits:
    for h in hits[:5]:
        print(f"    Hit: {h:016X}")

# Characterize hit pattern
if hits:
    print("\nAnalyzing hit structure:")
    for h in hits[:10]:
        nibbles = [(h >> (4*j)) & 0xF for j in range(16)]
        unique = len(set(nibbles))
        print(f"  {h:016X}: nibbles={nibbles}, unique={unique}")

# What about KEY=~0 (all F)?
print("\nSpecial case: KC=~0 (complement of ZERO)")
kc_zero = 0xFFFFFFFFFFFFFFFF
print(f"  Key={kc_zero:016X}: uniform-delta? {has_uniform_delta(kc_zero)}")
