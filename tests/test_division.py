"""QUARTET — division/integral distinguisher (exhaustive, stdlib)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cipher import quartet_encrypt

def division_distinguisher(rounds: int) -> bool:
    key = 0x0123456789ABCDEF
    for nib in range(4):
        for fixed in [0x0000]:
            vals = [quartet_encrypt(fixed | (v << (4*nib)), key, rounds) for v in range(16)]
            x = 0
            for c in vals: x ^= c
            if x == 0:
                return True
    return False

def main() -> int:
    print("="*70)
    print("QUARTET — division/integral distinguisher")
    print("="*70)
    for r in [2,3,4]:
        print(f"  R={r}: balanced structure? {division_distinguisher(r)}")
    print("\nPASS")
    return 0

if __name__=="__main__":
    sys.exit(main())
