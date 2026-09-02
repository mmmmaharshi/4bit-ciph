"""QUARTET-32 thin 20-vector sanity check (random Python vs C)."""
import random, subprocess, sys, os
import cipher32

EXE="quartet32_runner.exe"
if not os.path.exists(EXE):
    import subprocess as sp
    sp.run(["gcc","-O2","-o",EXE,"quartet32_runner.c"], check=True)

random.seed(12345)
procs = subprocess.Popen([f"./{EXE}"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
ok=0
for i in range(20):
    pt = random.getrandbits(32)
    khi = random.getrandbits(64); klo = random.getrandbits(64)
    key = (khi<<64)|klo
    py = cipher32.quartet32_encrypt(pt, key)
    procs.stdin.write(f"{khi:016X}{klo:016X} {pt:08X}\n"); procs.stdin.flush()
    c = int(procs.stdout.readline().strip(),16)
    match="OK" if py==c else "FAIL"
    print(f"{i:2d} {key:032X} {pt:08X} {py:08X} {c:08X} {match}")
    if py==c: ok+=1
    else: sys.exit(1)
procs.stdin.close(); procs.wait()
print(f"\nSUCCESS: {ok}/20 cross-validated (QUARTET-32)" if ok==20 else "FAIL")
sys.exit(0 if ok==20 else 1)
