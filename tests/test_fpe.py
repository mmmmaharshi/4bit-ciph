"""QUARTET FPE — round-trip + tweak + benchmark."""
from __future__ import annotations
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fpe import fpe_encrypt, fpe_decrypt

def main():
    print("="*70)
    print("QUARTET FPE — Path 4 breakthrough")
    print("="*70)
    k=0x0123456789ABCDEF
    for p in ["0000000000000000","1234567890123456","9999999999999999"]:
        c=fpe_encrypt(p,k, tweak=0x1234)
        assert fpe_decrypt(c,k, tweak=0x1234)==p
        print(f"  {p} -> {c} -> OK (tweak sensitive: {fpe_encrypt(p,k,1)!=fpe_encrypt(p,k,2)})")
    t=time.time()
    for _ in range(1000): fpe_encrypt("1234567890123456",k)
    print(f"  1k FPE enc: {time.time()-t:.3f}s (~{1000/(time.time()-t):.0f} ops/s)")
    print("\nPASS")
    return 0
if __name__=="__main__":
    sys.exit(main())
