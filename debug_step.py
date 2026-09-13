"""Debug step_encrypt bug - compare manual vs quartet_encrypt."""
from __future__ import annotations
import sys
sys.path.insert(0, "python")

from cipher import quartet_encrypt, _unpack, _pack, _rc, linear_layer, SBOX

# ---------------------------------------------------------------
# BUGGY version (mutating state in-place while reading it)
# ---------------------------------------------------------------
def step_encrypt(state, rk, r):
    c = [_rc(r,i) for i in range(4)]
    new = []
    for i in range(4):
        s = SBOX[state[i] ^ c[i] ^ rk]
        new.append(s ^ c[i] ^ rk)
    return linear_layer(new)

# ---------------------------------------------------------------
# CORRECT version (like cipher._round)
# ---------------------------------------------------------------
def step_correct(p, k, rk, r):
    """Match cipher._round exactly."""
    c0 = _rc(r, 0); c1 = _rc(r, 1); c2 = _rc(r, 2); c3 = _rc(r, 3)
    s0 = SBOX[p[0] ^ c0 ^ rk]; s1 = SBOX[p[1] ^ c1 ^ rk]
    s2 = SBOX[p[2] ^ c2 ^ rk]; s3 = SBOX[p[3] ^ c3 ^ rk]
    return linear_layer([s0 ^ c0 ^ rk, s1 ^ c1 ^ rk, s2 ^ c2 ^ rk, s3 ^ c3 ^ rk])

print("Comparing step_encrypt vs step_correct:")
print("=" * 70)

test_cases = [
    ([0,0,0,0], 0x0, 0),
    ([5,4,10,5], 0xF, 1),
    ([0xC,0xA,0xD,0xB], 0xE, 2),
]

for state, rk, r in test_cases:
    a = step_correct(list(state), rk, r)
    b = step_encrypt(list(state), rk, r)
    match = (a == b)
    print(f"  state={state}, rk={hex(rk)}, r={r}")
    print(f"    step_correct: {a}")
    print(f"    step_encrypt: {b}")
    print(f"    Match? {match}")
    if not match:
        print(f"    *** BUG CONFIRMED: step_encrypt mutates state mid-read! ***")
    print()

# ---------------------------------------------------------------
# Re-trace with CORRECT step function
# ---------------------------------------------------------------
print("\nCORRECT per-round trace for KEY=0 and KEY=hexdigits:")
print("=" * 70)

rk0_keys = [0x0, 0x123456789ABCDEF0]

for k_val in rk0_keys:
    print(f"\nKey={k_val:016X}:")
    from cipher import _expand_key
    k_rks = [_expand_key(k_val, 17)[r] for r in range(16)]
    kc = k_val ^ 0xFFFFFFFFFFFFFFFF
    kc_rks = [_expand_key(kc, 17)[r] for r in range(16)]
    
    p_state = list(_unpack(0x0000))  # P=0x0000
    comp_state = list(_unpack(0xFFFF))  # ~P=0xFFFF
    
    for r in range(17):
        if r < 16:
            p_state = step_correct(p_state, k_rks[r], r)
            comp_state = step_correct(comp_state, kc_rks[r], r)
        
        xor_diff = [(a^b) for a,b in zip(p_state, comp_state)]
        diff_hex = sum(d << (4*i) for i,d in enumerate(reversed(xor_diff)))
        neg_p = [(~s)&0xF for s in p_state]
        comp_with_neg = [c==n for c,n in zip(comp_state, neg_p)]
        comp_ok = all(comp_with_neg)
        
        marker = " <-- PERFECT COMPLEMENTATION" if comp_ok else ""
        print(f"  R={r:2d}: XOR-diff={diff_hex:04X}, CompOK={comp_ok}{marker}")
        
        if r == 16:
            final_orig = _pack(p_state)
            final_comp = _pack(comp_state)
            print(f"  => Manual: E(P=0)={final_orig:04X}, E(~P=FFFF)={final_comp:04X}, ~E(P)={(~final_orig)&0xFFFF:04X}")
            print(f"     Match? {(final_comp == ((~final_orig)&0xFFFF))}")
    
    # Also run quartet_encrypt directly
    c1 = quartet_encrypt(0x0000, k_val, 16)
    c2 = quartet_encrypt(0xFFFF, kc, 16)
    print(f"  => quartet_encrypt: E(0)={c1:04X}, E(FFFF)={c2:04X}, ~E(0)={(~c1)&0xFFFF:04X}")
    print(f"     Match? {(c2 == ((~c1)&0xFFFF))}")
