# QUARTET — Formal Assurances (status, 2026-09-02)

- `coq/quartet_correct.v` — **Machine-checked.** Proves
  `quartet_roundtrip : forall K p, decrypt K (encrypt K p) = p` for *all*
  keys and plaintexts (structural, per-round invertibility telescoping;
  no enumeration). Verified with `coqc quartet_correct.v` on
  `coqorg/coq:8.18` (produces `quartet_correct.vo`, ~3 MB). Also proves
  `inv_fullmix_fullmix` (M³∘M = id, i.e. order-4) and the per-component
  cancellation lemmas.
- `easycrypt/prp.ec` — not yet in the repository. Intended: a Luby-Rackoff
  PRP bound for §10.4 Mode 1. The earlier README text asserting an
  `Adv ≤ 32·2^-8 → 2^-32` result was retracted: it cannot be checked and
  it did not match the SPEC. The target number is 2^27 queries
  (§10.4 Mode 1); nothing on the PRP side has been derived.

Status: Coq round-trip is proved; EasyCrypt PRP remains scaffolding.
SPEC §10.4 Mode 1 numbers are authoritative for the PRP claim.

Compile: `docker --context default run --rm -v "%cd%/coq:/w" -w /w coqorg/coq:8.18 coqc quartet_correct.v`