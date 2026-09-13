"""Direct comparison: quartet_encrypt vs manual trace."""
from python.cipher import _expand_key, quartet_encrypt, _unpack, _pack, _rc, linear_layer, SBOX

key = 0x8765432109CDEFE0
kc = key ^ 0xFFFFFFFFFFFFFFFF

ek_k = _expand_key(key, 17)
ek_kc = _expand_key(kc, 17)

def step_n(rk, r):
    """One round step — matches cipher._round exactly."""
    c = [_rc(r,i) for i in range(4)]
    out = []
    for i in range(4):
        s = SBOX[c[i] ^ rk]
        out.append(s ^ c[i] ^ rk)
    return linear_layer(out)

# For P=0: initial state = [0,0,0,0]
p_state = list(_unpack(0))
comp_state = list(_unpack((~0)&0xFFFF))

print("Manual trace (matches cipher._round):")
for r in range(17):
    if r < 16:
        p_state = step_n(ek_k[r], r)
        comp_state = step_n(ek_kc[r], r)
    
    if r <= 3 or r >= 15:
        xor_d = sum(((a^b)<<4*i) for i,(a,b) in enumerate(zip(reversed(comp_state), reversed(p_state))))
        print(f"R={r}: XOR-diff after mix = {xor_d:04X}")
        
        if r == 16:
            final_p = _pack(p_state)
            final_c = _pack(comp_state)
            print(f"  Final: E(P)= {final_p:04X}, E(~P)={final_c:04X}")

# Compare with quartet_encrypt
c1 = quartet_encrypt(0, key, 16)
c2 = quartet_encrypt((~0)&0xFFFF, kc, 16)
print(f"\nquartet_encrypt: E(P)= {c1:04X}, E(~P)={c2:04X}")
print(f"Match? orig={_pack(step_n(ek_k[15], 15)) == c1}")
