# AGENTS.md

Operating guide for AI coding agents working in this repository.

## Must follow

- **[@CODING_STANDARDS.md](./CODING_STANDARDS.md) is binding.** Read it before changing anything. Its rules are not advisory; they are project policy. If a change contradicts a rule, do not make the change.

## Project shape

- One cipher (QUARTET) in two languages, one shared contract.
  - `cipher.py` — the cipher, single Python source of truth.
  - `cryptanalysis.py` — analyses (DDT/LAT/SAC/diff/linear/stats/benchmark); imports `cipher`.
  - `sbox.h` — S-box and inverse, single C source of truth (initializers only).
  - `quartet.h` — cipher interface and implementation (header-only).
  - `quartetchiffre.c` — canonical C reference: defines the S-box tables and `SBOX_READ` macros, includes `quartet.h`, runs the self-test.
  - `quartet_runner.c` — thin stdin/stdout adapter over `quartet.h`.
  - `compare.py` — harness: random Python vs C vectors through the runner.
  - `cross_check.py` — harness: C self-test plus 65536×4 roundtrip.
  - `quartet_round_asm.s` — one-round AVR assembly reference, cycle count.
  - `SPEC.md` — authoritative spec (cipher parameters, test vectors, files section).

**Do not duplicate the cipher, the S-box, the round function, the key schedule, or the test vectors across files.** If a new file needs the cipher, include `cipher.py` / `quartet.h`. If a new file needs the S-box, use `sbox.h`. The deletion test confirms duplication: deleting any duplicate should either break the build (real duplication, the source of truth is wrong) or be invisible (stale copy, must be removed). Never accept the second case.

## Architectural vocabulary

This project uses the terms from `/codebase-design`: **module, interface, implementation, depth, seam, adapter, leverage, locality.** Use them exactly. Do not substitute "component", "service", "API", "boundary", "layer", or "wrapper".

## Conventions

- **Python:** stdlib only. No new dependencies. The cipher module is fast-import (no module-load computation beyond class/function definitions and tiny lookup tables).
- **C:** portable C11. AVR-friendly: keep `__attribute__((progmem))` placement concerns in the `.c` file that defines the S-box tables, not in `sbox.h` or `quartet.h`. The headers stay portable.
- **Tests:** every test must fail for a distinct, real reason if the code is wrong. Do not assert the implementation against itself.
- **Adapters:** when adding a second implementation (e.g. a new language, a new I/O transport), give it its own thin module that implements the same contract as the existing one. Two adapters justify a seam; one does not.
- **Dead code:** delete it. If you add an interface that has no caller, you have added a speculative API — remove it or wait for a real caller.

## Workflow

1. Read `SPEC.md` and `@CODING_STANDARDS.md` before changing anything.
2. Prefer editing existing files to creating new ones. A new file is justified only when it carries a distinct concept the existing files don't own.
3. Run `python compare.py` and `python cross_check.py` after any change to the cipher, the S-box, the key schedule, the test vectors, or the C/Python harness contract. Both must pass.
4. If a change contradicts `SPEC.md`, update `SPEC.md` in the same change.
5. If a change contradicts a rule in `CODING_STANDARDS.md`, do not make the change.
6. Prompt the user before committing. Use conventional commit messages.

## Things that will get a change reverted

- Editing the S-box, FullMix, round function, key schedule, or test vectors in more than one place. There is one source of truth per language; keep it that way.
- Adding a `__attribute__((progmem))` placement, a wrapper function, or a configuration flag that exists only to support a hypothetical future use.
- Adding a test that just restates the implementation.
- Adding `if version > 1` style backwards-compat branches.

## File map

| File | Owns | Imports / includes |
|------|------|--------------------|
| `cipher.py` | The cipher (S-box, FullMix, round, key schedule, encrypt, decrypt, self-test) | stdlib only |
| `cryptanalysis.py` | DDT, LAT, SAC, differential, linear, statistics, benchmark, test vectors | `cipher` |
| `sbox.h` | PRESENT S-box and inverse initializers | `<stdint.h>` |
| `quartet.h` | Cipher interface and implementation (header-only) | `sbox.h` is included by the consumer; `quartet.h` requires `SBOX_READ` / `INV_SBOX_READ` |
| `quartetchiffre.c` | C reference: defines the S-box tables, runs the self-test | `sbox.h`, `quartet.h` |
| `quartet_runner.c` | stdin/stdout adapter for cross-validation | `sbox.h`, `quartet.h` |
| `quartet_round_asm.s` | One-round AVR assembly reference, cycle count | `<avr/io.h>` |
| `compare.py` | Cross-validation harness (Python vs C, 20 random vectors) | `cipher`, subprocess |
| `cross_check.py` | C self-test + full 65536×4 roundtrip | `cipher`, subprocess |
| `SPEC.md` | Spec, test vectors, file map | — |
| `CODING_STANDARDS.md` | Project policy, **must follow** | — |
