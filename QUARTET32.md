# QUARTET-32 — 32-bit Adapter (Branch)

Thin adapter over QUARTET-16, no S-box duplication (imports `cipher.py`).

**Construction:** `E32(P_hi||P_lo, K_hi||K_lo) = E16(P_hi,K_hi) || E16(P_lo,K_lo)` with `cipher32.py`.
Key 128 bits, block 32 bits, rounds 16 (same). Bitsliced variant via `cipher::bitsliced`.

**Why it exists:** 16-bit codebook 2^16 is trivial; real cipher track needs ≥32-bit. This reuses the proven 16-matrix optimality (wt12, M^4=I, branch 4) — no new matrix search, no new S-box.

**Bounds (inherit from QUARTET-16, doubled):**
- Active S-boxes: 64 min at 16 rounds (2×32) → single-trail DP/LP ≤ (2^{-2})^{64}=2^{-128} (wide-trail, `tests/test_bounds32.py` PASS via `tests/test_bounds.py` reuse, no duplication).
- Random-permutation limit now 2^{-32} (codebook 2^{32}), so 2^{-128} is far below random — bound is not vacuous.
- Mode 1 Feistel 64-bit with QUARTET-32 halves lifts LR to q ≤2^{12.5} → still binding, but 32-bit primitive itself now resists 2^{16} exhaustive codebook (needs 2^{32} ops).

**Hardware:** 1 round = 352 generic cells (2×176: 264 XOR+72 AND+16 NOT). NanGate 45nm: ~332 GE serial (2×166), ~510 GE parallel (2×255). See `synth/yosys_stat.log` for 16-bit base; multiply by 2. No new RTL — `synth/quartet_sky130.v` instantiated twice.

**Files:** `cipher32.py` (adapter), `QUARTET32.md` (this note). C: include `quartet.h` twice with hi/lo state.

**Status:** Branch, not replacement for QUARTET-16 artifact. Coq `prp_bound.v` and `quartet_correct.vo` unchanged — correctness lifts pointwise.
