"""Verify step_correct vs _round_bitsliced."""
from python.cipher import _round_bitsliced, _expand_key, quartet_encrypt
import random

# Test a random key (not KEY=0, not KEY=hexdigits)
key = 0x8765432109CDEFE0
kc = key ^ 0xFFFFFFFFFFFFFFFF

print("Key:", hex(key))
print("~Key:", hex(kc))

ek_k = _expand_key(key, 17)
ek_kc = _expand_key(kc, 17)
deltas = [(ek_kc[r] ^ ek_k[r]) for r in range(16)]
uniform = all(d == 0xF for d in deltas)
print(f"Uniform delta=0xF? {uniform}")
print(f"First 4 deltas: {[hex(d) for d in deltas[:4]]}")

# Compare step_correct (manual) vs _round_bitsliced
from python.cipher import _unpack, _pack, _rc, linear_layer, SBOX

def step_correct(state_list, rk, r):
    """Match cipher._round exactly."""
    c = [_rc(r,i) for i in range(4)]
    new = []
    for i in range(4):
        s = SBOX[state_list[i] ^ c[i] ^ rk]
        new.append(s ^ c[i] ^ rk)
    return linear_layer(new)

p = 0x0000
state_orig = list(_unpack(p))
state_comp = list(_unpack((~p)&0xFFFF))

for r in range(17):
    if r < 16:
        rk_o = ek_k[r]
        rk_c = ek_kc[r]
        
        # step_correct (nibble-level)
        state_orig_nc = step_correct(list(state_orig), rk_o, r)
        state_comp_nc = step_correct(list(state_comp), rk_c, r)
        
        # _round_bitsliced (packed)
        state_orig_rb = _round_bitsliced(int.from_bytes(bytes([int(x) for x in state_orig]), 'big'), rk_o, r)
        state_comp_rb = _round_bitsliced(int.from_bytes(bytes([int(x) for x in state_comp]), 'big'), rk_c, r)
        
        # Convert rb back to nibble list
        state_orig_rb_nl = [(state_orig_rb >> (12-4*i)) & 0xF for i in range(4)]
        state_comp_rb_nl = [(state_comp_rb >> (12-4*i)) & 0xF for i in range(4)]
        
        nc_match = (state_orig_nc == state_orig_rb_nl)
        comp_nc_match = (state_comp_nc == state_comp_rb_nl)
        
        print(f"R={r}: nc_match={nc_match} comp_nc_match={comp_nc_match}")
        
        state_orig = state_orig_nc
        state_comp = state_comp_nc
    
    if r == 16:
        final_nc_orig = _pack(state_orig)
        final_nc_comp = _pack(state_comp)
        
        # Also call quartet_encrypt
        c_orig = quartet_encrypt(p, key, 16)
        c_comp = quartet_encrypt((~p)&0xFFFF, kc, 16)
        
        print(f"\nFinal nc_orig={final_nc_orig:04X}, nc_comp={final_nc_comp:04X}")
        print(f"quartet_encrypt: orig={c_orig:04X}, comp={c_comp:04X}")
        print(f"Match nc vs qe? orig={final_nc_orig==c_orig}, comp={final_nc_comp==c_comp}")
        
        # Check complement
        xor_diff = final_nc_comp ^ (~final_nc_orig)&0xFFFF
        print(f"Complement check: nc_comp XOR ~nc_orig = {xor_diff:04X}")
        print(f"Perfect complement? {xor_diff == 0}")
