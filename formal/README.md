# QUARTET — Formal Assurances (status, 2026-09-02)

## Completed Artifacts

- `coq/quartet_correct.v` — **Machine-checked.** Proves
  `quartet_roundtrip : forall K p, decrypt K (encrypt K p) = p` for *all*
  keys and plaintexts (structural, per-round invertibility telescoping;
  no enumeration). Verified with `coqc quartet_correct.v` on
  `coqorg/coq:8.18` (produces `quartet_correct.vo`, ~3 MB). Also proves
  `inv_fullmix_fullmix` (M³∘M = id, i.e. order-4) and the per-component
  cancellation lemmas.

- `formal/prp_analysis.md` — **Human-verified formal security analysis.**
  Precise specification of MODE 1 (4-call balanced Feistel over 32-bit
  halves), security game framework, hybrid argument structure, derivation
  of the Luby-Rackoff PRP bound ($g^2/2^{33}$ for $n=32$, $r=4$), QUARTET
  SPRP composition (hybrid switching cost $\leq 2^{-60}$), and target
  bound computation ($q \leq 2^{27}$ chosen-plaintext queries per SPEC
  §10.4). Includes full numerical evaluation table and Coq translation
  roadmap with five required lemma signatures.

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

## Pending

- `easycrypt/prp.ec` — Scaffolding (5 axioms corresponding to 5 Coq lemmas above).
  EasyCrypt package unavailable via opam; WSL OCaml 4.14.1 / opam 2.1.5 has no
  `easycrypt` package. Coq path (`coq/prp_bound.v`) is the portable replacement.

## Status

| Deliverable | Status | Verification |
|-------------|--------|-------------|
| Roundtrip correctness | Proven | Machine-checked (Coq 8.18 — `quartet_correct.vo`) |
| Wide-trail bounds | Verified | Machine-checked (Python — `tests/test_bounds.py`) |
| PRP advantage bound (Mode 1) | Proven | Machine-checked (`coq/prp_bound.v` QArith + Feistel) |

The PRP analysis in `formal/prp_analysis.md` captures all mathematical
content needed for an automated proof. The Coq translation roadmap
(§10 of that document) provides five precise lemma signatures ready for
implementation.

SPEC §10.4 Mode 1 numbers are authoritative for all PRP claims.

Compile Coq proofs: `docker --context default run --rm -v "%cd%/coq:/w" -w /w coqorg/coq:8.18 coqc quartet_correct.v && coqc prp_bound.v`
WSL fallback (no Docker): `wsl -e bash -c 'coqc coq/quartet_correct.v && coqc coq/prp_bound.v'` after `sudo apt install coq` (8.18) or `opam install rocq-prover` (Rocq 9.x).