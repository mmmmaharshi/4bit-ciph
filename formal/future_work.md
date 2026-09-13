# Future Work — Exploratory Directions

**This document describes exploratory research directions that are NOT proven results. They are included to document promising approaches that require further development.**

---

## 1. Tight Hull Bound (COMPLETED)

The spectral hull method provides a computable upper bound on hull accumulation when S-boxes exhibit Fourier vanishing. Applied to 13 ciphers with 12/13 showing provable bounds via machine-checked Fourier verification. See `formal/hull_bound_proof.md` and `formal/tightness_proof.md`.

| Bound | Value | Method | Status |
|-------|-------|--------|--------|
| Single-trail | 2⁻⁶⁴ | Wide-trail | Proven (vacuous at small block sizes) |
| Nilpotent | 2⁻⁶³ | M = I + N, N⁴ = 0 | Proven (weak algebraic confirmation) |
| **Spectral hull** | **2⁻⁸** | **Fourier vanishing** | **Proven (tight, < 2× gap)** |
| Empirical | 2⁻⁶·³⁸ | Exhaustive enumeration | Measured |

---

## 2. Related-Key Security (Open)

The QUARTET key schedule is designed to resist slide and trivial related-key attacks (non-periodic, full-key-dependent). However:

- No quantitative query-bound exists in a formal related-key model
- Standard lightweight ciphers (GIFT, Piccolo) have had related-key distinctions published; this cipher has none yet
- A rigorous FKDM/FKAM analysis would strengthen the paper's position

**Status:** Design rationale provided; formal model left as future work.

---

## 3. Side-Channel L2 Proof (Requires Hardware)

Level 1 TVLA (`tests/tvla.py`) validates methodology via negative controls. Level 2 hardware traces are required for Q1-side-channel contributions:

| Requirement | Status | Needed For |
|-------------|--------|------------|
| Oscilloscope / ChipWhisperer | NOT acquired | Power trace capture |
| Shunt resistor + wiring | NOT acquired | Power measurement |
| FPGA target board | NOT acquired | Hardware implementation |
| 1M+ power traces | NOT captured | Q1 publication |
| CPA analysis | NOT performed | Key recovery resistance |

The L1 harness in `tests/tvla_l2_harness.py` provides methodology structure ported to hardware traces. Physical lab setup required.

---

## 4. Camellia S-box Analysis (FORMALLY RESOLVED)

The spectral hull method fails on Camellia-s1 (max Fourier coefficient = 0.002197 ≠ 0). This has been **formally verified in Coq**:

- Machine-checked proof: `coq/camellia_negative_case.v` — computes F(6) = 100 via exhaustive 256×256 DDT enumeration, proves F(6) ≠ 0, derives contradiction with hypothetical Fourier vanishing. Zero axioms.
- Structural analysis: `formal/camellia_failure_analysis.md` — explains why composite-field construction breaks Fourier vanishing (no rational function identity over GF(2ⁿ) analogous to field inversion symmetry).
- Python empirical verification: `tests/test_hull_bound_general.py::test_camellia_fails_vanishing` — confirms max |coeff| ≈ 0.002197 for 8-bit Camellia-s1.

Remaining open questions:
- Can the bound be adapted for non-vanishing S-boxes (bounded-error Fourier approach)?
- Does the method extend to non-bijective S-boxes (AES S-box is bijective, but many lightweight designs use approximations)?
- What structural feature of composite-field constructions exactly breaks Fourier vanishing? Can this be characterized algebraically?

**Status:** Negative case formally proven. The Camellia boundary condition is no longer "open" — it is a certified disproof. Remaining work is on generalized bounds for non-vanishing S-boxes.

---

## 5. Independent Cryptanalysis (Open)

All cryptanalysis so far is author-directed. A third-party attack survey would strengthen submission:

- Expanded MILP hull enumeration (Bai et al., CHES 2014 style) for additional rounds
- Algebraic distinguishing attacks
- Cube attacks on the key schedule
- Impossible-differential search over R ≤ 8 rounds

**Status:** Pending external review. The artifact suite (Coq proofs, Python reference, C reference, KAT vectors) supports independent verification.

---

## 6. Higher-Round Spectral Bounds (Open)

At high round counts (R ≥ 16), the single-trail bound typically dominates the spectral bound for large-block ciphers. Interesting open problem:

- Can the spectral method be combined with MILP single-trail enumeration to produce *both* upper bounds simultaneously?
- Does a hybrid "spectral-MILP" framework improve bounds in intermediate regimes?

**Status:** Conceptual. Would require extensions to both methods.

---

*Document generated 2026-09-03. Items marked "COMPLETED" are verified; remaining items require further development before claiming contribution.*
