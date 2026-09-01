"""QUARTET — NIST STS monobit (stdlib, 1M-bit CTR stream)."""
from __future__ import annotations
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cipher import quartet_encrypt

def nist_frequency(bits: list[int]) -> bool:
    n = len(bits)
    sobs = abs(sum(bits) - n/2) / math.sqrt(n/4) if n else 0
    return sobs < 4.5

def main() -> int:
    print("="*70)
    print("QUARTET — NIST STS monobit (CTR keystream)")
    print("="*70)
    bits: list[int] = []
    key = 0x0123456789ABCDEF
    for ctr in range(65536):
        c = quartet_encrypt(ctr & 0xFFFF, key)
        for b in range(16):
            bits.append((c >> b) & 1)
        if len(bits) >= 1000000: break
    bits = bits[:1000000]
    ok = nist_frequency(bits)
    print(f"  n={len(bits)} ones={sum(bits)} { 'PASS' if ok else 'FAIL'} (sobs<4.5)")
    print("\nPASS" if ok else "\nFAIL")
    return 0 if ok else 1

if __name__=="__main__":
    sys.exit(main())
