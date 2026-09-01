# QUARTET — Formal Assurances (status, 2026-09-02)

- `coq/quartet_correct.v` — not yet in the repository. Intended: prove
  `fullmix_order4` (+ the full round-trip) with Coq. Do not cite.
- `easycrypt/prp.ec` — not yet in the repository. Intended: a Luby-Rackoff
  PRP bound for §10.4 Mode 1. The earlier README text asserting an
  `Adv ≤ 32·2^-8 → 2^-32` result was retracted: it cannot be checked and
  it did not match the SPEC. The target number is 2^27 queries
  (§10.4 Mode 1); nothing in `formal/` has been derived.

Status: directory is scaffolding. No formal result exists yet.
SPEC §10.4 Mode 1 numbers are authoritative.

Compile (when files exist): `coqc coq/quartet_correct.v` ;
`easycrypt easycrypt/prp.ec`