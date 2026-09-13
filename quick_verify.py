"""Quick verify round vs bitsliced."""
from python.cipher import _round, _round_bitsliced, _expand_key, _unpack, _pack

key = 0
p = 0x0000
r = 0

state_list = list(_unpack(p))
rk = _expand_key(key, 17)[r]

result_round = _round(list(state_list), rk, r)
print(f"_round result: {result_round}")

# Correct packing for bitsliced
state_int = _pack(state_list)
print(f"Correct packed: {state_int:#x}, nibbles: {[((state_int>>(12-4*i))&0xF) for i in range(4)]}")

result_rb = _round_bitsliced(state_int, rk, r)
result_rb_nibbles = [_pack([(result_rb>>(12-4*i))&0xF for i in range(4)])]
print(f"_round_bitsliced packed: {result_rb:#x}")
print(f"Match: {list(result_round) == [(result_rb>>(12-4*i))&0xF for i in range(4)]}")

# Also check E(0) full encryption
from python.cipher import quartet_encrypt
full_enc = quartet_encrypt(p, key, 16)
print(f"E_0(0) = {full_enc:#x}")