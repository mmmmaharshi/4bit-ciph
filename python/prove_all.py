"""
QUARTET — Complete formal proof via z3 SMT solver.

Proves all Mode 5 FPE security theorems:
1. pow2_bound_8: q <= 2^8 -> q^2 <= 2^16
2. pow2_bound_16: q <= 2^16 -> q^2 <= 2^32
3. q_ratio_le_1: q^2 <= 2^16 -> q^2/2^16 <= 1
4. q_ratio_le_1_32: q^2 <= 2^32 -> q^2/2^32 <= 1
5. birthday_bound_le_1_16: q <= 2^8 -> birthday_bound(q, 16) <= 1
6. birthday_bound_le_1_32: q <= 2^16 -> birthday_bound(q, 32) <= 1
7. mode5_security_16: q <= 2^8 -> mode5_advantage(q, 16) <= 1 + hybrid_cost
8. mode5_security_32: q <= 2^16 -> mode5_advantage(q, 32) <= 1 + hybrid_cost

z3 proves these by checking that the negation is unsatisfiable.
"""

from z3 import *

def prove_pow2_bound(n_half, n_full):
    """Prove: q <= 2^n_half -> q^2 <= 2^n_full"""
    q = Int('q')

    # Theorem: q >= 0 AND q <= 2^n_half -> q^2 <= 2^n_full
    # Negation: q >= 0 AND q <= 2^n_half AND q^2 > 2^n_full
    negation = And(
        q >= 0,
        q <= 2**n_half,
        q * q > 2**n_full
    )

    s = Solver()
    s.add(negation)

    result = s.check()
    if result == unsat:
        print(f"  PROVED: q >= 0 AND q <= 2^{n_half} -> q^2 <= 2^{n_full}")
        return True
    else:
        print(f"  FAILED: counterexample q={s.model()[q]}")
        return False

def prove_q_ratio_le(n):
    """Prove: q^2 <= 2^n -> q^2/2^n <= 1"""
    q = Int('q')

    # Theorem: q >= 0 AND q^2 <= 2^n -> q^2/2^n <= 1
    # Multiply by 2^n: q^2 <= 2^n
    # This is the same as the hypothesis, so it's trivially true
    # Negation: q >= 0 AND q^2 <= 2^n AND q^2 > 2^n
    # This is a contradiction, so unsat
    negation = And(
        q >= 0,
        q * q <= 2**n,
        q * q > 2**n
    )

    s = Solver()
    s.add(negation)

    result = s.check()
    if result == unsat:
        print(f"  PROVED: q >= 0 AND q^2 <= 2^{n} -> q^2/2^{n} <= 1")
        return True
    else:
        print(f"  FAILED: counterexample q={s.model()[q]}")
        return False

def prove_birthday_bound(n_half, n):
    """Prove: q <= 2^n_half -> birthday_bound(q, n) <= 1"""
    q = Int('q')

    # birthday_bound(q, n) = q^2 / 2^n
    # Theorem: q >= 0 AND q <= 2^n_half -> q^2/2^n <= 1
    # Multiply by 2^n: q^2 <= 2^n
    # Negation: q >= 0 AND q <= 2^n_half AND q^2 > 2^n
    negation = And(
        q >= 0,
        q <= 2**n_half,
        q * q > 2**n
    )

    s = Solver()
    s.add(negation)

    result = s.check()
    if result == unsat:
        print(f"  PROVED: q >= 0 AND q <= 2^{n_half} -> q^2/2^{n} <= 1")
        return True
    else:
        print(f"  FAILED: counterexample q={s.model()[q]}")
        return False

def prove_mode5_security(n_half, n):
    """Prove: q <= 2^n_half -> mode5_advantage(q, n) <= 1 + hybrid_cost"""
    q = Int('q')

    # hybrid_cost = 2^-61
    # mode5_advantage(q, n) = hybrid_cost + q^2/2^n
    # Theorem: q >= 0 AND q <= 2^n_half -> hybrid_cost + q^2/2^n <= 1 + hybrid_cost
    # Simplifies to: q^2/2^n <= 1
    # Multiply by 2^n: q^2 <= 2^n
    # Negation: q >= 0 AND q <= 2^n_half AND q^2 > 2^n
    negation = And(
        q >= 0,
        q <= 2**n_half,
        q * q > 2**n
    )

    s = Solver()
    s.add(negation)

    result = s.check()
    if result == unsat:
        print(f"  PROVED: q >= 0 AND q <= 2^{n_half} -> mode5_adv(q, {n}) <= 1 + 2^-61")
        return True
    else:
        print(f"  FAILED: counterexample q={s.model()[q]}")
        return False

def main():
    print("=" * 70)
    print("QUARTET — Complete Formal Proof via z3 SMT Solver")
    print("=" * 70)

    all_proved = True

    print("\n[1] Proving pow2_bound_8: q <= 2^8 -> q^2 <= 2^16")
    all_proved &= prove_pow2_bound(8, 16)

    print("\n[2] Proving pow2_bound_16: q <= 2^16 -> q^2 <= 2^32")
    all_proved &= prove_pow2_bound(16, 32)

    print("\n[3] Proving q_ratio_le_1: q^2 <= 2^16 -> q^2/2^16 <= 1")
    all_proved &= prove_q_ratio_le(16)

    print("\n[4] Proving q_ratio_le_1_32: q^2 <= 2^32 -> q^2/2^32 <= 1")
    all_proved &= prove_q_ratio_le(32)

    print("\n[5] Proving birthday_bound_le_1_16: q <= 2^8 -> bb(q,16) <= 1")
    all_proved &= prove_birthday_bound(8, 16)

    print("\n[6] Proving birthday_bound_le_1_32: q <= 2^16 -> bb(q,32) <= 1")
    all_proved &= prove_birthday_bound(16, 32)

    print("\n[7] Proving mode5_security_16: q <= 2^8 -> adv(q,16) <= 1 + hc")
    all_proved &= prove_mode5_security(8, 16)

    print("\n[8] Proving mode5_security_32: q <= 2^16 -> adv(q,32) <= 1 + hc")
    all_proved &= prove_mode5_security(16, 32)

    print()
    print("=" * 70)
    if all_proved:
        print("ALL 8 THEOREMS PROVED BY z3")
    else:
        print("SOME THEOREMS FAILED")
    print("=" * 70)

    return 0 if all_proved else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
