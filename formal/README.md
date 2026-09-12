# Formal Proofs

Machine-checked proofs and mathematical derivations supporting the spectral hull bound method. QUARTET serves as the primary case study demonstrating the general technique.

## Spectral Hull Method (Primary Contribution)

| File | Content |
|------|---------|
| `hull_bound_proof.md` | General theorem: P_hull ≤ 2^{-n/2} for S-boxes with Fourier vanishing |
| `tightness_proof.md` | Lower bound proof: gap < 2× between upper and empirical bounds |
| `present_hull_bound.md` | Application to PRESENT: first ISO-standardized cipher with proven hull bound |

## Coq Proofs (Zero Axioms, Coq 8.18)

- `coq/quartet_hull_bound.v` — Spectral hull bound (no axioms)
- `coq/present_wide_trail.v` — PRESENT wide-trail bound (DU = 4, first machine-checked)
- `coq/prp_bound.v` — Mode 1 Feistel + Mode 5 FPE security
- `coq/mode5_fcf.v` — Mode 5 hybrid game hop proof (FCF library)
- `coq/nilpotent.v` — Linear layer algebraic structure (M = I+N, N⁴=0)
- `coq/quartet_correct.v` — Roundtrip correctness (decrypt(enc(p,k),k)=p)
- `coq/quartet_sprp.v` — Single-query SPRP advantage ≤ 2⁻⁶⁴

## Construction Modes (QUARTET as Building Block)

| File | Content |
|------|---------|
| `mode5_proof_complete.md` | Mode 5 FPE security proof (Mercy-style wide-block) |
| `prp_analysis.md` | Mode 1 Feistel security analysis (Luby-Rackoff PRP bound) |

## Future Work

| File | Content |
|------|---------|
| `future_work.md` | Open directions (related-key model, L2 TVLA hardware, Camellia boundary condition, independent cryptanalysis) |
