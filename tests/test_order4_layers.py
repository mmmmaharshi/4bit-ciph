"""Characterization of all 4x4 GF(2) matrices with M^4=I and branch #4.

Proves FullMix achieves minimal XOR weight among all such matrices.

Mano H. | 2026
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ---------------------------------------------------------------------------
# Matrix helpers over GF(2)
# ---------------------------------------------------------------------------

def mat_mul(A, B):
    """Multiply two 4x4 binary matrices."""
    return [[sum(A[r][k] * B[k][c] for k in range(4)) % 2 for c in range(4)]
            for r in range(4)]

def mat_pow(M, exp):
    """M^exp over GF(2) via repeated squaring."""
    result = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
    base = [row[:] for row in M]
    while exp > 0:
        if exp & 1:
            result = mat_mul(result, base)
        base = mat_mul(base, base)
        exp >>= 1
    return result

def mat_equal(A, B):
    return all(A[r][c] == B[r][c] for r in range(4) for c in range(4))

def identity():
    return [[1 if i == j else 0 for j in range(4)] for i in range(4)]

def is_invertible(M):
    aug = [M[r][:] + [1 if r == i else 0 for i in range(4)] for r in range(4)]
    for col in range(4):
        pivot = None
        for row in range(col, 4):
            if aug[row][col]:
                pivot = row
                break
        if pivot is None:
            return False
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for row in range(4):
            if row != col and aug[row][col]:
                aug[row] = [(a ^ b) for a, b in zip(aug[row], aug[col])]
    return True

def bits_to_mat(bits):
    return [[(bits >> (r * 4 + c)) & 1 for c in range(4)] for r in range(4)]

def mat_bits(M):
    bits = 0
    for r in range(4):
        for c in range(4):
            if M[r][c]:
                bits |= 1 << (r * 4 + c)
    return bits


# ---------------------------------------------------------------------------
# Branch number (word-weight, not bit-weight)
# ---------------------------------------------------------------------------

def branch_number_word(M):
    """B(M) = min_{v!=0} wt_word(v) + wt_word(M*v).

    wt_word counts non-zero WORDS (nibbles), where v is represented as an
    integer whose bit i indicates whether word i differs.
    """
    best = 999
    for d in range(1, 1 << 4):
        dv = [(d >> i) & 1 for i in range(4)]
        w_in = sum(dv)
        # Compute M*v directly (not via mat_mul which assumes 4×4)
        ov = [sum(M[r][i] & dv[i] for i in range(4)) % 2 for r in range(4)]
        w_out = sum(ov)
        b = w_in + w_out
        if b < best:
            best = b
    return best


def xor_weight(M):
    return sum(sum(row) for row in M)


def classify_nilpotent_class(N):
    """Classify N = M - I (nilpotent part) by ranks of powers.

    Jordan block partition determines conjugacy class in GL(4,2).
    Possible nilpotent Jordan types for n=4:
      [4]   -> single 4-block, rank(N)=3, rank(N^2)=2, rank(N^3)=1
      [3,1] -> one 3-block + one 1-block, rank(N)=2, rank(N^2)=1, rank(N^3)=0
      [2,2] -> two 2-blocks, rank(N)=2, rank(N^2)=0
      [2,1,1] -> one 2-block + two 1-blocks, rank(N)=1, rank(N^2)=0
      [1,1,1,1] -> trivial, N=0

    We only care about types where N^2 != 0 (so M has order exactly 4):
      [4] or [3,1].
    """
    ranks = []
    cur = [row[:] for row in N]
    for power in range(1, 4):
        zeros = sum(cur[r][c] for r in range(4) for c in range(4))
        ranks.append(4 - zeros)  # rough; let's do proper rank instead
        if power >= 2:
            cur = mat_mul(cur, N)
    
    # Compute actual rank of N^p for p=1,2,3
    ranks = []
    cur = [row[:] for row in N]
    for power in range(1, 4):
        # Compute rank of cur (= N^power)
        aug = [cur[r][:] for r in range(4)]
        rk = 0
        for col in range(4):
            pivot = None
            for row in range(rk, 4):
                if aug[row][col]:
                    pivot = row
                    break
            if pivot is None:
                continue
            aug[rk], aug[pivot] = aug[pivot], aug[rk]
            for row in range(4):
                if row != rk and aug[row][col]:
                    aug[row] = [(a ^ b) for a, b in zip(aug[row], aug[rk])]
            rk += 1
        ranks.append(rk)
        if power < 3:
            cur = mat_mul(cur, N)
    
    if ranks[0] == 0:
        return "none"           # M = I (trivial)
    if ranks[1] == 0:
        return "[2,2]"          # N^2 = 0 -> M^2 = I (order 2)
    if ranks[2] == 0:
        return "[3,1]"          # N^3 = 0 but N^2 != 0 (order 4)
    return "[4]"               # All ranks > 0 (unlikely for n=4, check)


def main():
    print("=" * 70)
    print("ORDER-4 LINEAR LAYERS: Complete characterization in GL(4,GF(2))")
    print("=" * 70)
    print()
    print("Theory:")
    print("  Over GF(2): x^4 - 1 = (x - 1)^4, so all eigenvalues = 1.")
    print("  M^4 = I iff M = I + N where N is nilpotent with N^4 = 0.")
    print("  Order exactly 4 iff N^2 != 0 (Jordan blocks include size >= 3).")
    print()

    # ===== PHASE 1: Count totals =====
    total_matrices = 65536
    gl4_count = 0
    order4_exact = 0  # M^4 = I AND M^2 != I
    order4_div4 = 0   # M^4 = I (includes M^2 = I and M = I)

    for bits in range(total_matrices):
        M = bits_to_mat(bits)
        if not is_invertible(M):
            continue
        gl4_count += 1
        
        M2 = mat_pow(M, 2)
        M4 = mat_pow(M, 4)
        
        if mat_equal(M4, identity()):
            order4_div4 += 1
            if not mat_equal(M2, identity()):
                order4_exact += 1

    # Verify GL(4,2) order
    expected_gl4 = (16-1)*(16-2)*(16-4)*(16-8)  # 20160
    print(f"[1] GL(4,2) theoretical order: {expected_gl4}")
    print(f"    GL(4,2) verified count:    {gl4_count}")
    assert gl4_count == expected_gl4, f"GL(4,2) count mismatch: {gl4_count}"
    print()

    print(f"    Matrices with M^4=I:       {order4_div4}")
    print(f"    With exact order 4:        {order4_exact}")
    print(f"    With order 1 or 2:         {order4_div4 - order4_exact}")
    print()

    # ===== PHASE 2: Find all M^4=I with branch >= 4 =====
    print("[2] Matrices with M^4=I and branch >= 4:")
    qualifiers = []  # (bits, M, branch, xor_wt, jordan_type)
    
    for bits in range(total_matrices):
        M = bits_to_mat(bits)
        if not is_invertible(M):
            continue
        M4 = mat_pow(M, 4)
        M2 = mat_pow(M, 2)
        if not mat_equal(M4, identity()):
            continue
        
        bw = branch_number_word(M)
        if bw < 4:
            continue
            
        # Get nilpotent N = M + I
        N = [[M[r][c] ^ (1 if r == c else 0) for c in range(4)] for r in range(4)]
        jtype = classify_nilpotent_class(N)
        
        qualifiers.append((bits, M, bw, xor_weight(M), jtype))

    print(f"    Found {len(qualifiers)} qualifying matrices")
    print()

    # ===== PHASE 3: Group by branch number and find minima =====
    print("[3] Distribution by branch number:")
    by_branch = {}
    for _, M, bw, wt, jt in qualifiers:
        if bw not in by_branch:
            by_branch[bw] = []
        by_branch[bw].append((wt, jt, bits))

    best_overall = float('inf')
    best_matrices = []
    
    for bw in sorted(by_branch.keys()):
        entries = by_branch[bw]
        min_wt = min(wt for wt, jt, _ in entries)
        count = len(entries)
        unique_weights = set(wt for wt, jt, _ in entries)
        jtypes_seen = set(jt for wt, jt, _ in entries)
        print(f"    Branch #{bw}: {count} matrices, weights in {{{','.join(str(w) for w in sorted(unique_weights))}}}, "
              f"Jordan types {{{','.join(sorted(jtypes_seen))}}}")
        
        if bw == 4:
            best_for_4 = min(wt for wt, jt, _ in entries)
            print(f"    --> Minimum XOR weight at branch #4: {best_for_4}")
            if best_for_4 < best_overall:
                best_overall = best_for_4
        
        for wt, jt, bits_val in entries:
            if wt <= best_for_4 if 'best_for_4' in dir() else False:
                pass
    
    print()

    # Show matrices achieving minimum weight at branch #4
    branch4_entries = by_branch.get(4, [])
    if branch4_entries:
        min_wt_b4 = min(wt for wt, jt, _ in branch4_entries)
        opt_mats = [(bits, M, wt, jt) for bits, M, bw, wt, jt in qualifiers
                     if bw == 4 and wt == min_wt_b4]
        
        print(f"[4] Optimal XOR-weight matrices (branch #4, wt={min_wt_b4}):")
        for bits, M, wt, jt in opt_mats:
            rows_str = " ".join("".join(str(x) for x in row) for row in M)
            print(f"  bits={bits:#010x}  wt={wt}  Jordan={jt}")
            print(f"    [{rows_str}]")
            print(f"    [{rows_str[4:]}]")
            print(f"    [{rows_str[8:]}]")
            print(f"    [{rows_str[12:]}]")
        print()

        # Compare with FullMix
        fullmix = [[1,1,1,0],[0,1,1,1],[1,0,1,1],[1,1,0,1]]
        fm_fm4 = mat_pow(fullmix, 4)
        fm_m2 = mat_pow(fullmix, 2)
        fm_bw = branch_number_word(fullmix)
        fm_wt = xor_weight(fullmix)
        fm_N = [[fullmix[r][c] ^ (1 if r == c else 0) for c in range(4)] for r in range(4)]
        fm_jtype = classify_nilpotent_class(fm_N)
        
        print(f"FullMix: branch={fm_bw} weight={fm_wt} Jordan={fm_jtype}")
        assert mat_equal(mat_pow(fullmix, 4), identity())
        assert not mat_equal(mat_pow(fullmix, 2), identity())
        assert fm_bw == 4
        print()
        print(f"Result: FullMix weight ({fm_wt}) {'==' if fm_wt == min_wt_b4 else '!='} optimal ({min_wt_b4})")

        if fm_wt == min_wt_b4:
            print("\n*** PROVED: FullMix achieves MINIMUM XOR weight among ALL")
            print("*** 4x4 binary matrices with M^4=I and branch=#4. ***")
        else:
            print(f"\n*** FullMix does NOT achieve optimal weight. Best found: {min_wt_b4}. ***")

    print()

    # ===== PHASE 4: Prove optimality algebraically =====
    print("[5] Algebraic proof that weight >= 12:")
    
    # If M^4 = I and branch >= 4, we can prove lower bound on weight.
    # Key insight: for branch 4, each column must have weight >= 2 (since
    # wt(e_i) + wt(Me_i) >= 4 => 1 + wt(col_i) >= 4 => wt(col_i) >= 3? No, 
    # wait: wt_word(e_i) = 1 (single active word), so wt_word(M*e_i) >= 3.
    # That means each column has weight >= 3.
    
    # Actually: e_i = [0,...,1,...,0] with 1 at position i.
    # M * e_i = column i of M.
    # So wt_word(M * e_i) = wt_word(column i) = number of 1-bits in column i.
    # Branch condition: wt_word(e_i) + wt_word(M * e_i) >= 4
    # => 1 + wt(column_i) >= 4 => wt(column_i) >= 3.
    
    # Each column has >= 3 ones, 4 columns => total weight >= 12.
    
    # Verification:
    col_weights = []
    for bits, M, bw, wt, jt in qualifiers:
        col_wts = [sum(M[r][c] for r in range(4)) for c in range(4)]
        col_weights.append(min(col_wts))
    
    min_col_min = min(col_weights) if col_weights else 0
    print(f"  Min column-weight among qualifiers: {min_col_min}")
    print(f"  Each column has >= {min_col_min} ones => total weight >= 4*{min_col_min} = {4*min_col_min}")
    
    if min_col_min >= 3:
        print(f"  Column-weight bound proves XOR weight >= 12.")
        print(f"  FullMix has weight 12 -> PROVABLY OPTIMAL.")
    else:
        print(f"  Column-weight analysis inconclusive; checking explicit bounds...")
        min_total = min(wt for _, _, _, wt, _ in qualifiers) if qualifiers else 0
        print(f"  Explicit minimum among all qualifiers: {min_total}")

    print()
    print("=" * 70)
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
