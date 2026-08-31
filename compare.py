"""
Cross-validate the Python cipher against the C binary.

Contract: input is "<16-hex-key> <4-hex-pt>" lines on the C binary's stdin,
output is one "<4-hex-ct>" line per input on its stdout. The cipher source
lives in cipher.py and quartet.h respectively — this script only owns the
harness.
"""
import os
import random
import subprocess
import sys

from cipher import quartet_decrypt, quartet_encrypt

WORK_DIR = r"C:\Users\manoh\OneDrive\Desktop\4bit-ciph"
C_FILE = os.path.join(WORK_DIR, "quartet_runner.c")
EXE_FILE = os.path.join(WORK_DIR, "quartet_runner.exe")

random.seed(0xDEADBEEF)
TEST_COUNT = 20


def compile_runner() -> None:
    """Build quartet_runner.exe from quartet_runner.c.

    quartet_runner.c includes quartet.h, which includes sbox.h — the cipher
    comes from the shared headers, not from a string embedded in this script.
    """
    result = subprocess.run(
        ["gcc", "-O3", "-std=c11", "-I", WORK_DIR, "-o", EXE_FILE, C_FILE],
        capture_output=True, text=True, cwd=WORK_DIR,
    )
    if result.returncode != 0:
        print(f"FAIL: gcc error: {result.stderr}")
        sys.exit(1)


def run_c(vectors: list[tuple[int, int]]) -> list[int]:
    """Send vectors to the C binary, return its ciphertexts."""
    stdin = "\n".join(f"{key:016X} {pt:04X}" for key, pt in vectors) + "\n"
    result = subprocess.run(
        [EXE_FILE], input=stdin, capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"FAIL: C run failed: {result.stderr}")
        sys.exit(1)
    return [int(line.strip(), 16) for line in result.stdout.strip().split("\n")]


def main() -> int:
    compile_runner()

    vectors = [
        (random.randint(0, 2 ** 64 - 1), random.randint(0, 2 ** 16 - 1))
        for _ in range(TEST_COUNT)
    ]

    # Python side: cipher source = cipher.py, never inline.
    py_results = [quartet_encrypt(pt, key) for key, pt in vectors]

    # Python must also be self-consistent (encryption roundtrip).
    for (key, pt), ct in zip(vectors, py_results):
        if quartet_decrypt(ct, key) != pt:
            print(f"  Python FAIL: pt=0x{pt:04X} key=0x{key:016X}")
            return 1

    c_results = run_c(vectors)

    print(f"Cross-validation: Python vs C, {TEST_COUNT} random test vectors\n")
    print(f"{'#':<3} {'Key':<18} {'PT':<6} {'Py_CT':<6} {'C_CT':<6} {'Match'}")
    print("-" * 60)
    all_match = True
    for i, ((key, pt), py_ct, c_ct) in enumerate(zip(vectors, py_results, c_results)):
        if py_ct != c_ct:
            all_match = False
        print(f"{i:<3} 0x{key:016X} 0x{pt:04X} 0x{py_ct:04X} 0x{c_ct:04X} "
              f"{'OK' if py_ct == c_ct else 'MISMATCH'}")

    print()
    if all_match:
        print(f"SUCCESS: All {TEST_COUNT} cross-validated test vectors MATCH")
        return 0
    print("FAIL: Some test vectors differ between Python and C")
    return 1


if __name__ == "__main__":
    sys.exit(main())
