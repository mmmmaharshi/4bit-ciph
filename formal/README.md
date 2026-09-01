# QUARTET — Formal Ceiling 1
- `coq/quartet_correct.v` — `fullmix_order4` via `vm_compute`, round-trip placeholder exhaustive 2^16
- `easycrypt/prp.ec` — PRP game sketch, `Adv ≤32·2^-8` → `2^-32` for 10-round Feistel (uses `fpe.py`)

Compile: `coqc coq/quartet_correct.v` ; `easycrypt easycrypt/prp.ec`
