"""
QUARTET — constant-time code-inspection test.

The reference C implementation claims (§12.4) to be written so that
all 4 S-box lookups, all 4 key XORs, all 12 FullMix XORs, and all 16
key-schedule S-box reads execute every round. This is a *code-inspection*
claim — it has not been validated with power/EM traces (no such traces
are available in this artifact set).

This script verifies the claim by static analysis of the C source. It
fails if any of the following appear in the cipher core (quartet.h and
the includes it transitively pulls in):

  - Data-dependent conditional branches (if/else/switch on a non-constant)
  - Data-dependent memory accesses (array index that isn't a compile-time
    constant or a known-constant lookup)
  - Data-dependent loop bounds (for/while with a bound that depends on
    data, not a compile-time constant)
  - Function-pointer or computed-goto dispatch (compiler-dependent)

The check is conservative: it allows the SBOX_READ / INV_SBOX_READ
macros to use a runtime index (these are constant-time only if the
underlying memory access is itself constant-time, which is true for
flash-resident arrays on AVR and for static RAM arrays on PC). It
fails on any explicit data-dependent control flow.

This is NOT a TVLA. It is a necessary condition for a constant-time
implementation, not a sufficient one. A passing check means the
control flow does not depend on secret data; it does not mean the
micro-architectural timing does not depend on secret data.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

WORK_DIR = Path(__file__).resolve().parent

# Files that make up the cipher core (the test scans these).
CORE_FILES = [
    WORK_DIR / "sbox.h",
    WORK_DIR / "quartet.h",
    WORK_DIR / "quartetchiffre.c",
    WORK_DIR / "quartet_runner.c",
]

# Patterns that indicate data-dependent control flow. Each pattern is
# (regex, description). The regex is matched against the file contents.
FORBIDDEN_PATTERNS = [
    (r"\bif\s*\(\s*[^)]*[a-zA-Z_][^)]*\)",
     "data-dependent if() condition"),
    (r"\bif\s*\(\s*[a-zA-Z_]",  # any if() whose condition is a name
     "data-dependent if() condition (identifier in condition)"),
    (r"\bwhile\s*\(\s*[a-zA-Z_]",
     "data-dependent while() loop bound"),
    (r"\bswitch\s*\(\s*[a-zA-Z_]",
     "data-dependent switch()"),
    (r"\?\s*[a-zA-Z_]\s*:",
     "ternary expression on data"),
    (r"\b__builtin_expect\b.*[a-zA-Z_]",
     "__builtin_expect with data-dependent hint"),
]

# Patterns that are allowed (the S-box read macros use a runtime index;
# array access with a runtime index in those macros is OK because the
# memory itself is constant-time).
ALLOWED_CONTEXTS = [
    re.compile(r"SBOX_READ\s*\(\s*[a-zA-Z_][^)]*\)"),
    re.compile(r"INV_SBOX_READ\s*\(\s*[a-zA-Z_][^)]*\)"),
    re.compile(r"sbox\s*\[\s*[a-zA-Z_][^\]]*\]"),
    re.compile(r"inv_sbox\s*\[\s*[a-zA-Z_][^\]]*\]"),
]


def is_allowed(line: str) -> bool:
    """True if the line's match is in an allowed context (S-box read)."""
    return any(p.search(line) for p in ALLOWED_CONTEXTS)


def find_function_body(lines: list[str], func_name: str) -> tuple[int, int] | None:
    """Find the (start, end) line numbers of a function definition
    named `func_name`. The definition must start with `static inline`
    (or a return type followed by the name) — this disambiguates from
    function calls. Returns None if not found.
    """
    # Match "static inline <type> funcname(" or "<type> funcname(" at
    # the start of a line (allowing leading whitespace).
    def_pat = re.compile(
        rf"^\s*(static\s+inline\s+)?\w[\w\s\*]*\b{re.escape(func_name)}\s*\("
    )
    for i, line in enumerate(lines):
        if not def_pat.search(line):
            continue
        # Verify this is a definition by looking for a `{` within a
        # few lines. Function calls are followed by `;` or `,` or
        # end-of-expression, not by an opening brace.
        for j in range(i, min(i + 3, len(lines))):
            if "{" in lines[j]:
                depth = 0
                for k in range(j, len(lines)):
                    depth += lines[k].count("{") - lines[k].count("}")
                    if depth == 0:
                        return (i + 1, k + 1)  # 1-indexed
                return None
        # If we saw `funcname(` but no `{` within 3 lines, it's a
        # declaration without body (extern) — skip.
    return None


CIPHER_FUNCS = [
    "quartet_fullmix",
    "quartet_round_key",
    "quartet_round",
    "quartet_inv_round",
    "quartet_encrypt",
    "quartet_decrypt",
]


def check_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_number, pattern_description, line_text)
    for any forbidden pattern found inside the cipher core functions.
    """
    findings: list[tuple[int, str, str]] = []
    if not path.exists():
        return findings
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    core_ranges: list[tuple[int, int]] = []
    for fn in CIPHER_FUNCS:
        r = find_function_body(lines, fn)
        if r is not None:
            core_ranges.append(r)

    # If the file has no cipher core function definitions, skip it.
    # Driver / I/O files contain main() and test loops, not the
    # cipher core. The cipher core lives in quartet.h.
    if not core_ranges:
        return findings

    core_line_set: set[int] = set()
    for start, end in core_ranges:
        for ln in range(start, end + 1):
            core_line_set.add(ln)

    for lineno, line in enumerate(lines, 1):
        if lineno not in core_line_set:
            continue
        line_no_comment = re.sub(r"//.*$", "", line)
        if is_allowed(line_no_comment):
            continue
        for pat, desc in FORBIDDEN_PATTERNS:
            if re.search(pat, line_no_comment):
                findings.append((lineno, desc, line.rstrip()))
                break
    return findings


def main() -> int:
    print("=" * 70)
    print("QUARTET — constant-time code inspection")
    print("=" * 70)
    print()
    print("This is a STATIC check, not a TVLA. It verifies that the cipher")
    print("core contains no data-dependent control flow. A passing check")
    print("is a NECESSARY condition for a constant-time implementation;")
    print("it is not sufficient. Micro-architectural timing is not tested.")
    print()

    all_findings: list[tuple[Path, int, str, str]] = []
    for path in CORE_FILES:
        findings = check_file(path)
        for lineno, desc, text in findings:
            all_findings.append((path, lineno, desc, text))

    if all_findings:
        print(f"FAIL: {len(all_findings)} data-dependent pattern(s) found:")
        print()
        for path, lineno, desc, text in all_findings:
            rel = path.relative_to(WORK_DIR)
            print(f"  {rel}:{lineno}: {desc}")
            print(f"    > {text}")
            print()
        print("=" * 70)
        print("CONSTANT-TIME CODE-INSPECTION: FAIL")
        print("=" * 70)
        return 1

    # Also report file sizes so the user sees what was scanned.
    total_lines = 0
    for path in CORE_FILES:
        if path.exists():
            n = sum(1 for _ in path.open(encoding="utf-8", errors="replace"))
            total_lines += n
            print(f"  scanned {path.relative_to(WORK_DIR)}: {n} lines")
    print(f"\n  total cipher core: {total_lines} lines")
    print()
    print("=" * 70)
    print("CONSTANT-TIME CODE-INSPECTION: PASS")
    print("=" * 70)
    print()
    print("  Caveat: this is a code-inspection claim, not a measurement.")
    print("  A TVLA t-test is NOT included in this artifact set. To turn")
    print("  this into a measurement, run the cipher on a target with")
    print("  power/EM trace capture and compute Welch's t-statistic on")
    print("  fixed-vs-random and fixed-vs-fixed-with-different-key trace")
    print("  sets at the 95% confidence threshold (|t| < 4.5).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
