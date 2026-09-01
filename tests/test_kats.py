"""
QUARTET — Known Answer Test (KAT) harness.

Reads tests/vectors/quartet_kat.txt, runs the Python reference AND
the C reference (via the runner) against every entry, and asserts
both match the expected CT. The KAT file is the test surface; the
implementations are the systems under test.

Why this is not a tautology:

  1. The KAT lives in a separate file (tests/vectors/quartet_kat.txt).
  2. The C reference is a *different* implementation, compiled from
     a different language. It runs as a subprocess and reads the
     KAT vectors from its stdin. Its output is compared to the KAT.
  3. The Python reference is also a separate path: it imports
     cipher.py and calls quartet_encrypt. The KAT asserts that
     the Python reference matches the values it generated
     yesterday (or last commit). If cipher.py changes silently,
     the KAT regeneration produces a different file, the diff is
     the audit trail, and this test catches any mismatch.

The 13 spec vectors (SPEC §9) are a Known Answer Test set: they
are values the cipher MUST produce, published in the spec. The
full-space KAT (65536 PT x 4 keys = 262144 entries) is generated
by the reference and serves as a regression test against the
implementations.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cipher import quartet_encrypt  # noqa: E402

KAT_PATH = _REPO_ROOT / "tests" / "vectors" / "quartet_kat.txt"
C_RUNNER_SRC = _REPO_ROOT / "quartet_runner.c"
C_RUNNER_EXE = _REPO_ROOT / "quartet_runner.exe"

# Hard-locked golden vectors from SPEC §9 — independent of KAT file.
# If cipher.py is broken and KAT is regenerated, Phase 1/2 still pass
# (tautology), but this Phase 0 fails. This is the external oracle.
# These match tests/vectors/quartet_kat.txt Section 2 and SPEC §9.
GOLDEN_VECTORS: list[tuple[int, int, int]] = [
    (0x0123456789ABCDEF, 0x0000, 0xDDDD),
    (0x0123456789ABCDEF, 0x0001, 0xDDDF),
    (0x0123456789ABCDEF, 0x1234, 0x6927),
    (0x0123456789ABCDEF, 0xDEAD, 0xBC0B),
    (0x0123456789ABCDEF, 0xFFFF, 0x5555),
    (0xFFFFFFFFFFFFFFFF, 0x0000, 0x3333),
    (0xFFFFFFFFFFFFFFFF, 0x0001, 0x333A),
    (0xFFFFFFFFFFFFFFFF, 0x1234, 0x19B4),
    (0x0000000000000000, 0x0000, 0x4444),
    (0x0000000000000000, 0x0001, 0x4440),
    (0x0000000000000000, 0x1234, 0xCF7E),
    (0xFEDCBA9876543210, 0x0000, 0x9999),
    (0xFEDCBA9876543210, 0x1234, 0x50CF),
]


def parse_kat(path: Path) -> list[tuple[int, int, int, str]]:
    """Parse a KAT file. Returns list of (key, pt, expected_ct, source).

    `source` is "kat" for full-space entries, "spec" for SPEC §9 entries.
    """
    entries: list[tuple[int, int, int, str]] = []
    pending_key: int | None = None
    pending_pt: int | None = None
    pending_source: str = "kat"
    in_spec_section = False
    in_full_section = False

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if "Section 2" in line or "SPEC §9" in line:
                in_spec_section = True
                in_full_section = False
            elif "Section 1" in line:
                in_spec_section = False
                in_full_section = True
            elif "--- Key" in line:
                in_full_section = True
            continue
        if line.startswith("KEY"):
            val = line.split("=", 1)[1].strip()
            pending_key = int(val, 16)
            pending_source = "spec" if in_spec_section else "kat"
        elif line.startswith("PT") and pending_key is not None:
            pending_pt = int(line.split("=", 1)[1].strip(), 16)
        elif line.startswith("CT") and pending_key is not None and pending_pt is not None:
            expected_ct = int(line.split("=", 1)[1].strip(), 16)
            entries.append((pending_key, pending_pt, expected_ct, pending_source))
            pending_key = None
            pending_pt = None
    return entries


def build_c_runner() -> None:
    """Compile quartet_runner.c. The runner reads KEY and PT on stdin,
    writes CT on stdout. Its cipher source is quartet.h, which is
    shared with the canonical C reference.
    """
    if C_RUNNER_EXE.exists():
        C_RUNNER_EXE.unlink()
    result = subprocess.run(
        ["gcc", "-O2", "-std=c11", "-I", str(_REPO_ROOT),
         "-o", str(C_RUNNER_EXE), str(C_RUNNER_SRC)],
        capture_output=True, text=True, cwd=str(_REPO_ROOT),
    )
    if result.returncode != 0:
        print(f"FAIL: gcc error: {result.stderr}")
        sys.exit(1)


def run_c_runner(entries: list[tuple[int, int, int, str]]) -> list[int]:
    """Send every (key, pt) to the C runner, return its CTs in order."""
    stdin = "\n".join(f"{k:016X} {p:04X}" for k, p, _, _ in entries) + "\n"
    result = subprocess.run(
        [str(C_RUNNER_EXE)], input=stdin, capture_output=True, text=True,
        timeout=600, cwd=str(_REPO_ROOT),
    )
    if result.returncode != 0:
        print(f"FAIL: C runner returned {result.returncode}: {result.stderr}")
        sys.exit(1)
    lines = [ln for ln in result.stdout.strip().splitlines() if ln.strip()]
    if len(lines) != len(entries):
        print(f"FAIL: C runner returned {len(lines)} lines, expected {len(entries)}")
        sys.exit(1)
    return [int(ln.strip(), 16) for ln in lines]


def main() -> int:
    print("=" * 70)
    print("QUARTET — Known Answer Test (KAT) harness")
    print("=" * 70)
    print()

    if not KAT_PATH.exists():
        print(f"FAIL: KAT file missing: {KAT_PATH}")
        print("Generate it with: python tests/generate_kat.py")
        return 1

    entries = parse_kat(KAT_PATH)
    spec_count = sum(1 for e in entries if e[3] == "spec")
    full_count = sum(1 for e in entries if e[3] == "kat")
    print(f"  KAT: {KAT_PATH.relative_to(_REPO_ROOT)}")
    print(f"  {len(entries)} entries: {full_count} full-space + {spec_count} spec")
    print(f"  Golden: {len(GOLDEN_VECTORS)} locked vectors (SPEC §9)")
    print()

    # Phase 0: Golden vectors (external oracle) — Python and C vs SPEC §9.
    # This is the non-tautological test: even if KAT is stale/regenerated,
    # these 13 vectors must match.
    print(f"  Phase 0: Golden vectors vs SPEC §9 ({len(GOLDEN_VECTORS)} entries) ...", end="", flush=True)
    golden_py_fail = 0
    for k, p, exp in GOLDEN_VECTORS:
        if quartet_encrypt(p, k) != exp:
            golden_py_fail += 1
    if golden_py_fail:
        print(f" FAIL ({golden_py_fail} python mismatches)")
        return 1
    # Build C runner early for golden C check
    build_c_runner()
    golden_c_results = run_c_runner([(k, p, exp, "golden") for k, p, exp in GOLDEN_VECTORS])
    golden_c_fail = sum(1 for (k, p, exp), got in zip(GOLDEN_VECTORS, golden_c_results) if got != exp)
    if golden_c_fail:
        print(f" FAIL ({golden_c_fail} C mismatches)")
        return 1
    print(" OK")

    # Phase 1: Python reference vs KAT (sanity — should never fail
    # unless the KAT was edited by hand or generated from a different
    # cipher.py than the current one).
    print(f"  Phase 1: Python reference vs KAT ...", end="", flush=True)
    py_mismatches = 0
    first_py_mismatch = None
    for k, p, exp, _ in entries:
        got = quartet_encrypt(p, k)
        if got != exp:
            py_mismatches += 1
            if first_py_mismatch is None:
                first_py_mismatch = (k, p, exp, got)
    if py_mismatches:
        print(f" FAIL ({py_mismatches} mismatches)")
        if first_py_mismatch:
            k, p, exp, got = first_py_mismatch
            print(f"  first mismatch: K=0x{k:016X} P=0x{p:04X} "
                  f"KAT=0x{exp:04X} got=0x{got:04X}")
        print("  (KAT may be stale; regenerate with python tests/generate_kat.py)")
        return 1
    print(" OK")
    print()

    # Phase 2: C reference vs KAT (the actual research-acceptable test).
    # The C binary is built from quartet_runner.c, which is a different
    # path from the KAT generator. If they disagree, the cipher is
    # broken or the C compilation is broken.
    # (Runner already built in Phase 0; rebuild if missing)
    if not C_RUNNER_EXE.exists():
        print("  Phase 2: building C runner ...", end="", flush=True)
        build_c_runner()
        print(" OK")
    else:
        print("  Phase 2: C runner already built ... OK")
    print(f"  Phase 2: C reference vs KAT ({len(entries)} entries) ...", end="", flush=True)
    c_results = run_c_runner(entries)
    c_mismatches = 0
    first_c_mismatch = None
    for (k, p, exp, _), got in zip(entries, c_results):
        if got != exp:
            c_mismatches += 1
            if first_c_mismatch is None:
                first_c_mismatch = (k, p, exp, got)
    if c_mismatches:
        print(f" FAIL ({c_mismatches} mismatches)")
        if first_c_mismatch:
            k, p, exp, got = first_c_mismatch
            print(f"  first mismatch: K=0x{k:016X} P=0x{p:04X} "
                  f"KAT=0x{exp:04X} got=0x{got:04X}")
        return 1
    print(" OK")
    print()

    # Clean up the C binary.
    try:
        C_RUNNER_EXE.unlink()
    except OSError:
        pass

    print("=" * 70)
    print("KAT: PASS (Python + C both match all entries)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
