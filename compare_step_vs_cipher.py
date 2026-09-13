"""Clean comparison: step function vs cipher."""
import sys
sys.path.insert(0, "python")
from cipher import _round, _round_bitsliced, _expand_key, quartet_encrypt, SBOX, _unpack, _pack, _rc, linear_layer

# Test with known inputs
key = 0
p = 0x0000
state = list(_unpack(p))
rk = _expand_key(key, 17)[0]
r = 0

print(f"Initial: state={state}, rk={rk:#x}, r={r}")

# Call _round directly
result_round = _round(list(state), rk, r)
print(f"_round: {result_round}")

# Build pre_mix manually to verify S-box + RC + RK
c = [_rc(r, i) for i in range(4)]
print(f"RC: {c}")
print(f"Inputs to SBOX: {[state[i]^c[i]^rk for i in range(4)]}")
pre_mix = [SBOX[state[i]^c[i]^rk] ^ c[i] ^ rk for i in range(4)]
print(f"Pre-mix: {pre_mix}")

# What _round_bitsliced does
bitsliced_in = int.from_bytes(bytes(state), 'big')  # Wrong packing?
print(f"Packed for bitsliced (bytes): {bitsliced_in:#x}")

correct_packed = (state[0]<<12)|(state[1]<<8)|(state[2]<<4)|state[3]
print(f"Correct packed: {correct_packed:#x}")

result_rb = _round_bitsliced(correct_packed, rk, r)
result_rb_nibbles = [(result_rb>>(12-4*i))&0xF for i in range(4)]
print(f"_round_bitsliced nibbles: {result_rb_nibbles}")

# Verify _round == _round_bitsliced
match = (result_round == result_rb_nibbles)
print(f"Match? {match}")

# Also verify quartet_encrypt
full_result = quartet_encrypt(p, key, 16)
print(f"quartet_encrypt(E(0)): {full_result:#x}")
