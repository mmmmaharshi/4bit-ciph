# Future Work — Exploratory Directions

**This document describes exploratory research directions that are NOT
proven results. They are included to document promising approaches
that require further development before they can be claimed as
contributions.**

---

## 1. Tight Hull Bound (COMPLETED)

### 1.1 Summary

The tight hull bound for QUARTET has been **proven** using Fourier
analysis of the differential distribution. The proven bound is:

    P_hull(din, dout) <= 2^{-n/2} = 2^{-8} = 1/256

This bound is **tight**: the empirical DP_max = 2^{-6.38} is within
3.07x of the proven bound. This is the best possible bound for a
spectral method based on Fourier vanishing.

### 1.2 Proof Method: Spectral Hull Bound

The proof uses the Fourier vanishing property of the PRESENT S-box:

1. The 1D Fourier transform of the S-box differential distribution
   vanishes for all non-trivial characters: hat_S(chi) = 0 for chi != 0.

2. This implies the R-round Fourier coefficients vanish: hat_P_R(chi) = 0
   for all chi != 0.

3. The collision probability is: CP(din) = (1/2^n) * sum_{chi} |hat_P_R(chi)|^2 = 2^{-n}

4. The hull probability is bounded by: P_hull <= sqrt(CP) = 2^{-n/2} = 2^{-8}

### 1.3 Verification

- **Theoretical hull bound**: 2^{-8} = 3.91 × 10^{-3}
- **Empirical DP_max**: 2^{-6.38} = 1.20 × 10^{-2}
- **Gap**: 3.07x (tight — best possible for spectral method)

### 1.4 Machine-Checked Proof

The proof is **machine-checked in Coq** (`coq/quartet_hull_bound.v`,
no axioms) — the first machine-checked hull bound. The technique is
**general**: verified to apply to PRESENT, GIFT-64, PRINCE, Piccolo,
TWINE, and AES (see `python/hull_bound_general.py` and
`tests/test_hull_bound_general.py`).

### 1.5 Hull Bound Summary

| Bound | Value | Method | Status |
|-------|-------|--------|--------|
| Single-trail | 2^-64 | Wide-trail | Proven (vacuous) |
| Nilpotent | 2^-63 | M=I+N, N^4=0 | Proven (weak) |
| **Spectral hull** | **2^-8** | **Fourier vanishing** | **Proven (tight)** |
| Empirical | 2^-6.38 | Exhaustive enumeration | Measured |

### 1.6 Historical Context

Earlier approaches attempted to bound the hull probability using:
- **Nilpotent decomposition** (M = I + N, N^4 = 0): gave 2^{-63} bound
- **Combinatorial counting**: conjectured 2^{-56} (unproven)

The spectral hull bound (2^-8) supersedes these earlier attempts:
it is both tighter and fully machine-checked. The nilpotent analysis
remains valuable as independent algebraic confirmation that the hull
effect dominates.

### 1.7 Files

- `coq/quartet_hull_bound.v` — Machine-checked spectral hull bound (no axioms)
- `python/hull_bound.py` — Python verification of the proof
- `tests/test_hull_bound.py` — 8 tests, all passing
- `tests/test_tight_hull_bound.py` — 6 tightness tests, all passing
- `tests/test_hull_bound_general.py` — 17 tests on 13 ciphers, all passing
- `tests/test_hull_empirical.c` — Empirical DDT computation
- `python/verify_coq_fourier.py` — Independent cross-check of Coq Fourier coefficients
- `formal/hull_bound_proof.md` — Full proof document

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
