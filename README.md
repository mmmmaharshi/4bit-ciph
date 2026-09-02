# QUARTET — 16-bit + 32-bit (thin adapter)

[![KAT 262k](https://img.shields.io/badge/KAT-262157%20PASS-brightgreen)](#kat)
[![KAT32 20k](https://img.shields.io/badge/KAT32-20480%20PASS-brightgreen)](#kat32)
[![Coq 8.18](https://img.shields.io/badge/Coq-quartets_correct.vo%20%7C%20prp_bound.vo-blue)](#formal)
[![Yosys](https://img.shields.io/badge/Yosys-176%20cells%2Fround-lightgrey)](#hardware)

16-bit artifact + 32-bit thin adapter sharing one S-box / FullMix (`M^4=I`).

**Quick check (2 min):**
```
python tests/test_bounds.py      # 32 active -> 2^-64 PASS
python tests/test_bounds32.py    # 64 active -> 2^-128 PASS (reuse)
python tests/test_kats.py        # 262157 PASS (Py+C)
python tests/test_kats32.py      # 20480 PASS (Py+C)
python compare.py && python compare32.py  # 20/20 each
yowasp-yosys -p "read_verilog synth/quartet_sky130.v; hierarchy -check -top quartet_round_logic; proc; opt; techmap; opt; stat"
```

**Tracks:** `SPEC.md` (honest `5792/2^16` Mode1) + `QUARTET32.md` (2×16, 332 GE serial) + `formal/` Coq.

Repo: `mmmaharshi/4bit-ciph` — `cipher.py` single source of truth.
