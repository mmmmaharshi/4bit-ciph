"""
QUARTET — generate the Known Answer Test (KAT) vector file.

The KAT file is the test surface for the cipher. The implementation
(`cipher.py` for Python, `quartet.h` for C) is the system under test;
the test reads the KAT, runs the implementation, and compares.

This script regenerates the KAT from the Python reference. NIST CAVP
follows the same pattern: a reference implementation generates the
expected outputs, and the SUT is checked against them. The KAT is
*not* a tautology because:

  1. The KAT lives in a separate file (tests/vectors/quartet_kat.txt).
  2. The test that uses the KAT runs a *different* implementation
     (the C reference) against it.
  3. If the Python reference changes, the KAT diff is the audit
     trail; the human reviewer sees what changed and decides.

Format: NIST CAVP-style
  KEY = <16 hex>
  PT  = <4 hex>
  CT  = <4 hex>

with a header (cipher name, parameters, generation date) and a
trailer with the 13 spec test vectors (SPEC §9) marked as
"Known Answer Test".

Coverage: 65536 PT x 4 spec keys = 262,144 KAT entries, plus the
13 spec vectors. Regeneration should be a no-op (byte-identical
file) when cipher.py and the spec vectors are unchanged. If a
change to cipher.py alters the KAT, the diff must be reviewed
before committing.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cipher import quartet_encrypt  # noqa: E402

# Spec test keys (SPEC §9, §10.3, §10.4).
SPEC_KEYS = [
    0x0123456789ABCDEF,
    0xFFFFFFFFFFFFFFFF,
    0x0000000000000000,
    0xFEDCBA9876543210,
]

# Spec test vectors (SPEC §9).
SPEC_VECTORS = [
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

VECTORS_PATH = _REPO_ROOT / "tests" / "vectors" / "quartet_kat.txt"


def generate() -> str:
    """Build the KAT file content as a string."""
    lines: list[str] = []
    today = date.today().isoformat()
    lines.append("# QUARTET Known Answer Test (KAT) — Generated " + today)
    lines.append("#")
    lines.append("# Cipher:    QUARTET-16/64")
    lines.append("# Block:     16 bits (4 nibbles)")
    lines.append("# Key:       64 bits (16 nibbles)")
    lines.append("# Rounds:    16")
    lines.append("# Generated: " + today)
    lines.append("# Source:    tests/generate_kat.py (uses cipher.py)")
    lines.append("#")
    lines.append("# DO NOT EDIT — regenerate with `python tests/generate_kat.py`")
    lines.append("#")
    lines.append("# Format: NIST CAVP-style, three lines per vector:")
    lines.append("#   KEY = <16 hex>")
    lines.append("#   PT  = <4  hex>")
    lines.append("#   CT  = <4  hex>")
    lines.append("#")
    lines.append("# Coverage: 65536 PT x 4 spec keys = 262,144 KAT entries.")
    lines.append("#           + 13 spec test vectors (SPEC §9).")
    lines.append("#")
    lines.append("# ============================================================================")
    lines.append("# Section 1: full-space KAT (65536 PT x 4 keys)")
    lines.append("# ============================================================================")
    lines.append("")

    total = 0
    for key in SPEC_KEYS:
        lines.append(f"# --- Key = 0x{key:016X} ---")
        lines.append("")
        for pt in range(65536):
            ct = quartet_encrypt(pt, key)
            lines.append(f"KEY = {key:016X}")
            lines.append(f"PT  = {pt:04X}")
            lines.append(f"CT  = {ct:04X}")
            total += 1
        lines.append("")

    lines.append("# ============================================================================")
    lines.append("# Section 2: Known Answer Test (SPEC §9) — published spec vectors")
    lines.append("# ============================================================================")
    lines.append("")
    for key, pt, expected_ct in SPEC_VECTORS:
        ct = quartet_encrypt(pt, key)
        assert ct == expected_ct, (
            f"Spec vector mismatch: K=0x{key:016X} P=0x{pt:04X} "
            f"got=0x{ct:04X} expected=0x{expected_ct:04X}"
        )
        lines.append(f"# SPEC §9: K=0x{key:016X} P=0x{pt:04X} -> C=0x{ct:04X}")
        lines.append(f"KEY = {key:016X}")
        lines.append(f"PT  = {pt:04X}")
        lines.append(f"CT  = {ct:04X}")
        lines.append("")
        total += 1

    lines.append(f"# Total KAT entries: {total}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    content = generate()
    VECTORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    VECTORS_PATH.write_text(content, encoding="utf-8")
    # Line count and entry count for the human eye.
    lines = content.splitlines()
    entries = (len(lines) - sum(1 for ln in lines if ln.startswith("#") or ln == "")) // 3
    print(f"Wrote {VECTORS_PATH.relative_to(_REPO_ROOT)}")
    print(f"  {len(lines)} lines, ~{entries} KAT entries (262157 expected)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
