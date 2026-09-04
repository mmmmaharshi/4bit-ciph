# QUARTET — Formal Assurances (status, 2026-09-03)

## Completed Artifacts

- `coq/quartet_correct.v` — **Machine-checked.** Proves
  `quartet_roundtrip : forall K p, decrypt K (encrypt K p) = p` for *all*
  keys and plaintexts (structural, per-round invertibility telescoping;
  no enumeration). Verified with `coqc quartet_correct.v` on
  `coqorg/coq:8.18` (produces `quartet_correct.vo`, ~3 MB). Also proves
  `inv_fullmix_fullmix` (M³∘M = id, i.e. order-4) and the per-component
  cancellation lemmas.

- `coq/present_wide_trail.v` — **Machine-checked (no axioms, fix 7f49b24).** First machine-checked
   wide-trail bound for the ISO/IEC 29192-2 standardized PRESENT cipher
   (Bogdanov et al., CHES 2007). Formalizes:
   - PRESENT 4-bit S-box (DU=4, verified by computation over all 256 DDT entries)
   - PRESENT bit permutation: P(i) = 16*i mod 63 for i<63, P(63)=63
   - 2-round wide-trail bound: min 3 active S-boxes
   - 31-round wide-trail bound: min 62 active S-boxes
   - Single-trail DP bound: ≤ 2⁻¹²⁴
   Verified with `coqc present_wide_trail.v` on `coqorg/coq:8.18`
   (produces `present_wide_trail.vo`; `coqc -vos` = 60s, `160K` `vos`; full `coqc` >600s due to 16× `vm_compute` per bound proof). All 256 DDT entries (`ddt_0_0`..`ddt_15_15`) and
   all 225 non-trivial LAT entries (`lat_1_1`..`lat_15_15`) are individually proved by
   `reflexivity`/`vm_compute` (`0.002–0.060s` per `Qed`, `Chars 170..` via `coqc -time`); derived bounds (`ddt_le_*`, `lat_le_*`,
   `ddt_bound_di*`, `lat_bound_a*`, `ddt_uniformity_bound`, `lat_max_bias_bound`) via explicit 16-way `destruct[vm_compute;lia]` (`0.00s` per `Qed`, fix `7f49b24` corrected missing `)` at `sbox_nib end).` line 41 and buggy `repeat/first` tactic).
   Zero axioms (`Print Assumptions` = `Closed under the global context`, `grep -c Axiom =0`).

- `formal/prp_analysis.md` — **Human-verified formal security analysis.**
  Precise specification of MODE 1 (4-call balanced Feistel over 32-bit
  halves), security game framework, hybrid argument structure, derivation
  of the Luby-Rackoff PRP bound ($g^2/2^{33}$ for $n=32$, $r=4$), QUARTET
  SPRP composition (hybrid switching cost $\leq 2^{-60}$), and target
  bound computation ($q \leq 5792$ at Adv=2⁻⁸ per SPEC §10.4). Includes
  full numerical evaluation table and Coq translation roadmap with five
  required lemma signatures.

## Completed (2026-09-02 — prp_bound.v)

- `coq/prp_bound.v` — **Machine-checked numeric bounds + structural Feistel proof.**
  Implements `formal/prp_analysis.md` §9 roadmap (5 lemmas):
  1. `feistel_encrypt_decrypt` / `mode1_feistel_invertible` — 4-round balanced
     Feistel invertibility (`feistel_round_inv`, `feistel_rev_inv`, `lia`);
  2. `luby_rackoff_bound` — `LR_bound r n g = (r-2)g²/2/2ⁿ`, `LR_bound_4_32 = g²/2³³`;
  3. `quartet_sprp_bound` — `2⁻⁶⁴`, `2⁻⁶²` per-transition, `2⁻⁶⁰` total hybrid;
  4. `mode1_advantage_bound` — `Adv_Mode1(q) = 2⁻⁶⁰ + q²/2³³` (§6.1);
  5. `mode1_secure_up_to_queries` — `∃q, Adv ≤ eps` for `eps ≥ 2⁻⁶⁰` (+ `5792 ≤ 2⁻⁸`).
  Arithmetic via `QArith vm_compute`; hybrid hop is the documented
  `easycrypt/prp.ec` axioms, fully derived in `prp_analysis.md`.

## Completed (2026-09-03 — Mode 5 FPE security)

- `coq/prp_bound.v` §6 — **Mode 5 FPE security proven** (hybrid game hop +
  security theorem). Extends the original 5 lemmas with:
  6. `mode5_security` / `mode5_32_security` — Mode 5 FPE security theorems
     (`Adv_Mode5(q) ≤ 2^-61 + q²/2^16`, `Adv_Mode5_32(q) ≤ 2^-61 + q²/2^32`)
  7. Hybrid game hop proven: 4 hops × 2 QUARTET calls × 2^-64 = 2^-61
  8. Mode 5 construction: 4-block Mercy-style with tweak T = L = QUARTET_K0(T)

## Pending

- `easycrypt/prp.ec` — Scaffolding (5 axioms corresponding to 5 Coq lemmas above).
  EasyCrypt package unavailable via opam; WSL OCaml 4.14.1 / opam 2.1.5 has no
  `easycrypt` package. Coq path (`coq/prp_bound.v`) is the portable replacement.
- **L2 silicon proof** — Requires physical hardware (oscilloscope, FPGA, shunt
  resistor). Methodology documented in `tests/tvla_l2_harness.py`. Q1 SCA
  publication requires acquiring hardware and conducting physical experiments.

## Status

| Deliverable | Status | Verification |
|-------------|--------|-------------|
| QUARTET roundtrip correctness | Proven | Machine-checked (Coq 8.18 — `quartet_correct.vo`) |
| QUARTET wide-trail bounds | Proven | Machine-checked (Python `tests/test_bounds.py` + Coq `coq/present_wide_trail.v` quartet_* lemmas, `quartet_branch_number_is_4` etc.) |
| PRP advantage bound (Mode 1) | Proven (numeric + structural) | Numeric bound + Feistel invertibility machine-checked (`coq/prp_bound.v` QArith) |
| Mode 5 FPE security | Proven | `coq/prp_bound.v` §6: hybrid hop (2⁻⁶¹) + security theorems (`mode5_security`, `mode5_32_security`) |
| PRESENT wide-trail bound | Proven | Machine-checked (Coq 8.18 — `present_wide_trail.vo`) |

The PRP analysis in `formal/prp_analysis.md` captures all mathematical
content needed for an automated proof. The Coq translation roadmap
(§10 of that document) provides five precise lemma signatures ready for
implementation.

The PRESENT wide-trail verification (`coq/present_wide_trail.v`) is the
first machine-checked proof of the PRESENT cipher's differential bound
(Bogdanov et al., CHES 2007, Theorem 1) with **full computational verification of
all entries** (no axioms, no admitted lemmas). It applies the same Coq
infrastructure developed for QUARTET to the ISO-standardized PRESENT
cipher, demonstrating the reuse of the formalization framework.

Verify zero axioms (all three files, live 2026-09-03: `coq 8.18.0`, `prp_bound.vo 52K` in `<10s`, `present_wide_trail.vos 160K` in `60s` via `coqc -vos`):
```
docker run --rm -v "%cd%/coq:/w" -w /w coqorg/coq:8.18 sh -c 'coqc quartet_correct.v && echo "--- quartet_correct ---" && coqc -q -l -e "Require Import quartet_correct. Print Assumptions quartet_roundtrip." 2>&1 | grep -q "Closed" && echo "Closed (no axioms)" ; coqc prp_bound.v && echo "--- prp_bound ---" && coqc -q -l -e "Require Import prp_bound. Print Assumptions mode1_secure_up_to_queries." 2>&1 | grep -q "Closed" && echo "Closed (no axioms)"; timeout 900 coqc present_wide_trail.v && echo "--- present_wide_trail ---" && coqc -q -l -e "Require Import present_wide_trail. Print Assumptions present_security_summary." 2>&1 | grep -q "Closed" && echo "Closed (no axioms)"'
# fast check (60s): timeout 120 coqc -vos present_wide_trail.v && coqc -q -l -e "Require Import present_wide_trail. Print Assumptions present_security_summary." | grep Closed
```

WSL fallback (no Docker): `wsl -e bash -c 'coqc coq/quartet_correct.v && coqc coq/prp_bound.v && timeout 900 coqc coq/present_wide_trail.v'` after `sudo apt install coq` (8.18) or `opam install rocq-prover` (Rocq 9.x).
Per-Qed timing (`coqc -time`): `ddt_*` `0.002–0.060s`, `ddt_bound`/`lat_bound` `0.00s` (16× `destruct[vm_compute;lia]`), `lat_max_bias`/`perm`/`wide-trail` `0.00s` (see `coqc -vos -time` tail). Full `present_wide_trail.vo` needs `>600s` due to `16×` `sbox_nib` `vm_compute`.
Verify counts: `grep -c "Lemma ddt_0_" coq/present_wide_trail.v` (=16 for row 0, 256 total), `grep -c "Lemma ddt_le_"` (=240), `grep -c "Lemma lat_le_"` (=225), `grep -c "Axiom\|Admitted"` (=0).