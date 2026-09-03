# Quartet: a 4-bit native block cipher

The smallest 4-bit SPN with an order-4 linear layer and a machine-checked wide-trail bound.

Quartet-16 is a 16-bit block, 64-bit key SPN for hardware less than 200 GE. Quartet-32 is a thin 32-bit adapter that reuses the same S-box and FullMix. This document is a short paper that summarizes the design, the bound, and the evidence. The full specification is in `SPEC.md`.

## Abstract

Quartet uses only 4-bit operations in the round function. The S-box is the PRESENT S-box. The linear layer is a 4x4 matrix over GF(2) with `M^4 = I` and branch number 4. The matrix has weight 12 and is one of 16 optimal matrices in `GL(4,2)`.

The wide-trail bound is 32 active S-boxes at 16 rounds. With `DU = 4` this gives a single-trail `DP <= 2^-64` and `LP <= 2^-64`. Python enumerates the bound and Coq proves it. The bound is vacuous for the 16-bit codebook. The meaningful limit is `q << 2^8`.

The hardware cost is 176 generic cells per round. The serial NanGate estimate is about 166 GE. The 32-bit adapter costs about 332 GE.

## Problem

Many constrained devices use 4-bit datapaths. Standard ciphers use wider operations in the linear layer. That adds cost in 4-bit hardware. A cipher that uses only 4-bit primitives reduces area and power.

A 16-bit block is tiny. A single-trail bound of `2^-64` does not give `2^-64` security against a full-codebook adversary. The birthday bound is `2^8` queries and the codebook is `2^16`. We state this vacuity directly and give modes that make the bound useful.

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

The S-box has `DU = 4` and max LAT bias 4. The differential branch number is 4 and the linear branch number is 4. The minimum active counts are:

* 2 rounds: 4 active, `DP <= 2^-8`
* 4 rounds: 8 active, `DP <= 2^-16`
* 8 rounds: 16 active, `DP <= 2^-32`
* 16 rounds: 32 active, `DP <= 2^-64`

The linear side matches. `tests/test_bounds.py` enumerates the `2^16` states. `coq/present_wide_trail.v` proves the same branch numbers and active counts. The result is a single-trail bound. The hull can be larger: `tests/test_hull_empirical.c` measures DP_max ~2^-6.38 (vs 2^-64 single-trail). `python/hull_enum.py` provides the wide-trail bound framework; `python/hull_bound.py` implements the conjectured nilpotent hull bound.

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
* `python tests/tvla.py` is a Level 1 software Welch t-test with PDH hardware counters (processor time, C-states, interrupts) and a leaky negative control. Level 2 (power/EM traces) requires hardware.
* `coq/quartet_correct.v` proves `decrypt(encrypt(p,k),k) = p` for all `p` and `k`.
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
