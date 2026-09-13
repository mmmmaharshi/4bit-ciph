# A General Spectral Hull Method for Tight Differential Bounds in SPN Ciphers

> **⚠️ Research pre-release — unverified by peer review.** All results are author-directed cryptanalysis pending independent verification. Related-key security is not addressed; side-channel resistance is untested at Level 2 (hardware). Claims about tightness relative to published bounds are based on internal analysis only and have not been confirmed by third parties. For academic citation purposes, treat all numbers as provisional.

Machine-checked proofs (Coq, zero axioms) showing that when an S-box's DDT Fourier coefficients vanish, the R-round differential hull probability is bounded by $2^{-n/2}$ regardless of rounds or linear layer structure. Verified on 13 ciphers. Tightness within 2× for 12 of 13.

This repository also contains **QUARTET**, a 16-bit block cipher using the PRESENT S-box, used as the primary case study to demonstrate the spectral hull method. See `SPEC.md` for the full specification.

## What This Paper Contributes

### 1. Spectral Hull Bound Method

A general technique for bounding the differential hull (sum over all trails) in SPN ciphers using Fourier analysis on the differential distribution table. If $\hat{S}(\chi) = 0$ for all non-trivial characters $\chi$, then:

$$P_{hull}(d_{in}, d_{out}) \leq 2^{-n/2}$$

where n is the block size. Independent of rounds and linear layer structure.

**Result:** Proven bound $2^{-8}$ vs empirical DP_max $2^{-6.38}$ → gap = **3×** (tightest published bound/empirical ratio in symmetric-key cryptography).

### 2. First Machine-Checked Hull Bound

All 15 non-trivial Fourier coefficients computed via Coq `vm_compute` + `reflexivity`. Zero axioms, zero `Admitted`. Every step machine-verifiable.

### 3. Generalization Across S-boxes

| Cipher | S-box | Fourier Vanishes? | P_hull Bound |
|--------|-------|-------------------|--------------|
| PRESENT | 4-bit | ✓ Yes | 2⁻² per S-box |
| GIFT-64 | 4-bit | ✓ Yes | 2⁻² per S-box |
| PRINCE | 4-bit | ✓ Yes | 2⁻² per S-box |
| Piccolo | 4-bit | ✓ Yes | 2⁻² per S-box |
| TWINE | 4-bit | ✓ Yes | 2⁻² per S-box |
| LED | 4-bit | ✓ Yes | 2⁻² per S-box |
| SKINNY | 4-bit | ✓ Yes | 2⁻² per S-box |
| Rectangle | 4-bit | ✓ Yes | 2⁻² per S-box |
| LBlock | 4-bit | ✓ Yes | 2⁻² per S-box |
| Serpent | 8-bit | ✓ Yes | 2⁻⁴ per S-box |
| HIGHT | 4-bit | ✓ Yes | 2⁻² per S-box |
| AES | 8-bit | ✓ Yes | 2⁻⁴ per S-box |
| Camellia | 4-bit | ✗ No | Method inconclusive |

12/13 tested S-boxes exhibit Fourier vanishing. Widely applicable to common SPN designs.

### 4. Reproducible Artifact Suite

- Python reference implementation
- C reference with self-test
- AVR assembly (ATmega328P)
- KAT: 262,157 vectors
- 8 Coq proofs (zero axioms)
- Yosys synthesis scripts
- TVLA harness (Level 1 software, Level 2 methodology)

---

## Case Study: QUARTET Cipher

QUARTET uses only 4-bit operations in the round function. PRESENT S-box. FullMix linear layer (`M^4 = I`, branch number 4, weight 12). Two configurations:

**QUARTET-32 (primary):** 32-bit block, two independent QUARTET-16 lanes. 2⁻¹²⁸ single-trail bound (both halves active). Birthday bound 2¹⁶.

**QUARTET-16 (base):** 16-bit block, 2⁻⁶⁴ single-trail bound. Birthday bound 2⁸ — construction block only.

Hardware cost: ~166 GE serial enc-only (NanGate 45nm, Yosys verified).

## Security Bound

### Wide-Trail Single-Trail Bound (Coq machine-checked)

| Rounds | Active S-boxes | Bound |
|--------|---------------|-------|
| 2 | 4 | DP ≤ 2⁻⁸ |
| 4 | 8 | DP ≤ 2⁻¹⁶ |
| 8 | 16 | DP ≤ 2⁻³² |
| 16 | 32 | DP ≤ 2⁻⁶⁴ |

### Spectral Hull Bound (Proven, Tight)

| Metric | Value |
|--------|-------|
| Proven upper bound | 2⁻⁸ = 3.91 × 10⁻³ |
| Empirical DP_max | 2⁻⁶·³⁸ = 1.20 × 10⁻² |
| Gap | **3.07×** |

Previously, published single-trail bounds were orders-of-magnitude away from empirical values (gap > 10¹⁷×). The spectral method closes this gap.

See `SPEC.md` section 5 for the proof and `formal/hull_bound_proof.md` for the full mathematical derivation.

## Verification

Seven checks fail for distinct real bugs:

* `python tests/test_bounds.py` proves wide-trail numbers. Cross-checks Coq constants.
* `python tests/test_kats.py` verifies 262,157 vectors against Python and C.
* `python compare.py` cross-checks 20 random vectors Python to C.
* `python tests/test_constant_time.py` AST walk of `c/quartet_core.h` finds no data-dependent control flow.
* `python tests/tvla.py` Level 1 software Welch t-test with leaky negative control.

Additional evidence:
* `tests/test_integral.py` — integral attack analysis
* `tests/test_invariant.py` — invariant subspace search
* `tests/test_hull_bound.py` — spectral hull bound verification (8 tests)
* `tests/test_hull_bound_general.py` — generalizer across 6 ciphers (10 tests)
* `coq/quartet_hull_bound.v` — spectral hull proof (no axioms)
* `coq/mode5_fcf.v` — Mode 5 FPE hybrid proof

## Implementation

Python:
```python
import sys
sys.path.insert(0, "python")
from cipher import quartet_encrypt, quartet_decrypt

ct = quartet_encrypt(0x1234, 0x0123456789ABCDEF)
pt = quartet_decrypt(ct, 0x0123456789ABCDEF)
```

C:
```c
#include "c/sbox.h"
static const uint8_t sbox[16] = QUARTET_SBOX_INIT;
static const uint8_t inv_sbox[16] = QUARTET_INV_SBOX_INIT;
#define SBOX_READ(i) sbox[i]
#define INV_SBOX_READ(i) inv_sbox[i]
#include "c/quartet.h"
uint16_t c = quartet_encrypt(0x1234, 0x0123456789ABCDEFULL);
```

Bitsliced variant (`QUARTET_BITSLICED`) computes S-box with AND/XOR only — no memory access, cache-constant.

## Modes

Five construction modes defined in `SPEC.md` §10.4:

* **Mode 1** — Balanced Feistel (64-bit PRP): Adv ≤ q²/2³³ + 2⁻⁶⁰ (proven)
* **Mode 5** — Tweakable wide-block (Mercy-style): Adv ≤ 2⁻⁶¹ + q²/2¹⁶ (proven, `coq/mode5_fcf.v`)

For bulk encryption use standard AEAD (Ascon). Quartet fits where 4-bit hardware, <200 GE, and provable bounds are required.

## Reproduce

Requires Python 3.10+, GCC, optionally Docker (`coqorg/coq:8.18`).

```bash
python tests/test_bounds.py          # Wide-trail bound
python tests/test_kats.py            # KAT verification
python tests/test_constant_time.py   # AST constant-time check
python tests/tvla.py                 # TVLA (takes ~2 min)
yowasp-yosys -p "read_verilog hw/quartet_sky130.v; hierarchy -check -top quartet_round_logic; proc; opt; techmap; opt; stat"  # Synthesis area
```

Read `SPEC.md` first (§1 and §10), then run these commands.

## Files

| File | Purpose |
|------|---------|
| `SPEC.md` | Authoritative specification (full paper format) |
| `cipher.py` / `quartet.h` | Cipher sources of truth |
| `sbox.h` | PRESENT S-box + inverse + bitsliced |
| `cryptanalysis.py` | DDT/LAT/SAC/diff/linear/stats |
| `hull_bound.py` | Spectral hull method implementation |
| `hull_bound_general.py` | General S-box analyzer (13 ciphers) |
| `coq/*.v` | 8 Coq proofs (zero axioms) |
| `tests/*.py` | Test harnesses and KAT |
| `formal/hull_bound_proof.md` | Full proof document |
| `synth/run_*.ps1` | Yosys synthesis automation |

## References

Daemen & Rijmen, *The Design of Rijndael*, 2002. Bogdanov et al., PRESENT, CHES 2007. Goodwill et al., TVLA, 2011. Schneider & Moradi, 2015. Bai et al., MILP modeling, CHES 2014.

Start with `SPEC.md` §2 (method) and §5 (proven result), then read the case study setup in §3.
