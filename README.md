# QUARTET — 4-bit Native Block Cipher

[![KAT 262k](https://img.shields.io/badge/KAT-262157%20PASS-brightgreen)](tests/vectors/quartet_kat.txt)
[![KAT32 20k](https://img.shields.io/badge/KAT32-20480%20PASS-brightgreen)](tests/vectors/quartet32_kat.txt)
[![Coq 8.18](https://img.shields.io/badge/Coq-quartets_correct.vo%20%7C%20prp_bound.vo-blue)](formal/README.md)
[![Yosys 0.68](https://img.shields.io/badge/Yosys-176%20cells%2Fround-lightgrey)](hw/quartet_sky130.v)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](python/cipher.py)

> The smallest 4-bit SPN with an order-4 linear layer and a machine-checked wide-trail bound.

`QUARTET-16` is a 16-bit block, 64-bit key SPN for <200 GE hardware. `QUARTET-32` is a thin 32-bit adapter that reuses the same S-box and FullMix. Both share one source of truth.

> [!NOTE]
> This is a construction block for constrained modes, not a drop-in for AES bulk encryption. See `SPEC.md` §1 and §10.4.

## Table of contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Usage](#usage)
- [Project structure](#project-structure)
- [Verification](#verification)
- [Security at a glance](#security-at-a-glance)
- [Hardware and formal proofs](#hardware-and-formal-proofs)
- [Modes](#modes)

## Features

- 4-bit native round: PRESENT S-box, FullMix 4×4 over GF(2) with `M⁴=I` and branch number 4.
- Provable wide-trail bound: 32 active S-boxes at 16 rounds gives `DP/LP ≤ 2⁻⁶⁴`.
- Exhaustive optimality proof: 16 matrices meet `M⁴=I` and `B=4` with weight 12. FullMix is optimal.
- Two tracks from one code base: `QUARTET-16` artifact and `QUARTET-32` adapter (`2×16`, `332 GE` serial).
- Reproducible checks: 262157-vector KAT, 20-vector Py↔C cross-check, yosys stat, Coq 3 MB proof.

## Prerequisites

Make sure that you have the tools that follow:

- Python 3.10 or later (stdlib only, no extra packages).
- GCC with C11 support for the C reference.
- `coqorg/coq:8.18` for the Coq proofs (Docker or WSL).
- `yowasp-yosys 0.68` for the generic synth check.

## Quick start

Do the steps that follow to run the quick check:

1. Clone the repo and enter the directory.
   ```
   git clone https://github.com/mmmmaharshi/4bit-ciph.git
   cd 4bit-ciph
   ```
2. Make sure that the wide-trail bounds hold.
   ```
   python tests/test_bounds.py
   python tests/test_bounds32.py
   ```
3. Make sure that the KAT and the Py↔C cross-check hold.
   ```
   python tests/test_kats.py
   python tests/test_kats32.py
   python compare.py
   python compare32.py
   ```
4. Make sure that the generic synth stat holds.
   ```
   yowasp-yosys -p "read_verilog hw/quartet_sky130.v; hierarchy -check -top quartet_round_logic; proc; opt; techmap; opt; stat"
   ```

> [!TIP]
> Each step takes less than 30 seconds on a laptop. The full KAT32 run takes about 1 minute.

## Usage

QUARTET-16 encrypts a 16-bit block with a 64-bit key. QUARTET-32 encrypts a 32-bit block with a 128-bit key.

```python
import cipher, cipher32

ct = cipher.quartet_encrypt(0x1234, 0x0123456789ABCDEF)
pt = cipher.quartet_decrypt(ct, 0x0123456789ABCDEF)

ct32 = cipher32.quartet32_encrypt(0x12345678, 0x0123456789ABCDEF0123456789ABCDEF)
pt32 = cipher32.quartet32_decrypt(ct32, 0x0123456789ABCDEF0123456789ABCDEF)
```

C reference uses the same header contract:

```c
#define SBOX_READ(i) sbox[i]
#define INV_SBOX_READ(i) inv_sbox[i]
#include "sbox.h"
static const uint8_t sbox[16] = QUARTET_SBOX_INIT;
static const uint8_t inv_sbox[16] = QUARTET_INV_SBOX_INIT;
#include "quartet.h"    // QUARTET-16
#include "quartet32.h"  // QUARTET-32 = 2×16
uint16_t c = quartet_encrypt(0x1234, 0x0123456789ABCDEFULL);
uint32_t c32 = quartet32_encrypt(0x12345678, 0x0123456789ABCDEFULL, 0xFEDCBA9876543210ULL);
```

> [!CAUTION]
> Do not use the table S-box for cache-sensitive code on a cached CPU. Use `QUARTET_BITSLICED` from `sbox.h`.

## Project structure

```
4bit-ciph/
├── c/            # sbox.h, quartet_core.h, quartet.h, quartet32.h — C single source of truth
├── python/       # cipher.py, cipher32.py, cryptanalysis.py, fpe.py — Python single source of truth
├── runners/      # quartet_runner.c, quartet32_runner.c, quartetchiffre.c, bitsliced.c — thin I/O adapters
├── hw/           # quartet.v, quartet_logic.v, quartet_sky130.v, quartet_round_asm.s — RTL/ASM
├── tests/ + tests/vectors/  # 6 checks + 262k / 20k KAT
├── formal/ + coq/           # prp_analysis.md + Coq 8.18 proofs
├── SPEC.md / QUARTET32.md   # authoritative spec + branch note
└── python/cipher.py is SOT — `import cipher` needs `PYTHONPATH=python` or `sys.path` `REPO/python`
```

| Area | Files | Rule |
|------|-------|------|
| **Cipher** | `c/sbox.h`, `c/quartet_core.h`, `c/quartet.h` + `python/cipher.py` | One S-box, one round, one key schedule. Delete a duplicate and the build must break. No root shims — use `PYTHONPATH=python` and `gcc -I c`. |
| **Adapter** | `python/cipher32.py`, `c/quartet32.h` | `2×16` parallel, 128-bit key. Imports the cipher, adds no tables. |
| **Spec** | `SPEC.md` (§1, §10–11), `QUARTET32.md` | Bounds and GE numbers live here once. |
| **Proof** | `formal/prp_analysis.md`, `coq/quartet_correct.v`, `coq/prp_bound.v` | Machine-checked roundtrip + `q²/2³³` Feistel bound. |
| **Check** | `tests/test_bounds*.py`, `test_kats*.py`, `compare*.py`, `test_constant_time.py`, `tvla.py` | Six checks, each fails for a distinct real bug. |
| **Hardware** | `hw/quartet_sky130.v`, `hw/yosys_stat.log`, `hw/*.v` | 176 cells/round generic; 166 GE serial NanGate. See `hw/`. |

## Verification

This project uses six independent checks. Each check fails for a distinct, real reason when the code is wrong.

| Check | Command | What it proves |
|-------|---------|----------------|
| Wide-trail 16-bit | `python tests/test_bounds.py` | 32 active at 16 rounds gives `2⁻⁶⁴` |
| Wide-trail 32-bit | `python tests/test_bounds32.py` | 64 active at 16 rounds gives `2⁻¹²⁸` (reuse, no MILP) |
| KAT 16-bit | `python tests/test_kats.py` | 262157 vectors: Python and C match |
| KAT 32-bit | `python tests/test_kats32.py` | 20480 vectors: Python and C match |
| Cross-check | `python compare.py` / `compare32.py` | 20 random vectors Python↔C |
| Constant-time AST | `python tests/test_constant_time.py` | No data-dependent control in `quartet_core.h` |

> [!NOTE]
> A passing AST check is necessary but not sufficient for constant-time. The TVLA harness in `tests/tvla.py` is Level 1 software Welch t-test with a leaky negative control.

To run the KAT generator again:

```
python tests/generate_kat.py     # 262157 entries -> tests/vectors/quartet_kat.txt
python tests/generate_kat32.py   # 20480 entries  -> tests/vectors/quartet32_kat.txt
```

## Security at a glance

QUARTET gives a single-trail bound, not a full hull measurement. The 16-bit codebook is trivial (65536 texts).

- 16-round single-trail `DP/LP ≤ 2⁻⁶⁴` (32 active, `DU=4` gives `1/4` per S-box).
- 32-bit adapter gives `64` active and `2⁻¹²⁸` for the both-halves case (thin reuse, `tests/test_bounds32.py` PASS).
- Feistel Mode 1 (64-bit PRP, 4-call balanced, `n=32`) has `Adv ≤ q²/2³³ + 2⁻⁶⁰`. Machine-checked `q ≤ 5792` at `Adv 2⁻⁸` and `q ≤ 2¹⁶` at `Adv 1/2`. See `coq/prp_bound.v`.
- Birthday and codebook for 16-bit: `2⁸` and `2¹⁶`. For 32-bit the limits move to `2¹⁶` and `2³²`.

> [!NOTE]
> `SPEC.md` §10.3 lists four invariant subspaces on the raw permutation (≤ 1/256 of the state). Construction blocks must avoid those subspaces.

## Hardware and formal proofs

**Hardware (generic, library independent):**

- 1 round `quartet_round_logic` = 132 `$_XOR_` + 36 `$_AND_` + 8 `$_NOT_` = 176 cells.
- 16 rounds unrolled = 2816 cells (2112 XOR + 576 AND + 128 NOT). See `hw/yosys_stat.log` (or `synth/yosys_stat.log` shim).
- NanGate 45nm serial estimate: ~166 GE enc-only, ~254 GE enc+dec. QUARTET-32 doubles the cells: 352 per round, ~332 GE serial.

Run `hw/run_sky130.sh` (shim at `synth/run_sky130.sh` also works) to reproduce. Sky130 PDK stat needs `PDK_ROOT`.

**Formal proofs:**

- `coq/quartet_correct.v` proves `decrypt(encrypt(p,k),k)=p` for all `k` and `p` on `coqorg/coq:8.18` (3 MB `.vo`).
- `coq/prp_bound.v` proves the Feistel invertibility and the numeric `q²/2³³` bound.
- `coq/present_wide_trail.v` — **First machine-checked wide-trail bound for the ISO/IEC 29192-2 standardized PRESENT cipher** (Bogdanov et al., CHES 2007). Proves: S-box DU=4, 31-round min 62 active S-boxes, single-trail DP ≤ 2⁻¹²⁴.
- `tests/test_order4_layers.py` proves FullMix is one of 16 optimal matrices with `M⁴=I` and weight 12 (exhaustive over `GL(4,2)`).

## Modes

The spec in `SPEC.md` §10.4 defines five construction blocks with explicit bounds. The binding limit for 64-bit Feistel Mode 1 is the Luby-Rackoff `q²/2³³` term, not the `2⁻⁶⁴` trail. Mode 2 (Even-Mansour, 16-bit) is `2⁸` queries. The sponge and HEH modes are `2⁸` limited by the 8-bit capacity. Mode 5 (FPE) is `≤ 2¹⁶` and not for sensitive data.

We recommend QUARTET for 4-bit hardware, <200 GE, and a provable single-trail bound. Use a standard AEAD such as ASCON for bulk encryption.

> [!TIP]
> Start with `SPEC.md` §1 and §10.4, then run the quick start. That path shows the cipher, the proof, and the hardware in one read.
