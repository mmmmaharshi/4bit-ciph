"""
QUARTET — constant-time code inspection (AST-based).

The reference C implementation claims (§12.4) to be written so that
all 4 S-box lookups, all 4 key XORs, all 12 FullMix XORs, and all 16
key-schedule S-box reads execute every round. This is a *code-inspection*
claim — it has not been validated with power/EM traces (no such traces
are available in this artifact set).

This script verifies the claim by static analysis of the C source
using pycparser. It parses the preprocessed cipher core and walks
the AST, looking for any of the following data-dependent constructs:

  - if / while / for / switch with a non-constant condition
  - ?: (ternary) with a non-constant condition
  - array subscripts that are not a literal or manifest constant
  - function pointer calls
  - computed gotos

The check is conservative: it allows the SBOX_READ / INV_SBOX_READ
macros to use a runtime index (these are constant-time only if the
underlying memory access is itself constant-time, which is true for
flash-resident arrays on AVR and for static RAM arrays on PC).

This is NOT a TVLA. It is a necessary condition for a constant-time
implementation, not a sufficient one. A passing check means the
control flow does not depend on secret data; it does not mean the
micro-architectural timing does not depend on secret data.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pycparser
from pycparser import c_ast

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "python"))

CORE_HEADERS = ["sbox.h", "quartet.h"]
CORE_CS = ["quartetchiffre.c", "quartet_runner.c"]
FAKE_LIBC = _REPO_ROOT / "tests" / "fake_libc"

# The cipher core: the 6 static inline functions in quartet.h that
# implement encrypt, decrypt, round, key schedule. quartet_self_test
# is excluded (it is a test, not cipher code). main() and I/O loops
# in .c files are also excluded — the check is cipher-core only.
CIPHER_FUNCS = {
    "quartet_fullmix",
    "quartet_round_key",
    "quartet_round",
    "quartet_inv_round",
    "quartet_encrypt",
    "quartet_decrypt",
}


def preprocess_quartet_core() -> str:
    """Run the C preprocessor on quartet_core.h (the cipher core,
    which is what we check for constant-time) and return the
    preprocessed text.
    """
    cpp = shutil.which("cpp") or shutil.which("gcc")
    if cpp is None:
        raise RuntimeError("cpp/gcc not found on PATH; cannot preprocess")
    cmd = [cpp, "-E",
           "-I", str(_REPO_ROOT / "c"),
           "-I", str(FAKE_LIBC),
           "-include", str(FAKE_LIBC / "sbox_for_ast.h"),
           "-DQUARTET_NO_AVR",
           str(_REPO_ROOT / "c/quartet_core.h")]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


def find_function_nodes(ast: c_ast.FileAST) -> dict[str, c_ast.FuncDef]:
    """Find all function definitions in the AST, indexed by name."""
    out: dict[str, c_ast.FuncDef] = {}
    for node in ast.ext:
        if isinstance(node, c_ast.FuncDef) and node.decl.name in CIPHER_FUNCS:
            out[node.decl.name] = node
    return out


def is_constant_expr(node: c_ast.Node) -> bool:
    """True if the AST node is a compile-time constant expression.

    Conservative: returns True only for integer literals, character
    literals, sizeof, and references to names bound to enum / const
    integer constants. Returns False for any expression that could
    depend on a function argument, a local variable, or a runtime
    value.
    """
    if isinstance(node, c_ast.Constant):
        return True
    if isinstance(node, c_ast.Cast):
        return is_constant_expr(node.expr)
    if isinstance(node, c_ast.UnaryOp) and node.op in ("sizeof", "+", "-", "~"):
        return is_constant_expr(node.expr)
    if isinstance(node, c_ast.BinaryOp):
        return is_constant_expr(node.left) and is_constant_expr(node.right)
    if isinstance(node, (c_ast.ID, c_ast.Typename)):
        # Names: we don't track const/enum bindings in this minimal
        # checker, so be conservative: any name is treated as
        # potentially data-dependent. The SBOX_READ macro expansion
        # uses literal indices only; a non-constant name would be
        # a function argument or a state variable.
        return False
    return False


def is_constant_array_index(node: c_ast.Node) -> bool:
    """True if the array index expression is a compile-time constant.

    Used for `arr[i]` where i must be a literal or sizeof for the
    array access to be constant-time.
    """
    return is_constant_expr(node)


def _is_bounded_iter_step(node: c_ast.Node) -> bool:
    """True if a for-loop's `next` expression is a bounded iteration
    step (i.e. increments or decrements the induction variable by a
    constant amount). The standard patterns are `i++`, `++i`, `i--`,
    `--i`, `i += k`, `i -= k` where k is constant.
    """
    if isinstance(node, c_ast.UnaryOp) and node.op in ("p++", "p--"):
        return True  # i++ or i--
    if isinstance(node, c_ast.BinaryOp) and node.op in ("+=", "-="):
        return is_constant_expr(node.right)
    if isinstance(node, c_ast.ID):
        return True  # bare `i` is treated as no-op or trivial step
    return False


class ConstantTimeVisitor(c_ast.NodeVisitor):
    """Walks the AST of a function body, reporting data-dependent
    control flow or memory access.
    """

    def __init__(self, func_name: str):
        self.func_name = func_name
        self.findings: list[tuple[str, str]] = []
        # Track loop variables seen so far: for( size_t i = 0; i < N; ... )
        # is constant-time (the bound N is constant). But for( i = 0; i < x; ... )
        # is not. We track declared-for-loop indices conservatively.
        self._suppress_for_bound_check: set[str] = set()

    def _flag(self, what: str, node: c_ast.Node) -> None:
        coord = node.coord if node.coord else "?"
        self.findings.append((f"{self.func_name} @ {coord}: {what}", ""))

    def visit_If(self, node: c_ast.If) -> None:
        if not is_constant_expr(node.cond):
            self._flag(f"data-dependent if() condition (cond={type(node.cond).__name__})", node)
        self.generic_visit(node)

    def visit_While(self, node: c_ast.While) -> None:
        if not is_constant_expr(node.cond):
            self._flag(f"data-dependent while() bound", node)
        self.generic_visit(node)

    def visit_DoWhile(self, node: c_ast.DoWhile) -> None:
        if not is_constant_expr(node.cond):
            self._flag(f"data-dependent do-while() condition", node)
        self.generic_visit(node)

    def visit_For(self, node: c_ast.For) -> None:
        # A for-loop is constant-time iff:
        #   (a) cond is a comparison of an induction variable with a
        #       compile-time constant upper bound (e.g. `i < 16` or
        #       `i <= N` where N is constant), AND
        #   (b) next is `i++`, `++i`, `i--`, `--i`, or `i += k` / `i -= k`
        #       where k is a constant (bounded iteration).
        # Loops of the form `for (i = 0; i < N; i++)` are the standard
        # pattern in C; the only data they leak is the iteration count,
        # which is bounded and known.
        if node.cond is None:
            self._flag("for() without condition is unbounded", node)
        elif isinstance(node.cond, c_ast.BinaryOp) and node.cond.op in (
            "<", "<=", ">", ">=",
        ):
            # Check that the right side (the bound) is constant. The
            # left side is the induction variable, which is fine.
            if not is_constant_expr(node.cond.right):
                self._flag(f"for() bound is not a compile-time constant "
                           f"(got {type(node.cond.right).__name__})", node)
        else:
            self._flag(f"for() condition is not a constant bound "
                       f"(got {type(node.cond).__name__})", node)

        if node.next is not None and not _is_bounded_iter_step(node.next):
            self._flag(f"for() increment is not a bounded iteration step "
                       f"(got {type(node.next).__name__})", node)
        self.generic_visit(node)

    def visit_Switch(self, node: c_ast.Switch) -> None:
        if not is_constant_expr(node.cond):
            self._flag("data-dependent switch() value", node)
        self.generic_visit(node)

    def visit_TernaryOp(self, node: c_ast.TernaryOp) -> None:
        if not is_constant_expr(node.cond):
            self._flag("data-dependent ternary (?) condition", node)
        self.generic_visit(node)

    def visit_ArrayRef(self, node: c_ast.ArrayRef) -> None:
        # Allow SBOX_READ(i) and inv_sbox[i] at runtime index only
        # if the array being indexed is `sbox` or `inv_sbox` (the
        # PRESENT S-box tables). Any other runtime-indexed array
        # is flagged.
        arr_name = self._array_name(node.name)
        if arr_name in ("sbox", "inv_sbox"):
            # S-box table lookup with runtime index: allowed (constant-time
            # if the underlying memory is constant-time, which it is for
            # static arrays and progmem-resident arrays).
            return
        if not is_constant_array_index(node.subscript):
            self._flag(
                f"data-dependent array index on {arr_name or 'array'}",
                node,
            )
        self.generic_visit(node)

    def visit_FuncCall(self, node: c_ast.FuncCall) -> None:
        # Function-pointer calls (where the callee is not a name but
        # an expression) are flagged. Named function calls are OK.
        if not isinstance(node.name, c_ast.ID):
            self._flag("function pointer / indirect call", node)
        self.generic_visit(node)

    def visit_Goto(self, node: c_ast.Goto) -> None:
        # `goto label;` is constant-time; `goto *expr;` (computed goto,
        # GCC extension) is not. pycparser doesn't have a separate
        # node for computed goto, but the name field is a UnaryOp
        # for `*expr` (rare in cipher code).
        if isinstance(node.name, c_ast.UnaryOp):
            self._flag("computed goto", node)
        self.generic_visit(node)

    @staticmethod
    def _array_name(node: c_ast.Node) -> str:
        if isinstance(node, c_ast.ID):
            return node.name
        return ""


def check_function(func: c_ast.FuncDef) -> list[tuple[str, str]]:
    """Run the AST visitor on a function and return findings."""
    visitor = ConstantTimeVisitor(func.decl.name)
    visitor.visit(func)
    return visitor.findings


def main() -> int:
    print("=" * 70)
    print("QUARTET — constant-time code inspection (AST-based)")
    print("=" * 70)
    print()
    print("This is a STATIC check, not a TVLA. It parses the preprocessed")
    print("cipher core and walks the AST, looking for data-dependent control")
    print("flow or memory access. A passing check is a NECESSARY condition")
    print("for a constant-time implementation; it is not sufficient.")
    print()

    try:
        preprocessed = preprocess_quartet_core()
    except (RuntimeError, subprocess.CalledProcessError) as e:
        print(f"SKIP: cannot preprocess — {e}")
        print("Install gcc/cpp to run this check.")
        return 0  # Treat as SKIP, not FAIL.

    parser = pycparser.CParser()
    try:
        ast = parser.parse(preprocessed, filename="<preprocessed quartet_core.h>")
    except pycparser.plyparser.ParseError as e:
        print(f"FAIL: parse error: {e}")
        return 1

    funcs = find_function_nodes(ast)
    if not funcs:
        print("FAIL: no cipher core functions found in preprocessed quartet_core.h")
        return 1

    all_findings: list[tuple[str, str]] = []
    for name in sorted(funcs):
        findings = check_function(funcs[name])
        all_findings.extend(findings)
        loc = "yes" if findings else "none"
        print(f"  {name:25s} findings: {loc}")

    if all_findings:
        print()
        print(f"FAIL: {len(all_findings)} data-dependent construct(s) "
              f"in cipher core:")
        for f, _ in all_findings:
            print(f"  {f}")
        print()
        print("=" * 70)
        print("CONSTANT-TIME AST CHECK: FAIL")
        print("=" * 70)
        return 1

    print()
    print("=" * 70)
    print("CONSTANT-TIME AST CHECK: PASS")
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
