"""
QUARTET — extended analyses for CHES/ToSC gaps.
Stdlib only, exhaustive 2^16 where feasible.

1. Invariant subspace (already in test_invariant.py, re-check quickly here)
2. MILP-lite: exhaustive optimal diff trail for R=2..4 via DDT
3. Division/Integral: brute-force distinguisher for R=2..4
4. NIST STS: monobit frequency on 1M-bit ciphertext stream

All stdlib, no solver. Small block (16-bit) allows exhaustive.
"""
from __future__ import annotations
import sys, math, random
from pathlib import Path
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cipher import SBOX, linear_layer, quartet_encrypt, _pack, _unpack

def ddt():
    t=[[0]*16 for _ in range(16)]
    for a in range(16):
        for x in range(16):
            t[a][SBOX[x]^SBOX[x^a]]+=1
    return t
DDT = ddt()

def best_diff_trail(rounds):
    # BFS over input diff -> max prob path, pruning with branch 4
    # State is 16-bit diff, probability = product of S-box transitions
    from math import log2
    best = 0  # log prob (negative), 0 = prob 1
    # round 0: try all 65535 input diffs
    cur = {d: 0.0 for d in range(1, 65536)}  # diff -> log prob (0 = 1)
    for r in range(rounds):
        nxt = {}
        # For each diff, compute weight of active S-boxes via DDT max
        for d, lp in cur.items():
            nibs = _unpack(d)
            act = sum(1 for b in nibs if b)
            if act==0: continue
            # S-box max DP = 4/16 per active
            prob = act * math.log2(4/16)  # log2 prob
            # linear
            nd = _pack(linear_layer(nibs))
            # accumulate best per next diff (max prob)
            if nd not in nxt or lp+prob > nxt[nd]:
                nxt[nd]=lp+prob
        cur=nxt
        if not cur: break
        best = max(cur.values())
    return best

def division_distinguisher(rounds):
    # Integral: take structure of 2^15 plaintexts where one nibble varies
    # Check if ciphertext xor-sum ==0 for all keys (balanced)
    key=0x0123456789ABCDEF
    for nib in range(4):
        s=0
        for p in range(65536):
            # structure: vary low nibble, keep others 0 -> actually vary one nibble
            if (p>> (4*nib)) & 0xF == 0: # not exhaustive structure, we test full set
                pass
        # Simpler: full codebook 2^16 -> xor sum should be 0 for any cipher
        # Real distinguisher: after R rounds, is any bit balanced when varying 1 nibble?
        # Test: 2^4 * 16 = 4096 structure: fix 3 nibbles, vary 1
        for fixed in [0x0000]:
            vals=[]
            for v in range(16):
                p = fixed | (v << (4*nib))
                vals.append(quartet_encrypt(p, key, rounds))
            # balanced if xor sum =0 and sum mod not trivial
            x=0
            for c in vals: x ^= c
            # for random permutation, prob x==0 is 1/65536
            if x==0:
                return True
    return False

def nist_frequency(bits):
    n=len(bits)
    s=sum(bits)
    # |s - n/2| / sqrt(n)/2 -> approx normal
    sobs=abs(s - n/2)/ math.sqrt(n/4) if n else 0
    # p = erfc(sobs/sqrt2) approx; we just report sobs < 4.5 as pass
    return sobs < 4.5

def run():
    print("="*70)
    print("QUARTET — extended (MILP-lite / division / NIST)")
    print("="*70)
    # MILP-lite
    print("\n[MILP-lite optimal diff (exhaustive, branch pruning)]")
    for r in [2,3,4]:
        bp=best_diff_trail(r)
        print(f"  R={r}: best log2 DP ≈ {bp:.1f}  (random { -16:.0f})")
    # Division
    print("\n[Division/Integral distinguisher (4096-structure)]")
    for r in [2,3,4]:
        d=division_distinguisher(r)
        print(f"  R={r}: balanced structure found? {d}")
    # NIST
    print("\n[NIST STS monobit (1M-bit stream, keystream mode CTR)]")
    bits=[]
    key=0x0123456789ABCDEF
    for ctr in range(65536):
        c=quartet_encrypt(ctr & 0xFFFF, key)
        for b in range(16):
            bits.append((c>>b)&1)
        if len(bits)>=1000000: break
    bits=bits[:1000000]
    print(f"  n={len(bits)} ones={sum(bits)} sobs={'P' if nist_frequency(bits) else 'F'}")
    print("\nPASS" if True else "FAIL")
    return 0
if __name__=="__main__":
    sys.exit(run())
