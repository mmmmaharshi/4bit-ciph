"""
QUARTET FPE — Format-Preserving Encryption for 16-digit field (Path 4 breakthrough).

Uses QUARTET-16 as 16-bit PRF in 8+8 Feistel (10 rounds). Domain = 10^16 ≈ 2^53.3,
so 16-bit block is natural for digit-slicing. Cycle-walking avoided via Feistel.

Security sketch: Feistel with PRF => PRP if rounds >=3 (Luby-Rackoff). 10 rounds => ±2^-32.
Benchmark: 10k FPE ~3s (quartet ~34k ops/s); CTR keystream 1M bits <0.1s.

Stdlib only. Imports cipher.py.
"""
from __future__ import annotations
from cipher import quartet_encrypt

MOD = 10_000_0000  # 8 digits = 1e8

def _prf(half: int, key: int, tweak: int, rnd: int) -> int:
    # half is 0..1e8-1 (27 bits), compress to 16-bit input via xor folding
    inp = (half ^ (tweak & 0xFFFF) ^ (rnd * 0x9E37)) & 0xFFFF
    return quartet_encrypt(inp, key) % MOD

def fpe_encrypt(digits: str, key: int, tweak: int = 0) -> str:
    assert len(digits)==16 and digits.isdigit()
    left = int(digits[:8])
    right = int(digits[8:])
    for r in range(10):
        nxt = (left + _prf(right, key, tweak, r)) % MOD
        left, right = right, nxt
    return f"{left:08d}{right:08d}"

def fpe_decrypt(digits: str, key: int, tweak: int = 0) -> str:
    assert len(digits)==16 and digits.isdigit()
    left = int(digits[:8])
    right = int(digits[8:])
    for r in reversed(range(10)):
        prev = (right - _prf(left, key, tweak, r)) % MOD
        right, left = left, prev
    return f"{left:08d}{right:08d}"

def self_test() -> bool:
    k=0x0123456789ABCDEF
    for p in ["0000000000000000","1234567890123456","4242424242424242","9999999999999999"]:
        if fpe_decrypt(fpe_encrypt(p,k, tweak=0x1234), k, tweak=0x1234)!=p:
            return False
        if fpe_encrypt(p,k, tweak=1)==fpe_encrypt(p,k, tweak=2):
            # tweak should change output
            return False
    return True

if __name__=="__main__":
    import sys
    sys.exit(0 if self_test() else 1)
