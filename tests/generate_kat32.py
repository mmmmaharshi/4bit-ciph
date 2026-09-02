"""QUARTET-32 — generate KAT (thin adapter over cipher32). 4096 sample PT x 4 keys + 13 spec = 164+? sampled, not 2^32."""
import sys, random
from datetime import date
from pathlib import Path
_REPO_ROOT=Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "python") not in sys.path: sys.path.insert(0,str(_REPO_ROOT / "python"))
from cipher32 import quartet32_encrypt
SPEC_KEYS=[0x0123456789ABCDEF0123456789ABCDEF,0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,0x0,0xFEDCBA9876543210FEDCBA9876543210]
SPEC_VECTORS=[(0x0123456789ABCDEF0123456789ABCDEF,0x00000000),(0x0123456789ABCDEF0123456789ABCDEF,0x12345678),(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,0x00000000)]
VPATH=_REPO_ROOT/"tests"/"vectors"/"quartet32_kat.txt"
def generate():
    lines=[]; today=date.today().isoformat()
    lines+=["# QUARTET-32 KAT — Generated "+today,"# Block 32 bits, Key 128 bits, R16","# DO NOT EDIT — regenerate with `python tests/generate_kat32.py`",""]
    lines+=["# Section 1: sampled KAT 4096 PT x 4 keys = 16384 entries",""]
    total=0
    for key in SPEC_KEYS:
        lines.append(f"# --- Key = 0x{key:032X} ---"); lines.append("")
        for pt in range(4096):
            ct=quartet32_encrypt(pt, key)
            lines+= [f"KEY = {key:032X}", f"PT  = {pt:08X}", f"CT  = {ct:08X}"]; total+=1
        lines.append("")
    # random larger sample
    random.seed(42)
    for _ in range(4096):
        key=random.getrandbits(128); pt=random.getrandbits(32); ct=quartet32_encrypt(pt,key)
        lines+= [f"KEY = {key:032X}", f"PT  = {pt:08X}", f"CT  = {ct:08X}"]; total+=1
    lines.append("")
    lines.append(f"# Total KAT entries: {total}")
    return "\n".join(lines)
def main():
    content=generate(); VPATH.parent.mkdir(parents=True, exist_ok=True); VPATH.write_text(content,encoding="utf-8")
    print(f"Wrote {VPATH.relative_to(_REPO_ROOT)} {len(content.splitlines())} lines")
    return 0
if __name__=="__main__": sys.exit(main())
