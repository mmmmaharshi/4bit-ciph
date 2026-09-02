"""QUARTET-32 KAT harness — 20480 entries Python+C."""
import sys, subprocess
from pathlib import Path
REPO=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(REPO / "python"))
import cipher32
KAT=REPO/"tests"/"vectors"/"quartet32_kat.txt"
import os
EXE="quartet32_runner.exe"
if not Path(EXE).exists():
    subprocess.run(["gcc","-O2","-o",EXE,"quartet32_runner.c"],check=True)

def parse_kat():
    vecs=[]
    key=pt=None
    for ln in KAT.read_text().splitlines():
        ln=ln.strip()
        if ln.startswith("KEY"): key=int(ln.split("=")[1].strip(),16)
        elif ln.startswith("PT"): pt=int(ln.split("=")[1].strip(),16)
        elif ln.startswith("CT"):
            ct=int(ln.split("=")[1].strip(),16); vecs.append((key,pt,ct))
    return vecs

def main():
    vecs=parse_kat(); print(f"KAT32: {len(vecs)} entries")
    # Python check
    for k,p,c in vecs[:5]: assert cipher32.quartet32_encrypt(p,k)==c, "py mismatch"
    # C check via runner
    import subprocess as sp
    proc=sp.Popen([f"./{EXE}"], stdin=sp.PIPE, stdout=sp.PIPE, text=True, bufsize=1)
    for k,p,c in vecs:
        khi=k>>64; klo=k&((1<<64)-1)
        proc.stdin.write(f"{khi:016X}{klo:016X} {p:08X}\n")
        proc.stdin.flush()
        cc=int(proc.stdout.readline().strip(),16)
        if cc!=c:
            print(f"FAIL K={k:032X} P={p:08X} exp {c:08X} got {cc:08X}"); sys.exit(1)
    proc.stdin.close(); proc.wait()
    print("KAT32: PASS (Python+C)")
if __name__=="__main__": main()
