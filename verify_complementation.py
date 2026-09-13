"""Verify complementation symmetry empirically."""
from __future__ import annotations
import sys, random
sys.path.insert(0, "python")

from cipher import quartet_encrypt, _expand_key

print("Complementation symmetry: E_{~K}(~P) == ~E_K(P)?")
print("=" * 70)

for key in [0, 0x123456789ABCDEF0, 0xDEADBEEFCAFEBABE]:
    kc = key ^ 0xFFFFFFFFFFFFFFFF
    ek_k = _expand_key(key, 17)
    ek_kc = _expand_key(kc, 17)
    rk_uniform = all((ek_kc[r] ^ ek_k[r]) == 0xF for r in range(16))
    
    print(f"\nKey={key:016X}  ~K={kc:016X}")
    print(f"  rk delta uniform=0xF? {rk_uniform}")
    print(f"  First 4 round keys K:   {[hex(v) for v in ek_k[:4]]}")
    print(f"  First 4 round keys ~K:  {[hex(v) for v in ek_kc[:4]]}")
    print(f"  Deltas:                 {[hex(ek_kc[r]^ek_k[r]) for r in range(4)]}")
    
    if rk_uniform:
        for p in [0x0000, 0x1234, 0xABCD, 0xFFFF]:
            neg_p = (~p) & 0xFFFF
            c_orig = quartet_encrypt(p, key, 16)
            c_comp = quartet_encrypt(neg_p, kc, 16)
            expected = (~c_orig) & 0xFFFF
            xor_diff = c_comp ^ expected
            print(f"    P={p:04X}: E(P)={c_orig:04X}  E(~P)={c_comp:04X}  ~E(P)={expected:04X}  XorDiff={xor_diff:04X}")
    else:
        print(f"  (Block-level not applicable — rk delta not uniform)")

# Also test: what happens per-round for KEY=0?
print("\n\nPer-round trace for KEY=0 (complement-holding key):")
print("=" * 70)

# Manual step-by-step encryption
from cipher import _unpack, _pack, _rc, linear_layer, SBOX

def compute_round_keys(k, n=16):
    return [_expand_key(k, n+1)[r] for r in range(n)]

def step_encrypt(state, rk, r):
    c = [_rc(r,i) for i in range(4)]
    new = []
    for i in range(4):
        s = SBOX[state[i] ^ c[i] ^ rk]
        new.append(s ^ c[i] ^ rk)
    return linear_layer(new)

for k_val, label in [(0, "KEY=0"), (0x123456789ABCDEF0, "KEY=hexdigits")]:
    print(f"\n{label}:")
    k_rks = compute_round_keys(k_val)
    kc = k_val ^ 0xFFFFFFFFFFFFFFFF
    kc_rks = compute_round_keys(kc)
    
    p = 0x0000
    neg_p = 0xFFFF
    
    state_orig = list(_unpack(p))
    state_comp = list(_unpack(neg_p))
    
    for r in range(17):
        if r < 16:
            rk_o = k_rks[r]
            rk_c = kc_rks[r]
            delta = rk_o ^ rk_c
            state_orig = step_encrypt(state_orig, rk_o, r)
            state_comp = step_encrypt(state_comp, rk_c, r)
        
        xor_diff = [(a^b) for a,b in zip(state_orig, state_comp)]
        diff_hex = sum(d << (4*i) for i,d in enumerate(reversed(xor_diff)))
        neg_orig = [(~s)&0xF for s in state_orig]
        match_with_neg = [a==b for a,b in zip(state_comp, neg_orig)]
        comp_ok = all(match_with_neg)
        
        marker = " ← PERFECT COMPLEMENTATION" if comp_ok else ""
        print(f"  R={r:2d}: XOR-diff={diff_hex:04X}, CompOK={comp_ok}{marker}")
        
        if r == 16:
            final_orig = _pack(state_orig)
            final_comp = _pack(state_comp)
            print(f"  => E(P)={final_orig:04X}, E(~P)={final_comp:04X}, ~E(P)={(~final_orig)&0xFFFF:04X}")
