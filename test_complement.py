"""Clean verification of complementation symmetry."""
from __future__ import annotations
import sys
sys.path.insert(0, "python")

from cipher import quartet_encrypt, _expand_key, _unpack, _pack, _rc, linear_layer, SBOX

# Correct manual step — matches cipher._round exactly
def correct_round(state, rk, r):
    c = [_rc(r,i) for i in range(4)]
    out = []
    for i in range(4):
        s = SBOX[state[i] ^ c[i] ^ rk]
        out.append(s ^ c[i] ^ rk)
    return linear_layer(out)

print("Complementation symmetry test:")
print("=" * 70)

for k_val in [0, 0x123456789ABCDEF0]:
    kc = k_val ^ 0xFFFFFFFFFFFFFFFF
    print(f"\nKey={k_val:016X}, ~K={kc:016X}")
    
    # Manual trace through all 16 rounds
    p_state = list(_unpack(0x0000))
    comp_state = list(_unpack(0xFFFF))
    k_rks = [_expand_key(k_val, 17)[r] for r in range(16)]
    kc_rks = [_expand_key(kc, 17)[r] for r in range(16)]
    
    comp_holds_all = True
    for r in range(17):
        if r < 16:
            p_state = correct_round(p_state, k_rks[r], r)
            comp_state = correct_round(comp_state, kc_rks[r], r)
        
        neg_p = [(~s)&0xF for s in p_state]
        ok = (comp_state == neg_p)
        if not ok:
            comp_holds_all = False
        
        xor_diff = sum(((a^b) << (4*i)) for i,(a,b) in enumerate(zip(reversed(comp_state), reversed(neg_p))))
        
        if r <= 3 or r >= 15 or not ok:
            marker = " <-- OK" if ok else " <-- BREAKS!"
            print(f"  R={r:2d}: XOR-diff={(~((p_state[0]<<12)|(p_state[1]<<8)|(p_state[2]<<4)|p_state[3]))&0xFFFF:04X}, CompOK={ok}{marker}")
        
        if r == 16:
            final_orig = _pack(p_state)
            final_comp = _pack(comp_state)
            print(f"  => Manual: E(0)={final_orig:04X}, E(FFFF)={final_comp:04X}, Match={final_comp==(~final_orig)&0xFFFF}")
    
    # Compare with quartet_encrypt
    c1 = quartet_encrypt(0x0000, k_val, 16)
    c2 = quartet_encrypt(0xFFFF, kc, 16)
    print(f"  => quartet_encrypt: E(0)={c1:04X}, E(FFFF)={c2:04X}, Match={c2==(~c1)&0xFFFF}")
    
    # Check: do both match on E(0)?
    print(f"  => Both agree on E(0)? {final_orig == c1}")
