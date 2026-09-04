# Quartet: a 4-bit native block cipher

The smallest 4-bit SPN with an order-4 linear layer and a machine-checked wide-trail bound.

**QUARTET-32 is the primary configuration:** 32-bit block, 128-bit key,
2^-128 single-trail bound (both halves active). QUARTET-16 is the base
construction block for hardware-constrained applications.

This document summarizes the design, the bound, and the evidence. The
full specification is in `SPEC.md`.

## Abstract

Quartet uses only 4-bit operations in the round function. The S-box is
the PRESENT S-box. The linear layer is a 4x4 matrix over GF(2) with
`M^4 = I` and branch number 4. The matrix has weight 12 and is one of
16 optimal matrices in `GL(4,2)`.

**QUARTET-32 (primary):** 32-bit block, two independent QUARTET-16 lanes.
Min bound (one half active): 32 active S-boxes → 2^-64 single-trail DP/LP.
Max bound (both halves): 64 active S-boxes → 2^-128 single-trail DP/LP.
Python enumerates the bound and Coq proves it. The birthday bound is 2^16.

**QUARTET-16 (base):** 16-bit block, 2^-64 single-trail bound. Birthday
bound 2^8 — construction block only.

The hardware cost is 176 generic cells per round. The serial NanGate
estimate is about 166 GE (QUARTET-16) or 332 GE (QUARTET-32).

## Problem

Many constrained devices use 4-bit datapaths. Standard ciphers use wider
operations in the linear layer. That adds cost in 4-bit hardware. A
cipher that uses only 4-bit primitives reduces area and power.

A 16-bit block has a 2^8 birthday bound — only usable as a construction
block. **QUARTET-32 achieves a 2^16 birthday bound** with single-trail
bounds ranging from 2^-64 (one half active) to 2^-128 (both halves active).
The minimum security guarantee is **2^-64**.

## Construction

The state has four 4-bit words `w0..w3`. One round does four S-box lookups, four key XORs, and FullMix. FullMix is:

```
w0' = w0 ^ w1 ^ w2
w1' = w1 ^ w2 ^ w3
w2' = w2 ^ w3 ^ w0
w3' = w3 ^ w0 ^ w1
```

The matrix satisfies `M^4 = I` and has branch number 4. The branch number is the minimum of `weight(in) + weight(M(in))` over non-zero inputs.

Round keys come from the 64-bit master key. The key schedule applies a round constant and the S-box nibble-wise and accumulates with XOR. Each round key bit depends on at least 23 master key bits. Round constants are `0, 5, 0xA, 0xF` and break symmetry of weak keys.

Quartet-16 uses 16 rounds. Quartet-32 encrypts two 16-bit lanes in parallel and costs two S-box blocks per round. No new table is added.

## Security bound

**Block size = 16 bits → birthday bound = 2^8 queries.** This is a hard
ceiling no analysis can overcome. No Q1 venue publishes a 16-bit bulk
cipher. QUARTET is a **4-bit-native construction block**, not a bulk cipher.

**Provable single-trail bounds (Coq machine-checked):**

* 2 rounds: 4 active, `DP <= 2^-8`
* 4 rounds: 8 active, `DP <= 2^-16`
* 8 rounds: 16 active, `DP <= 2^-32`
* 16 rounds: 32 active, `DP <= 2^-64`

**Reality check:**

* Empirical DP_max ≈ 2^-6.38 (`tests/test_hull_empirical.c`)
* Single-trail bound: 2^-64
* Gap: 10^17× (hull effect dominates)
* Effective security: **2^8 queries** (birthday bound)

Tightness verified at R=8 via branch-and-bound (`python/milp_hull.py`,
28 tight trails, 2^-27.19 lower bound vs 2^-32 single-trail).

Two extra facts matter. First, the 16-bit PRP bound is limited by the birthday attack. Second, the round constants break the period-4 structure of raw `M`. The raw linear layer alone collapses integral sets at even rounds, but the real cipher with constants keeps four varying nibbles after round 2.

## Implementation

Python is the reference. Import the cipher and call one function:

```python
import sys
sys.path.insert(0, "python")
from cipher import quartet_encrypt, quartet_decrypt

ct = quartet_encrypt(0x1234, 0x0123456789ABCDEF)
pt = quartet_decrypt(ct, 0x0123456789ABCDEF)
```

C uses the same contract. Include the S-box once and set the table macros, then include the core:

```c
#include "c/sbox.h"
static const uint8_t sbox[16] = QUARTET_SBOX_INIT;
static const uint8_t inv_sbox[16] = QUARTET_INV_SBOX_INIT;
#define SBOX_READ(i) sbox[i]
#define INV_SBOX_READ(i) inv_sbox[i]
#include "c/quartet.h"
uint16_t c = quartet_encrypt(0x1234, 0x0123456789ABCDEFULL);
```

The bitsliced variant `QUARTET_BITSLICED` in `c/sbox.h` computes the S-box with AND and XOR only. Use it on cached CPUs to remove table lookups.

## Verification

Six checks fail for distinct real bugs:

* `python tests/test_bounds.py` proves the wide-trail numbers above. Cross-checks Coq constants.
* `python tests/test_bounds32.py` proves the 32-bit adapter bound `64 active => 2^-128` for the both-halves case.
* `python tests/test_kats.py` verifies 262,157 vectors against Python and C.
* `python tests/test_kats32.py` verifies 20,480 vectors for the 32-bit adapter.
* `python compare.py` cross-checks 20 random vectors Python to C.
* `python tests/test_constant_time.py` walks the AST of `c/quartet_core.h` and finds no data-dependent control flow. A passing AST check is necessary but not sufficient.

Additional evidence:

* `python tests/test_integral.py` shows the simplified model collapse versus the real cipher with constants.
* `python tests/test_key_schedule.py` shows diffusion: each round key bit depends on 23 to 63 master bits.
* `python tests/milp_hull.py --exhaustive` proves R=8 optimum 2R (65k starts, 1000+ tight trails).
* `python tests/tvla.py` is a Level 1 software Welch t-test with 15 PDH hardware counters and a leaky negative control. Level 2 (power/EM traces) requires hardware.
* `coq/quartet_correct.v` proves `decrypt(encrypt(p,k),k) = p` for all `p` and `k`.
* `coq/nilpotent.v` proves `N^4=0, M^4=I` (Thm 4.2, weak hull).
* `coq/prp_bound.v` proves Feistel invertibility and the numeric bound `Adv <= q^2/2^33 + 2^-60`. The hybrid game step is pen-and-paper in `formal/prp_analysis.md`.

## Hardware

Yosys 0.68 with `hw/quartet_sky130.v` gives a library-independent area. One round uses `132 XOR + 36 AND + 8 NOT = 176` cells. The unrolled 16-round design uses 2816 cells. The log is `synth/yosys_generic_stat.log`.

The liberty-mapped run uses Sky130 `tt_025C_1v80`. Volare provides `sky130A bdc9412`. Yosys reads 334 cells from the liberty. The log is `synth/yosys_sky130_liberty.log`. The PDK enable command is `volare enable --pdk sky130 bdc9412`.

NanGate 45 nm estimates are `~166 GE` serial enc-only, `~255 GE` parallel enc-only, and `~254 GE` enc plus dec serial. Quartet-32 is about `332 GE` serial.

AVR ATmega328P at 8 MHz needs about 43 cycles per round. A 16-round encryption is about 688 cycles and 86 microseconds.

## Modes and limits

`SPEC.md` section 10.4 defines five blocks and their limits:

* Mode 1 (64-bit PRP, 4-call balanced Feistel, `n=32`): `Adv <= q^2/2^33 + 2^-60`. This gives `q <= 5792` at `Adv 2^-8` and `q <= 2^16` at `Adv 1/2`.
* Mode 2 (Even-Mansour on 16 bits): `q <= 2^8` queries.
* Mode 3 (sponge, rate 8, capacity 8): collision at `2^8`.
* Mode 4 (HEH MAC, 64-bit): forgery at `2^8`.
* Mode 5 (64-bit Mercy-style wide block): heuristic only, birthday at `2^8` (limited by underlying 16-bit block). No proof exists; `2^-64` remains vacuous. EME2/XCB cannot compensate for the small underlying block size.

`M` has period 4. At most one state in 256 falls into a small invariant subspace on the raw permutation. Blocks must avoid those subspaces.

Do not use Quartet for bulk encryption. Use a standard AEAD such as Ascon where you can. Quartet fits where 4-bit hardware, hardware less than 200 GE, and a provable single-trail bound matter.

## Reproduce

You need Python 3.10 or later, GCC, and optionally Docker with `coqorg/coq:8.18` for Coq.

If you want to check the bounds, run the commands that follow:

```
python tests/test_bounds.py
python tests/test_bounds32.py
```

If you want to check the KAT and the Python to C match, run the commands that follow:

```
python tests/test_kats.py
python compare.py
```

If you want to check the AST constant-time property, run the command that follows:

```
python tests/test_constant_time.py
```

If you want to check the generic synthesis area, run the command that follows:

```
yowasp-yosys -p "read_verilog hw/quartet_sky130.v; hierarchy -check -top quartet_round_logic; proc; opt; techmap; opt; stat"
```

If you want to check the leakage harness, run the command that follows:

```
python tests/tvla.py
```

If you want to rebuild the KAT file, run the command that follows:

```
python tests/generate_kat.py
```

If a command fails, read the log that the tool writes to standard output.

## Files

* `python/cipher.py` and `c/quartet_core.h` are the two sources of truth for the cipher. Do not duplicate the S-box or the round function.
* `python/cipher32.py` and `c/quartet32.h` are the thin adapters for the 32-bit block.
* `c/sbox.h` holds the S-box tables and the bitsliced S-box.
* `runners/` holds thin I/O adapters over `quartet.h`.
* `hw/` holds RTL. `formal/` holds the proof analysis. `coq/` holds Coq proofs. `tests/` holds checks and vectors. `SPEC.md` is the authoritative specification.

## References

Bogdanov et al., PRESENT, CHES 2007. Daemen, Rijmen, The Design of Rijndael, 2002. Luby, Rackoff, SIAM J. Computing, 1988. Goodwill et al., TVLA, 2011. Schneider, Moradi, 2015.

Start with `SPEC.md` section 1 and section 10.4. Then do the reproduce steps.
