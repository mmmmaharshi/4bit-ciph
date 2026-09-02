"""
Random-vector cross-check: draw N random (key, pt) from the KAT
file, run both Python and C, and assert both match.

This is a thin wrapper over the KAT harness (tests/test_kats.py).
For a full 262,157-entry KAT verification, run `python tests/test_kats.py`.
For the canonical self-test, run `python cipher.py`. This script
exists as a quick "is the cipher still working?" sanity check that
runs in <1s.
"""
from __future__ import annotations

import os
import random
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "python"))

from cipher import quartet_decrypt, quartet_encrypt  # noqa: E402

C_RUNNER_SRC = _REPO_ROOT / "runners/quartet_runner.c"
C_RUNNER_EXE = _REPO_ROOT / "quartet_runner.exe"

VECTORS = 20
SEED = 0xDEADBEEF


def main() -> int:
    random.seed(SEED)
    pairs = [
        (random.randint(0, 2 ** 64 - 1), random.randint(0, 2 ** 16 - 1))
        for _ in range(VECTORS)
    ]

    # Python self-consistency (encrypt then decrypt).
    for key, pt in pairs:
        ct = quartet_encrypt(pt, key)
        if quartet_decrypt(ct, key) != pt:
            print(f"Python FAIL: pt=0x{pt:04X} key=0x{key:016X}")
            return 1

    # Build C runner.
    if C_RUNNER_EXE.exists():
        C_RUNNER_EXE.unlink()
    result = subprocess.run(
        ["gcc", "-O2", "-std=c11", "-I", str(_REPO_ROOT / "c"), "-I", str(_REPO_ROOT / "c"), "-I", str(_REPO_ROOT / "python"),
         "-o", str(C_RUNNER_EXE), str(C_RUNNER_SRC)],
        capture_output=True, text=True, cwd=str(_REPO_ROOT / "python"),
    )
    if result.returncode != 0:
        print(f"gcc error: {result.stderr}")
        return 1

    # C side: stdin/stdout contract.
    stdin = "\n".join(f"{k:016X} {p:04X}" for k, p in pairs) + "\n"
    result = subprocess.run(
        [str(C_RUNNER_EXE)], input=stdin, capture_output=True, text=True,
        timeout=30, cwd=str(_REPO_ROOT / "python"),
    )
    if result.returncode != 0:
        print(f"C runner error: {result.stderr}")
        return 1
    c_results = [int(ln, 16) for ln in result.stdout.strip().splitlines() if ln]

    # Compare.
    print(f"Cross-validation: Python vs C, {VECTORS} random test vectors\n")
    print(f"{'#':<3} {'Key':<18} {'PT':<6} {'Py_CT':<6} {'C_CT':<6} {'Match'}")
    print("-" * 60)
    ok = 0
    for i, ((k, p), py_ct, c_ct) in enumerate(zip(pairs, [quartet_encrypt(p, k) for k, p in pairs], c_results)):
        match = py_ct == c_ct
        if match:
            ok += 1
        print(f"{i:<3} 0x{k:016X} 0x{p:04X} 0x{py_ct:04X} 0x{c_ct:04X} "
              f"{'OK' if match else 'MISMATCH'}")
    print()
    print(f"SUCCESS: {ok}/{VECTORS} cross-validated test vectors match" if ok == VECTORS else f"FAIL: {ok}/{VECTORS} match")

    try:
        C_RUNNER_EXE.unlink()
    except OSError:
        pass

    return 0 if ok == VECTORS else 1


if __name__ == "__main__":
    sys.exit(main())
