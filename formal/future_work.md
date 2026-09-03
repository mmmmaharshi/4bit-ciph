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

### 1.3 Prior Attempt (Superseded)

A prior attempt at a nilpotent hull bound used an ad-hoc trail
count factor of 2^{0.5R}, giving a conjectured bound of 2^{-3.5R}
(2^{-56} at R=16). **This was found to be insufficient:**

- Still 2^{49.6}× off from empirical (2^{-56} vs 2^{-6.38})
- The factor 2^{0.5R} has no spectral-radius proof
- A reviewer would correctly identify this as an ad-hoc factor, not a bound

The code for this exploratory attempt has been removed from the main
results. See git history for `python/hull_bound.py` and
`formal/hull_bound_analysis.md` if needed for reference.

### 1.4 What Would Be Needed

A rigorous hull bound would require one of:

1. **Spectral analysis**: Bound the spectral radius of the transition
   operator T where T[Δin][Δout] = sum of probabilities of all
   single-round transitions. The hull probability is related to
   trace(T^R).

2. **Combinatorial counting**: Exploit the M^4 = I periodicity to
   count trails by "nilpotent signature" and prove bounds on the
   number of trails in each weight class.

3. **DDT-weighted wide-trail**: Account for the specific structure
   of PRESENT's DDT (entries are 0, 2, or 4, not uniform) to get
   tighter bounds than the generic (1/4) per active S-box.

### 1.5 Current Status

**The honest position is:**
- Single-trail bound: 2^{-64} (proven, machine-checked in Coq)
- Empirical DP_max: ~2^{-6.38} (measured via exhaustive enumeration)
- Hull bound: **No proven bound exists**

The empirical measurement shows that the hull effect dominates the
differential probability. This is itself a publishable observation:
it demonstrates that single-trail bounds are vacuous for this cipher
and that the actual security is determined by the birthday bound
(2^8 for 16-bit block), not the trail bound.

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
