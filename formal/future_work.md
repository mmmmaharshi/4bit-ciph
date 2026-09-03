# Future Work — Exploratory Directions

**This document describes exploratory research directions that are NOT
proven results. They are included to document promising approaches
that require further development before they can be claimed as
contributions.**

---

## 1. Nilpotent Hull Bound (Exploratory)

### 1.1 Motivation

The QUARTET cipher has a significant gap between:
- **Proven single-trail bound**: 2^{-64} at R=16 (wide-trail, machine-checked)
- **Empirical actual DP_max**: ~2^{-6.38} (from exhaustive 2^32-pair enumeration)

This 10^{17}× gap means the proven bound is vacuous for the actual
cipher behavior. A hull bound (summing probabilities over all trails
sharing the same input/output difference) would bridge this gap.

### 1.2 Approach: Nilpotent Decomposition

QUARTET's FullMix matrix satisfies M^4 = I (order exactly 4). Over
GF(2), this gives a nilpotent decomposition:

- M = I + N where N is nilpotent
- N^4 = 0 and N^2 ≠ 0 (verified algebraically)
- M^r = (I + N)^r can be computed via binomial theorem in GF(2)

This nilpotent structure creates periodic trail patterns (period 4)
that could potentially be analytically counted.

### 1.3 Why a Hull Bound is Hard

Computational attempts to bound the hull probability ran into
fundamental obstacles:

1. **State space explosion**: The transition operator T is 65536×65536.
   After several rounds, probability mass spreads across too many
   states for exact computation.

2. **Pruning loses accuracy**: Aggressive pruning (keeping only top-K
   states) loses the true maximum because probability concentrates
   in ways that are hard to predict.

3. **Spectral radius is 1**: T is stochastic (rows sum to 1), so
   ρ(T) = 1, which gives no useful bound on ||T^R||.

4. **No clean combinatorial structure**: The interaction between the
   PRESENT DDT and FullMix does not factor nicely.

A prior attempt using an ad-hoc factor 2^{0.5R} gave 2^{-56} at R=16,
which was still 2^{49.6}× off from empirical (2^{-6.38}) and had no
proof. **This was removed from the main results.**

### 1.4 Current Status (Updated 2026-09-04)

**Proven:**
- Single-trail bound: 2^{-64} at R=16 (machine-checked `coq/present_wide_trail.v`, `tests/test_bounds.py`)
- R=8 optimum: 2R=16 active proven optimal via exhaustive branch-and-bound over 65535 starts (`python/milp_hull.py --exhaustive`, `tests/test_milp_opt.py`, 28 tight trails, lower hull 2^-27.19)
- Algebraic nilpotent part: M=I+N, N^4=0, M^4=I (`coq/nilpotent.v` by vm_compute) → proven weak hull upper bound 2·2^{-4R} (2^-63 at R16, 2^-31 at R8)

**Measured:**
- Empirical DP_max: ~2^{-6.38} (exhaustive 2^32-pair enumeration, `tests/test_hull_empirical.c`)

**Not yet proven:**
- Tight hull upper bound matching empirical (gap 2^{-63} vs 2^{-6.38} still ~57×2). Conjectured 2^{-56} remains exploratory.

**Publishable observation:** R=8 optimum proven + algebraic N^4=0 lifts Lane A to Lane B-lite: hull dominates, birthday 2^8 remains real limit, but wide-trail is now tight+optimal, not just lower-bounded.

---

## 2. Level 2 TVLA (Exploratory)

### 2.1 Motivation

The current TVLA implementation (`tests/tvla.py`) is Level 1 only:
software counters (psutil, wall clock) that measure OS-level
micro-architectural noise, not actual algorithmic leakage.

### 2.2 What Would Be Needed

For Q1 SCA (side-channel analysis), Level 2 is required:

| Requirement | Status | Why |
|-------------|--------|-----|
| Power trace capture | NOT available | Requires oscilloscope + shunt resistor |
| EM trace capture | NOT available | Requires EM probe + amplifier |
| PMU hardware counters | NOT available | Requires ETW kernel tracing (admin) or Linux perf |

### 2.3 Current Status

The Level 1 TVLA correctly:
- Validates the methodology (negative controls caught)
- Shows no algorithmic leakage at the trace counts run
- Identifies micro-architectural variation (correctly labeled as informational)

For Q1 SCA, hardware measurement equipment is required. The
methodology in `tests/tvla.py` is designed to be ported to hardware
traces without code changes.

---

*Document generated 2026-09-03. This file documents exploratory
directions, not proven results.*
