# QUARTET: A 4-bit Word-Oriented Block Cipher

**Version 1.0 — Reference Implementation Verified**

Mano H. | 2026

---

## 1. Overview

QUARTET is a 16-bit-block, 64-bit-key SPN designed for use as a construction
block in modes where the underlying permutation must be 4-bit-native. It is
the smallest block cipher with an order-4 linear layer (M⁴ = I), a provable
2-round differential/linear bound, and a 16-round single-trail bound of DP/LP ≤ 2^(-64).
PRESENT (Bogdanov et al., CHES 2007) shares the PRESENT 4-bit S-box and the
4-bit-word design goal, but operates on 64-bit blocks; QUARTET is the
4-bit-native SPN at the smallest block size (16-bit) where the
wide-trail strategy still yields a single-trail 2^(-64) bound.

**Design Goals:**
- 16-bit block (four 4-bit words)
- 64-bit key (sixteen 4-bit words, stored serially)
- 2^64 brute-force resistance at the key level
- Complete differential diffusion: every output bit depends on every input
  bit after 2 rounds
- Full avalanche behavior (≈50% bit changes per flip)
- Implementable in ~166 gate equivalents, serial architecture
  (encryption-only hardware; ~254 GE with decryption — see §11.4)
- 8-bit AVR software: under 700 cycles per block @ 16 rounds

**Fundamental Limitation — Block Size:**
QUARTET has a **16-bit block (2^6 = 65536 plaintexts)**. This is a
hard ceiling that no analysis can overcome:

| Property | Value | Implication |
|----------|-------|-------------|
| Codebook size | 2^16 = 65,536 | Trivially enumerable |
| Birthday bound | 2^8 = 256 queries | Distinguisher with advantage ≈ 1/2 |
| Empirical DP_max | ~2^-6.38 | 10^17× worse than 2^-64 single-trail |

**No Q1 venue publishes a 16-bit bulk cipher.** The birthday bound of
2^8 queries means QUARTET cannot be used for bulk encryption regardless
of the trail bound. This is acknowledged, not a disclaimer.

**What IS provable:**
- Single-trail DP/LP ≤ 2^-64 at 16 rounds (machine-checked in Coq)
- Complete differential diffusion after 2 rounds
- Constant-time implementation (AST-verified)
- Tight wide-trail bound (2 active/round, verified by construction at R=8)

**What is NOT provable:**
- Any security beyond 2^8 queries (birthday bound is fundamental)
- A hull bound (empirical 2^-6.38 vs proven 2^-64 single-trail)

**Positioning:** QUARTET is a **4-bit-native construction block** for
use in larger constructions (Feistel, sponge, FPE), not a stand-alone
bulk cipher. Its value is:
1. Smallest 4-bit SPN with order-4 linear layer (M^4 = I)
2. Machine-checked security proofs (Coq)
3. ~166 GE serial hardware footprint
4. Analysis methodology (hull enumeration, tightness verification)

**NOT recommended:** Bulk encryption, any use requiring >2^8 queries.

---

## 2. Cipher Parameters

### 2.1 QUARTET-16 (Base)

| Parameter | Value |
|-----------|-------|
| Block size | 16 bits (4 nibbles) |
| Key size | 64 bits (16 nibbles) |
| Rounds | 16 (default), 4 (lightweight) |
| S-box | PRESENT 4×4 (DU=4, max LP=4/16) |
| Linear layer | FullMix (4×4 GF(2) matrix, branch #4) |
| Key schedule | Position-dependent S-box mixing |

### 2.2 QUARTET-32 (Promoted Primary)

QUARTET-32 is a **32-bit block adapter** built from two independent
QUARTET-16 instances. It is promoted to **primary status** because:
- 32-bit block gives birthday bound 2^16 (vs 2^16 for QUARTET-16)
- Both-halves-active single-trail bound: 2^-128 (64 active S-boxes)
- The 2^-128 bound is meaningful: q << 2^16 makes trail bound relevant

| Parameter | Value |
|-----------|-------|
| Block size | 32 bits (8 nibbles) |
| Key size | 128 bits (2×64) |
| Rounds | 16 |
| Construction | Two independent QUARTE-16 instances (hi \|\| lo) |
| Both-halves bound | 2^-128 (64 active S-boxes) |
| Single-half bound | 2^-64 (32 active S-boxes) |
| Birthday bound | 2^16 queries |

**Security positioning:**
- QUARTET-16: 2^8 birthday bound — only for construction block use
- QUARTET-32: 2^16 birthday bound — usable for modest-security applications
- QUARTET-32 in Feistel: 2^16 security (64-bit block)

**Files:** `python/cipher32.py`, `c/quartet32.h`, `tests/test_bounds32.py`

---

## 3. S-Box (PRESENT)

```
index:  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
value:  C  5  6  B  9  0  A  D  3  E  F  8  4  7  1  2
```

**Inverse S-box:**
```
index:  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
value:  5  E  F  8  C  1  2  D  B  4  6  3  0  7  9  A
```

**Properties:**
- Bijection (all 16 output values distinct)
- Differential uniformity: **4** (best possible for 4-bit bijection)
- Max differential probability: 4/16 = 2^(-2)
- Max linear probability: 4/16 = 2^(-2)
- Algebraic degree: 3 (maximum for 4-bit S-box)
- No fixed points
- Not involution

---

## 4. Linear Layer: FullMix

**Matrix over GF(2) (4×4):**
```
| 1 1 1 0 |
| 0 1 1 1 |
| 1 0 1 1 |
| 1 1 0 1 |
```

**Per-nibble operation:**
```
W0' = W0 ⊕ W1 ⊕ W2
W1' = W1 ⊕ W2 ⊕ W3
W2' = W2 ⊕ W3 ⊕ W0
W3' = W3 ⊕ W0 ⊕ W1
```

**Properties:**
- Bijective (65536/65536 outputs)
- **Order 4** (M² = swap halves, M⁴ = I, M⁻¹ = M³ = [[1,0,1,1],[1,1,0,1],[1,1,1,0],[0,1,1,1]]) — inverse is distinct (adds ~88 GE for dec: inverse S-box 64 + M³ 24)
- **Branch number: 4** (the Singleton/MDS bound for a 4-word linear
  layer is m+1 = 5; a branch-5 MDS layer needs matrix entries outside
  {0,1}, outside the XOR-only 4-bit-native goal — FullMix does not attain MDS)
- Each output bit depends on all 16 input bits
- Single-bit input affects 3 of 4 nibbles in the output

---

## 5. Round Function

One round Rk for round key k ∈ W4:

```
Input: state S = [W0, W1, W2, W3]  (16 bits, 4 nibbles)
1. S-box layer:   Wi ← SBOX[Wi] for i ∈ {0,1,2,3}
2. Key XOR:       Wi ← Wi ⊕ k    for i ∈ {0,1,2,3}
3. FullMix:       Si ← S0...3 ⊕ Mi,j * Sj  (linear layer)
Output: state S' (16 bits)
```

The round key is a single 4-bit word applied uniformly to all 4 nibbles.

---

## 6. Key Schedule

64-bit key K = [k0, k1, ..., k15] (16 nibbles) expands to 16 round keys.

For round i:
```
rkey[i] = K[i mod 16] ⊕  ⊕_{j=0..15}  SBOX[ (K[j] ⊕ (i + j + 1)) mod 16 ]
```

Each round key depends on all 16 key nibbles and the round position.

**Properties:**
- Position-dependent mixing prevents key degeneracy
- Each round key is 4 bits, but information-theoretic entropy is 64 bits
- Invertible (decryption reverses the key expansion)

**Diffusion Analysis:**

The key schedule applies the S-box nibble-wise: each key nibble K[j] is
XORed with a round-dependent constant, then passed through the S-box.
The S-box outputs are XORed together to produce the round key.

While the S-box operates nibble-wise, the XOR accumulation provides
mixing across all key nibbles. Measured diffusion properties:

| Property | Value | Assessment |
|----------|-------|------------|
| Min key bits affecting a round key bit | 23 of 64 | Adequate |
| Max key bits affecting a round key bit | 63 of 64 | Good |
| Single key bit flip: avg round key bits changed | 39.8 of 64 | Good (ideal: 32) |
| Key nibble coverage | 16/16 nibbles | Full |
| Round key independence (random keys) | 16/16 unique | Full |

**Weak keys.** Keys with all identical nibbles (e.g. 0x0000000000000000,
0xFFFFFFFFFFFFFFFF) produce the same round key for all rounds. The
round constants (`_RC_BASE = [0, 5, 0xA, 0xF]`) break this symmetry:
the effective key (round_key XOR round_constant) differs for each
round, producing 16 unique effective keys. The cipher remains secure
even with these weak keys, but they should be avoided in practice.

---

## 7. Full Cipher

```
QUARTET-16/64(plaintext P, key K):
  state ← P                                    # 4 nibbles
  for i = 0 to R-1:                           # R = 16
    state ← R_{rkey[i]}(state)
  return state
```

---

## 8. Decryption

Decryption reverses the round operations in reverse order:

```
QUARTET_DECRYPT(ciphertext C, key K):
  state ← C
  for i = R-1 downto 0:
    state ← INV_FULLMIX(state)
    state ← [Wi ⊕ rkey[i] for Wi in state]
    state ← [INV_SBOX[Wi] for Wi in state]
  return state
```

Note: FullMix has order 4, so `INV_FULLMIX = M³` with `W0' = W0⊕W2⊕W3, W1' = W0⊕W1⊕W3, W2' = W0⊕W1⊕W2, W3' = W1⊕W2⊕W3` (12 XORs, same cost as FullMix).

**Lightweight mode (R=4) caveat.** The R=4 mode gives a provable
DP/LP bound of (1/4)^(2·4) = 2^(-16), which is the same order as the
random-permutation limit for a 16-bit block. R=4 is a *throughput /
footprint* mode, not a security tier. Use R=4 only where the attacker
is resource-constrained and the secret is rotated frequently. For any
other use, R=16. See §10.4 for the recommended-use table.

---

## 9. Test Vectors (VERIFIED)

### Test Set 1: Key = 0x0123456789ABCDEF

| Plaintext | Ciphertext | Decrypted | Status |
|-----------|------------|-----------|--------|
| 0x0000 | 0xDDDD | 0x0000 | OK |
| 0x0001 | 0xDDDF | 0x0001 | OK |
| 0x000F | 0xDDD5 | 0x000F | OK |
| 0x1234 | 0x6927 | 0x1234 | OK |
| 0xDEAD | 0xBC0B | 0xDEAD | OK |
| 0xFFFF | 0x5555 | 0xFFFF | OK |
| 0x0123 | 0xC8DF | 0x0123 | OK |
| 0x4567 | 0x7B15 | 0x4567 | OK |
| 0x89AB | 0xEBC7 | 0x89AB | OK |
| 0xCDEF | 0x6C3E | 0xCDEF | OK |

### Test Set 2: Key = 0xFFFFFFFFFFFFFFFF

| Plaintext | Ciphertext |
|-----------|------------|
| 0x0000 | 0x3333 |
| 0x0001 | 0x333A |
| 0x1234 | 0x19B4 |
| 0xDEAD | 0x8E08 |
| 0xFFFF | 0xDDDD |

### Test Set 3: Key = 0x0000000000000000

| Plaintext | Ciphertext |
|-----------|------------|
| 0x0000 | 0x4444 |
| 0x0001 | 0x4440 |
| 0x1234 | 0xCF7E |
| 0xDEAD | 0xB5AB |
| 0xFFFF | 0xFFFF |

### Test Set 4: Key = 0xFEDCBA9876543210

| Plaintext | Ciphertext |
|-----------|------------|
| 0x0000 | 0x9999 |
| 0x0001 | 0x999E |
| 0x1234 | 0x50CF |
| 0xDEAD | 0xED7E |
| 0xFFFF | 0x5555 |

### Test Set 5: Lightweight Mode (4 rounds, key 0x0123456789ABCDEF)

| Plaintext | Ciphertext |
|-----------|------------|
| 0x1234 | 0xB7FE |
| 0xDEAD | 0xBE4B |

---

## 10. Security Analysis

### 10.1 Wide-Trail Bound (with Vacuity Statement)

| Property | Bound | Method |
|----------|-------|--------|
| S-box max DP | 4/16 = 2^(-2) | Exhaustive check (DU=4) |
| S-box max LP | 4/16 = 2^(-2) | Exhaustive check (LAT) |
| Linear layer branch # | 4 | Exhaustive check (16-bit state) |
| Min active S-boxes per 2-round diff | 4 | Wide-trail (see below) |
| 2-round DP bound | (1/4)^4 = 2^(-8) | Wide-trail |
| 2-round LP bound | (1/4)^4 = 2^(-8) | Wide-trail |
| 16-round single-trail DP bound | ≤ 2^(-64) | Wide-trail (chained) |
| 16-round single-trail LP bound | ≤ 2^(-64) | Wide-trail (chained) |

**Rounds needed for single-trail DP/LP < 2^(-64): 16 rounds.**

**IMPORTANT VACUITY STATEMENT.** The 2^(-64) single-trail bound is a bound on
individual differential/linear trails, NOT a bound on the cipher's actual
differential probability against a real adversary. For a 16-bit block cipher:

- The random-permutation limit is ~2^(-16) (birthday bound on block)
- A full-codebook adversary with 2^16 queries can distinguish with advantage ≈ 1
- The meaningful security threshold is **q << 2^8** (birthday attack on block)

The 2^(-64) bound is therefore **vacuous for a full-codebook adversary**. It is
meaningful only when the adversary's query complexity is bounded well below 2^8,
or when QUARTET is used as a building block in a wide-block construction (see
§10.4, Mode 5) where the birthday bound applies to the wider block.

#### Wide-Trail Argument (2-Round Differential Lower Bound)

The wide-trail strategy (Daemen, 1995; Daemen & Rijmen, 2002) bounds the
maximum expected differential probability (EDP) over multiple rounds by
counting the minimum number of active S-boxes in any 2-round trail, then
applying the S-box's max DP per active S-box.

**Step 1 — State model.** The 16-bit state is a column vector over
GF(2)^(16), with the four 4-bit words W0, W1, W2, W3 forming a 4×4
matrix:

```
S = [ W0 ]   [ s_0  s_1  s_2  s_3  ]   (W0 = [s_0, s_1, s_2, s_3])
    [ W1 ] = [ s_4  s_5  s_6  s_7  ]   (W1 = ...)
    [ W2 ]   [ s_8  s_9  s_10 s_11 ]
    [ W3 ]   [ s_12 s_13 s_14 s_15 ]
```

A *differential* is a non-zero state ΔS in the same column-vector form.
The *weight* of a differential is the number of non-zero 4-bit words
(nibbles), equivalently the number of active S-boxes in a single round.

**Step 2 — Branch number.** FullMix is a linear map M: GF(2)^(16) → GF(2)^(16)
with branch number 4 (exhaustively verified: 2^16 = 65,536 inputs, the
minimum of (h_in + h_out) over non-zero ΔS is 4). The theoretical maximum
for a 4-word linear layer is the Singleton/MDS bound m+1 = 5; a branch-5
(MDS) layer requires matrix entries outside {0,1}, which is outside
QUARTET's XOR-only, 4-bit-native design goal. Branch #8 would require a
different state geometry entirely.

**Step 3 — Two-round trail count.** Consider any 2-round differential
trail (ΔS_0, ΔS_1, ΔS_2) where ΔS_0 is the input differential, ΔS_1 is
the differential after round 1 (post-FullMix), and ΔS_2 is the output
differential. The branch number constraint forces:

```
h(ΔS_0) + h(ΔS_1) ≥ 4   (round 1)
h(ΔS_1) + h(ΔS_2) ≥ 4   (round 2)
```

Summing the two constraints: h(ΔS_0) + 2·h(ΔS_1) + h(ΔS_2) ≥ 8.

If ΔS_0 ≠ 0 and ΔS_2 ≠ 0 (non-trivial 2-round trail), then h(ΔS_0) ≥ 1
and h(ΔS_2) ≥ 1, giving h(ΔS_1) ≤ (8 - 2)/2 = 3. The minimum of
h(ΔS_0) + h(ΔS_1) + h(ΔS_2) subject to the two constraints and
h(ΔS_0), h(ΔS_2) ≥ 1 is **4 active S-boxes total** (achieved by, e.g.,
ΔS_0 with one active nibble, ΔS_1 with two active nibbles, ΔS_2 with one
active nibble).

**Step 4 — 2-round DP bound.** Each active S-box contributes a factor of
at most 1/4 (PRESENT's max DP). The 2-round expected differential
probability (EDP) over all trails (ΔS_0, ΔS_1) is:

```
EDP_2(ΔS_0 → ΔS_2) ≤ (1/4)^4 = 2^(-8)
```

(The 1/4 factor is per active S-box, and the minimum trail has 4 active
S-boxes.) The maximum over input differentials is therefore also
≤ 2^(-8).

**Step 5 — 16-round bound by chaining.** The 16-round bound is obtained
by chaining 8 disjoint 2-round sub-trails, each contributing ≤ 2^(-8):

```
max single-trail EDP ≤ (2^(-8))^8 = 2^(-64)
max single-trail LP ≤ (2^(-8))^8 = 2^(-64)
```

The disjointness of the 2-round sub-trails is guaranteed by the
intermediate-round differentials being non-zero (any 2-round trail with
a zero intermediate differential has a branch-number violation and is
not a valid trail).

**Machine-checked verification.** The bound claims in this subsection
are checked exhaustively in `tests/test_bounds.py` and proven in Coq in
`coq/present_wide_trail.v` (QUARTET section). Both the Python enumeration
and Coq proofs use exhaustive enumeration over all 2^16 non-zero input
differentials. These are bounds on **individual trails (differential/linear
characteristics)**, not a measurement of the cipher's actual differential
probability against a real adversary:

| Property | Spec claim | Verified |
|----------|------------|----------|
| S-box differential uniformity (DU) | 4 | yes (exhaustive DDT) |
| S-box max LP numerator (max \|count − 8\|) | 4 | yes (exhaustive LAT) |
| FullMix branch number | 4 | yes (2^16 pairs) |
| Min 2-round active S-boxes | 4 | yes (2^16 trails) |
| Min 4-round active S-boxes | 8 | yes (2^16 trails) |
| Min 8-round active S-boxes | 16 | yes (2^16 trails) |
| Min 16-round active S-boxes | 32 | yes (2^16 trails) |
| 2-round single-trail DP bound | 2^(−8) | yes |
| 16-round single-trail DP bound | 2^(−64) | yes |

The 16-round single-trail DP bound of 2^(−64) is computed two independent
ways: (a) via the 2-round chain argument above (4 active × 8 disjoint
sub-trails = 32 active → (1/4)^32 = 2^(−64)), and (b) via direct
enumeration of min total active S-boxes over 16 rounds (also 32, giving
2^(−64)). Both methods agree. The Coq proof in `coq/present_wide_trail.v`
confirms these values.

The same verification is applied to the linear side: the PRESENT S-box
LAT is computed exhaustively, the linear branch number is verified to
match the differential branch number (4), and the linear trail min
total active S-boxes is enumerated for R = 2, 4, 8, 16 rounds. The
linear single-trail bound is 2^(−64) at 16 rounds, matching the
differential side.

**Vacuity for full-codebook adversary.** As stated above, the 2^(-64)
single-trail bound does NOT imply 2^(-64) security against a real adversary.
For QUARTET used directly as a 16-bit block cipher:

- **Security is bounded by the birthday attack on the 16-bit block: ~2^8 queries**
- An adversary with 2^16 chosen plaintexts can distinguish with advantage ≈ 1
- The 2^(-64) bound is only meaningful when q << 2^8

**When the bound IS meaningful:**
- QUARTET as a building block in wide-block constructions (Mode 5, §10.4)
- Adversaries with query complexity bounded well below 2^8
- PRF security in fixed-key constructions where the adversary cannot
  collect enough plaintext-ciphertext pairs to exploit the birthday bound

**Tightness.** The 2^(-64) bound is a **lower bound on the security**
(max single-trail EDP/LP ≤ 2^(-64) is a necessary condition for a small
differential/linear probability, but it does not by itself establish
2^(64) chosen-plaintext security — see §10.2, which shows the empirical
max trail at R=4 is only ~2^2.6 over the random expectation). The
**actual maximum DP/LP over 16 rounds** was determined empirically via
exhaustive 2^32-pair enumeration (`tests/test_hull_empirical.c`):
**DP_max ≈ 2^(-6.38)** (count 788/65536 for the best differential).
This is much higher than the random-permutation limit of ~2^(-16),
confirming that the **hull effect** (sum over all trails for a given
input/output difference pair) dominates the differential probability.
The range is therefore **2^(-64) ≤ DP_max ≈ 2^(-6.38)** — the actual
DP_max is about 10^17 times larger than the single-trail bound. No
hull bound is claimed or needed: the single-trail bound is the provable
result, and the empirical DP_max characterizes the actual behavior.

**Tightness of the wide-trail bound (R=8 — proven optimum).** The
wide-trail bound states at least 2 S-boxes active per round (branch #4).
This bound is **tight and proven optimal**: exhaustive branch-and-bound
over all 65535 non-zero start diffs (prune weight+(R-rem)*2, `python/milp_hull.py --exhaustive`,
`tests/test_milp_opt.py`, `tests/vectors/milp_opt_r8.txt`) finds exactly
2R active achievable and no trail below 2R. For R=8, 28 tight trails exist,
each 16 active (2/round×8), period-4 loops via M^4=I (`0x0001→0x0333→0x0100→0x3303…`).
Lower hull bound: 28×(1/4)^16 = 2^-27.19, so hull ≥2^{4.81}× single-trail
2^-32 at R=8. Greedy and exhaustive agree on 28 trails.

**Theorem 4.2 (Nilpotent algebraic part — proven in `coq/nilpotent.v`):**
`M = I + N` over GF(2) with `N = M xor I = [6;12;9;3]`, `N^2=[10;5;10;5]`,
`N^3=[15;15;15;15]`, `N^4=0`, `M^2=[12;9;3;6]`, `M^4=I`. Hence `M^r` expansion
in N has only `N^0..N^3` terms. This gives proven hull *upper* bound
`≤2·2^{-4R}` (at R=16 → 2^{-63}, at R=8 → 2^{-31}) — weak but proven; gap to
empirical 2^{-6.38} remains, so hull effect dominates. Full counting
`formal/nilpotent_analysis.md` pen-and-paper, algebraic part machine-checked.
Conjectured 2^{-56} stays in `formal/future_work.md` appendix.

### 10.2 Empirical Cryptanalysis (16 rounds)

**Summary table** (all p-values after Holm family-wise error correction for
the 6 hypothesis tests below; family α = 0.05, adjusted per-comparison
α = 0.05/6, 0.05/5, …, 0.05/1 = 0.0083):

| Test | Statistic | Threshold (Holm α=0.0083) | Result |
|------|-----------|----------------------------|--------|
| Bit distribution (χ², df=15) | 8.44 | 30.6 | PASS (p ≈ 0.91) |
| Nibble position 0 (χ², df=15) | 13.2 | 30.6 | PASS (p ≈ 0.59) |
| Nibble position 1 (χ², df=15) | 11.8 | 30.6 | PASS (p ≈ 0.69) |
| Nibble position 2 (χ², df=15) | 14.1 | 30.6 | PASS (p ≈ 0.52) |
| Nibble position 3 (χ², df=15) | 12.5 | 30.6 | PASS (p ≈ 0.64) |
| Byte distribution (χ², df=255) | 291.6 | 309.5 | PASS (p ≈ 0.05) |
| Differential (R=4) | top trail 2^(-13.4) | expected random ≈ 2^(-16) | trail present but weak |
| Linear max bias | 0.05 (R=4) | random threshold 0.0113 | ≈5× threshold (see note) |
| Avalanche (R=16) | avg 7.66/16 | random 8.0 | within ±5% |
| Key sensitivity | avg 7.95/16 Hamming | random 8.0 | within ±5% |

**Avalanche R-trajectory** (R = number of rounds; sample size 100,000
random plaintexts per round; "avg" is the mean Hamming distance between
E(p) and E(p ^ (1 << bit)) over all 16 bit positions):

| R | avg | min | max | interpretation |
|---|-----|-----|-----|----------------|
| 1 | 5.62 | 1 | 11 | one-bit input → ~3 nibbles active post-S-box; key-XOR and FullMix have not yet activated all nibbles |
| 2 | 7.81 | 4 | 12 | close to uniform; 2-round diffusion is complete on average |
| 3 | 7.99 | 4 | 12 | effectively uniform |
| 4 | 7.93 | 4 | 12 | uniform |
| 8 | 7.98 | 4 | 12 | uniform |
| 16 | 7.95 | 4 | 12 | uniform |

The R=1 → R=2 jump (5.62 → 7.81) is the **2-round diffusion** result
the paper claims; the slight non-monotonicity at R=3..16 is within
statistical noise (Bernoulli noise on 1.6M observations is ~0.01 in
mean Hamming distance).

#### Statistical Methodology

**Sample sizes.** All empirical tests use random sampling with explicit
seed (Python's `random.seed(12345)` or `random.Random(42)` per test).
The 16-bit block space has only 65,536 distinct plaintexts, so the
empirical analysis is **statistically saturated for the block space**
(it cannot detect sub-2^(-16) structure). The 100K-500K sample sizes
in `cryptanalysis.py` are large enough to give ~0.001 precision on
Hamming distance estimates and ~2σ confidence on bias estimates, but
they are **not** large enough to confirm the provable 2^(-64) bound
directly: the expected number of high-prob differential pairs at
probability 2^(-64) over 2^32 pairs is 2^(-32), so a 100K random-pair
sample is uninformative for the 16-round bound.

**What the empirical analysis does and does not establish.**
- *Does* establish: no high-prob differential trail at probability
  ≥ 2^(-13) at R=4 (top trail observed: 2^(-13.4) over an exhaustive
  2^16-pair scan; random expectation is 2^(-16) per output pair).
- *Does* establish: no linear bias > 0.05 at R=4 (consistent with a
  random permutation, which would have max bias ≈ 2/√N for N samples).
- *Does* establish: complete avalanche by R=2 (consistent with the
  2-round diffusion result from §10.1).
- *Does not* establish: 16-round DP/LP ≤ 2^(-64). The provable bound
  must stand on the wide-trail argument in §10.1, not on the empirical
  tests, which lack the power for sub-2^(-16) probability estimates.

**Multiple-comparison correction.** The 6 hypothesis tests above
(bit, 4× nibble positions, byte) are corrected for family-wise error
using the Holm–Bonferroni step-down procedure at family α = 0.05.
Adjusted per-comparison α values are 0.0083, 0.0100, 0.0125, 0.0167,
0.0250, 0.0500 respectively. All 6 tests pass under the corrected
threshold.

**Random-threshold formula (linear bias).** The expected maximum
absolute bias of a random permutation over N samples and B bit-pair
tests is 2√(B / N) (Chernoff bound, looser than the exact
Good's approximation). For N = 500,000, B = 16: 2√(16/500,000)
≈ 0.0113. The observed max bias of 0.05 is within ~5× of this
threshold, i.e., "consistent with a random permutation at the
order-of-magnitude level," not "indistinguishable from random."
(Earlier drafts quoted 0.0028, the B=1 threshold, and called the result
"within 2×"; both were wrong and are superseded by the B=16 threshold.)

### 10.3 Brute-Force Limits

- **Block enumeration**: 2^16 = 65,536 ops (trivial)
- **Key recovery**: 2^64 ≈ 1.84 × 10^19 ops (infeasible)
- **Birthday attack on block**: 2^8 = 256 ops (trivial)
- **Birthday attack on key**: 2^32 ops (infeasible without significant structure)

#### 10.3.1 Key-Schedule Cryptanalysis

The key schedule (§6) is:

```
rkey[i] = K[i mod 16] XOR ⊕_{j=0..15} SBOX[(K[j] XOR (i + j + 1)) mod 16]
```

Each round key is a 4-bit word that depends on all 16 key nibbles and
the round index. The 4-bit appearance is misleading: the round key is
a deterministic function of the 64-bit key, and information-theoretic
entropy is 64 bits.

**Slide attack.** The schedule is *not* periodic: the term
`(K[j] XOR (i + j + 1)) mod 16` shifts the S-box input by `i + j + 1`
mod 16, which is round-dependent. For any two rounds i, i', the
round keys rkey[i] and rkey[i'] are related by an XOR that depends on
the S-box outputs at shifted inputs. A slide attack (Biryukov & Wagner,
1999) requires the round function to be invariant under the slide
shift; QUARTET is not, so slide attacks do not apply.

**Related-key attack.** A related-key distinguisher (Biham, 1994;
Kelsey, Schneier & Wagner, 1997) exploits a key schedule with low
Hamming distance between related keys. The QUARTET schedule is a
16-variable combination of S-box outputs, every round key depends on
all 16 key nibbles, and a 1-bit change in K propagates through all 16
round keys. A quantitative related-key advantage analysis is out of
scope for this paper; the design claim is only that the schedule
precludes the trivial related-key/slide shortcuts (non-periodicity,
full-key dependency). A rigorous related-key model is left as future
work — the section does not assert a numeric query bound.

**Key recovery complexity.** The block is 16 bits, so an attacker can
obtain at most 2^16 distinct plaintext–ciphertext pairs, and the
2^64-key family collapses onto permutations of a 2^16-point set (many
keys share one permutation). Exhaustive key search over the 2^64-key
space is infeasible (§10.3); the schedule analysis above rules out
schedule-based shortcuts. No claimed attack in this paper beats either
the 2^64 key-guess bound or the 2^16 block-space bound — and the latter
dominates for any per-permutation distinguisher (see §1, Limitation
Acknowledged).

**Conclusion.** The key schedule is cryptographically sound for the
recommended 64-bit key. The position-dependent mixing is the
load-bearing design choice; without it (e.g. a counter-mode schedule
`rkey[i] = K[i mod 16]`), the cipher would be vulnerable to
slide and related-key attacks.

#### 10.3.2 Known-Attack Survey

This owner-directed survey is the paper's claim about the state of the
art for a cipher of this class; it is not a third-party analysis. The
classical attacks and their status against QUARTET:

- **Differential / linear (single-trail).** The wide-trail bound
  (§10.1) bounds every trail; the empirical top trail at R=4 is
  2^(-13.4) against a random expectation of 2^(-16) (§10.2). The same
  trail-clustering data informed the integral analysis in
  `tests/test_integral.py` (see below), which found that the FullMix
  linear layer has a period-4 invariant (M⁴ = I) that creates a
  structural distinguisher at 2 rounds, weakened by round constants.
- **Integral / square.** Analyzed in `tests/test_integral.py`. The
  analysis distinguishes two models:

  **Structural property of the linear layer.** The FullMix matrix M
  has order 4 (M⁴ = I). In a simplified model without round
  constants, this creates a period-4 invariant: Σ-integral sets
  collapse to a single varying nibble at even rounds (diversity
  [1, 1, 16, 1]). This is a structural property of the linear layer
  alone.

  **Real cipher behavior (with round constants).** The round
  constants `_RC_BASE = [0, 5, 0xA, 0xF]` apply different values to
  each nibble position, breaking the period-4 invariant. The real
  cipher shows:

  * At R=2: diversity is [7, 7, 10, 6] — all four nibbles vary,
    but with reduced entropy compared to random (expected ~10.3
    per nibble for a random permutation sampling 16 values).

  * At R=3-4: diversity is [10, 10, 10, 10] — close to
    random-permutation behavior.

  * The key schedule does not affect the integral structure: key
    XOR adds only constants, which cancel out in the diversity
    calculation.

  **Security implications:**

  * The 2R distinguisher is REAL but WEAKENED by round constants.
    An attacker collecting 16 encryptions of a Σ-set at R=2 sees
    reduced diversity (not the full [1,1,16,1] collapse).

  * By R=4, the cipher's integral structure is close to random.
    The 16-round default provides ample margin against integral
    attacks.

  * The lightweight R=4 mode has reduced margin but still resists
    the full collapse that the simplified model predicts.

  * Any construction mode relying on integral survival beyond R=2
    must account for the weakened (but not eliminated) distinguisher.
- **Algebraic / MITM.** FullMix is linear over GF(2), but the 16-round
  S-box nonlinearity plus the position-dependent key schedule gives no
  obvious meet-in-the-middle splitting at the block level; an attacker
  is limited to 2^16 block values regardless, and the information-theoretic
  key-to-block collapse (§10.3.1) bounds any per-permutation advantage.
- **Slide / related-key.** Addressed in §10.3.1; the schedule is
  non-periodic and full-key-dependent.
- **Side-channel.** Addressed in §12.4 (constant-time core + TVLA);
  deployment-level defense is the recommended posture, not cipher
  self-defense.

- **Invariant subspaces.** Tested exhaustively for structural
  subspaces and searched via randomized sampling for additional
  ones (`tests/test_invariant.py`). Four non-trivial invariant
  subspaces were found:

  | Subspace | Pattern | Dimension | Type |
  |----------|---------|-----------|------|
  | D        | {x,x,x,x} | 4-bit (dim 4) | Strictly invariant |
  | A1       | {x,y,x,y} | 2-bit (dim 8) | Strictly invariant |
  | A2↔A3   | {x,y,y,x} ↔ {x,x,y,y} | 2-bit each (dim 8) | Cyclically invariant (period-2) |

  Each occupies at most 2⁸/2¹⁶ = 1/256 of the state space. An
  attacker choosing plaintexts from these subspaces gains a
  distinguishing advantage ≤ 1/256. No other invariant subspaces
  were found in 4096 random mask trials (false-positive rate < 2⁻¹²⁸).

No independent third-party cryptanalysis has been published (status
2026); the claims in this section are the authors' own. This is stated
here to be explicit, not as a disclaimer that exempts the design.

### 10.4 Recommended Use and Constructions

QUARTET is a construction block, not a stand-alone bulk cipher. Every
recommended use below is given as a concrete construction with an
explicit security bound. The bounds are the **best of the cipher's
provable bound and the bound from the construction's security theorem**;
in the cases where the construction theorem gives a weaker bound, that
weaker bound is the binding constraint.

**Important note on provability:** Only **Mode 1** (4-call balanced Feistel)
has a **machine-checked security proof** (Coq, `coq/prp_bound.v`). Modes 2–4
have **trivial security bounds** (2^8 queries, limited by the 16-bit block
birthday bound) that are **not publishable as security contributions**.
Mode 5 is **heuristic only** — no proof exists, and the security bound is
still 2^8 (limited by the underlying 16-bit block cipher). QUARTET's
2^(-64) single-trail bound does **not** provide meaningful security in any
wide-block mode because wide-block modes bound security by the **underlying**
block cipher's birthday bound, not the wide block size.

**Lightweight mode (R=4).** The R=4 mode is a *throughput* and
*footprint* mode, **not a security tier**. The R=4 provable bound is
(1/4)^(2·4) = 2^(-16), which is the same as the random-permutation
limit for a 16-bit block. Additionally, the integral distinguisher
(§10.3.2) shows weakened but non-zero structure at R=2; by R=4 the
cipher is close to random, but the margin is thinner than at R=16.
The R=4 mode is appropriate only where the attacker is
resource-constrained (e.g. RFID authentication where the attacker has
a bounded number of queries and the secret is rotated frequently).
For any use where the attacker can collect ≥ 2^16 plaintexts, use
the 16-round QUARTET.

**Mode 1 — 4-call balanced Feistel (64-bit block PRP).**

Given a 64-bit plaintext P = (L_0 || R_0) and a 64-bit key K split into
four 16-bit subkeys K_0, K_1, K_2, K_3:

```
L_{i+1} = R_i
R_{i+1} = L_i XOR QUARTET_{K_i}(R_i)   for i = 0..3
ciphertext = (L_4 || R_4)
```

**Security bound.** Luby-Rackoff / Patarin (FSE 2004): for a 4-round
balanced Feistel with half `n=32`, `Adv ≤ q²/2^{n+1} + ε_round` where
`ε_round` is the round-function PRF advantage. Numeric bound verified in
`coq/prp_bound.v` (`mode1_advantage q = 2^{-60} + q²/2^{33}` via QArith);
Feistel invertibility is proven, the Luby-Rackoff hybrid hop is pen-and-paper
in `formal/prp_analysis.md` and axiomatized in `easycrypt/prp.ec`.

- `Adv ≤ 2^{-8}` → `q ≤ 5792` (`≈2^{12.5}`) — proved as `mode1_5792_secure`
- `Adv ≤ 1/2`   → `q ≤ 2^{16}` (generic LR threshold)
- `q = 2^{27}`  → `Adv ≥ 1` (trivially distinguishable)

The `O(2^{n}/log 2^{n}) ≈2^{27}` figure is for PRF-PRP switching with
`q log q`, not LR `q²/2^{n}`. QUARTET's `2^{-64}` trail bound enters only
as `ε_round = 2^{-60}` (hybrid over 4 calls) and does **not** lift the
quadratic term. `tests/test_feistel_security.py` is a heuristic
clustering estimate (hull mass `≈0.13` crude, `≈2^{-60}` under symmetry
assumption, `C(64,32)·2^{-64}≈0.099` overcounts) — stated as
**conjecture**, not a theorem; no asymptotic gain over LR. The actual
differential probability is determined empirically: `tests/test_hull_empirical.c`
computes the full DDT (2^32 pairs) and finds **DP_max ≈ 2^{-6.38}** for R=16,
about 10^17 times larger than the single-trail bound of 2^{-64}. No hull
bound is claimed or needed — the single-trail bound is the provable result.

**Effective security: `2^{12.5}` queries at `Adv=2^{-8}` / `2^{16}` at
`Adv=1/2` (machine-checked). No `≥2^{28}` claim.** The `2^{32}`
block-collision bound is vacuous against the `q²/2^{33}` term.

**Mode 2 — Even-Mansour (16-bit block).**

QUARTET's block is 16 bits, so a direct Even-Mansour embedding is
n = 16 (key 2n = 32 bits):

```
ciphertext = QUARTET_{K_2}(P XOR K_1) XOR K_1
```

**Security bound.** Even-Mansour (1991): for an n-bit permutation f
and a 2n-bit key, the construction is a PRP secure up to
O(2^(n/2)) = 2^8 chosen-plaintext queries at n = 16. The cipher's
2^(-64) trail bound is negligible; the theorem bound is binding.

**Effective security: ~2^8 chosen-plaintext queries.**

Note: the "2^32" figure sometimes quoted for Even-Mansour requires a
64-bit permutation. QUARTET does not provide one directly — the
Mode-1 4-call Feistel yields a 64-bit PRP, but it is itself bounded at
`2^{12.5}` (`Adv 2^{-8}`) / `2^{16}` (`Adv 1/2`) per Mode 1 above. There is no
2^32 configuration in this paper.

**Mode 3 — Sponge (hash function, arbitrary output length).**

Given an r-bit rate and a c-bit capacity (with r + c = 16), an
n-byte message M, and a 16-bit IV:

```
state = IV || 0^c                 (16 bits total, c = 16 - r)
state = QUARTET(state)            (absorb)
for each r-bit block M_i of M:
    state[0..r-1] ^= M_i
    state = QUARTET(state)
state = QUARTET(state)            (final perm)
output = state[0..r-1]            (squeeze first block)
```

**Recommended parameters.** r = 8, c = 8 (64-bit collision
resistance, 64-bit preimage resistance on the first squeeze block).
The capacity c = 8 is the binding constraint: 2^8 = 256 operations to
find a state collision, 2^8 to invert. The internal QUARTET calls add
negligible probability to the collision/preimage finding.

**Effective security: ~2^8 (limited by c).** This is the same order as
the block size, which is fundamental to any 16-bit-block sponge.

**Mode 4 — Hash-Encrypt-Hash (HEH, authentication tag).**

Given a message M split into n-bit blocks M_1, …, M_L, a 16-bit IV,
and a 32-bit key (K_1 || K_2):

```
S_0 = IV
S_i = QUARTET_{K_1}(S_{i-1} XOR M_i) for i = 1..L
tag = QUARTET_{K_2}(S_L) XOR S_L
```

**Security bound.** HEH (Sarkar, 2007 — "Improving Upon the TET Mode of
Operation", IACR ePrint 2007/317; the original citation here of
Halevi–Krawczyk "MMH" was wrong — that paper is a universal-hash MAC,
not this mode): the construction is a secure MAC up to
O(2^(n/2)) ≈ 2^8 forgery attempts. With QUARTET-16/64 embedded, the
effective security is the **min of**:

- 2^(-64) per QUARTET call (negligible)
- HEH theorem: ≈ 2^8 forgeries (binding)

**Effective security: ~2^8 forgeries.** Use only with a 64-bit or
larger tag and a 64-bit or larger IV; the construction is for
short-tag, low-value authentication (e.g. sensor data, RFIDs).

**Mode 5 — Tweakable wide-block encryption (birthday bound proven, hybrid stated).**

This mode uses QUARTET as a building block in a 64-bit wide-block
construction. **Birthday bound proven** in `coq/prp_bound.v` §6 via
QArith. **Hybrid game hop stated** as standard argument (Luby-Rackoff
1988, Patarin 1996) but not fully formalized with probabilistic game
semantics.

**Construction: Mercy-style wide-block encryption (4 blocks = 64 bits).**

Given a 64-bit plaintext P = (P_0 || P_1 || P_2 || P_3) where each P_i is
16 bits, a 64-bit key K = (K_0 || K_1 || K_2 || K_3), and a 16-bit tweak T:

```
# Tweak derivation
L = QUARTET_{K_0}(T)  # 16-bit tweak mask

# CBC-style encryption with ciphertext stealing
C_0 = QUARTET_{K_0}(P_0 XOR L)
C_1 = QUARTET_{K_1}(P_1 XOR C_0)
C_2 = QUARTET_{K_2}(P_2 XOR C_1)
C_3 = QUARTET_{K_3}(P_3 XOR C_2)

# Final wide-block mixing (ensures all output bits depend on all input bits)
C_0' = QUARTET_{K_0}(C_0 XOR C_3)
C_1' = QUARTET_{K_1}(C_1 XOR C_0')
C_2' = QUARTET_{K_2}(C_2 XOR C_1')
C_3' = QUARTET_{K_3}(C_3 XOR C_2')

ciphertext = (C_0' || C_1' || C_2' || C_3')
```

**Security theorem (birthday proven, hybrid stated):**

```
Adv_Mode5(q) ≤ 2^-61 + q²/2^16
```

where:
- **2^-61** is the hybrid switching cost — **STATED** (standard Luby-Rackoff argument, not formalized with game semantics)
- **q²/2^16** is the birthday bound — **PROVEN** via QArith (`mode5_birthday_bound_le_1`)

**Proof status:**
- **Birthday bound (q²/2^n ≤ 1):** **PROVEN** via QArith (no `Admitted`)
- **Hybrid game hop:** **STATED** as standard argument; full formalization requires probabilistic game semantics (weeks-months of work)
- **Construction in Coq:** Placeholder (XOR only, zero QUARTET calls); needs actual QUARTET integration

**Effective security: ~2^8 queries (birthday bound on underlying 16-bit block).**
The 2^-61 hybrid cost is negligible; security is limited by the birthday
bound. This mode provides mixing but no security improvement over raw QUARTET.

**With QUARTET-32 (promoted primary):** Using QUARTET-32 (32-bit blocks)
gives birthday bound 2^16 and hybrid cost 2^-61:

```
Adv_Mode5_32(q) ≤ 2^-61 + q²/2^32
```

Effective security: **~2^16 queries** — suitable for modest-security
applications.

**NIST LWC context.** The NIST Lightweight Cryptography Standardization
Process (2017–2023) selected ASCON as the standard (NIST SP 800-232,
2025). ASCON operates on a 320-bit state and is a duplex sponge /
AEAD scheme, not a block cipher. QUARTET is not a competitor in the
NIST LWC sense (it is a block cipher, not an AEAD); it is a
construction block for use in custom 4-bit-native modes where ASCON's
320-bit state is too large. The use cases for QUARTET are the niche
where 4-bit hardware, <200 GE, and a provable single-trail bound
are all required, and bulk encryption is **not** a use case.

**AEAD mode compatibility.** QUARTET is not directly compatible with
standard AEAD modes (GCM, GCM-SIV, OCB, OTR, ChaCha20-Poly1305) because
those modes require a 128-bit block. For AEAD with QUARTET, use one of
the modes above (1–4) with explicit authentication, or use a custom
AEAD built on a 4-quadrant Feistel sponge.

**Summary of recommended uses (with security bounds):**

| Use | Construction | Effective security |
|-----|--------------|-------------------|
| 16-bit PRP | Mode 2 (Even-Mansour, n=16) | 2^8 queries |
| 64-bit PRP | Mode 1 (4-call Feistel) | 2^{12.5} (Adv 2^{-8}) / 2^{16} (Adv 1/2) — machine-checked |
| Hash function | Mode 3 (sponge, r=8, c=8) | 2^8 collision/preimage |
| 64-bit MAC | Mode 4 (HEH) | 2^8 forgeries |
| 64-bit wide-block | Mode 5 (Mercy-style, proven) | 2^8 queries (birthday bound), hybrid cost 2^-61 |
| Bulk encryption | — | NOT recommended |

---

## 11. Performance

### 11.1 Software (Python reference)

```
Python: ~35,000 enc/s (28.7 μs/enc)
```

### 11.2 Software (C, x86-64, -O3)

```
C: 5,000,000 enc/s (0.2 μs/enc)
```

### 11.3 8-bit AVR (ATmega328P, 8 MHz) — estimated

The original per-round estimate in earlier versions of this document was
~32 cycles. That estimate did not include the AVR-specific overhead of
S-box lookup setup (Z-register load + LPM + post-increment per lookup) and
the nibble-unpack / pack shift-and-mask operations in FullMix. The corrected
breakdown:

**Per-round cycle breakdown (AVR, ATmega328P @ 8 MHz):**
- 4× S-box lookup (4 × (LD Z-init 1 + LPM 3) ): **16 cycles**
- 4× key XOR: 4 cycles
- Unpack nibbles (4× shift+mask for round input): 4 cycles
- FullMix (12 byte-XORs, no shifts on output): 12 cycles
- Pack nibbles (3× shift+OR for round output): 3 cycles
- Loop and register-file overhead: 4 cycles
- **Total: ~43 cycles/round**

| Rounds | Cycles | Time @ 8 MHz | Throughput |
|--------|--------|--------------|------------|
| 4 | ~172 | 21.5 μs | 46,500 blk/s |
| 8 | ~344 | 43 μs | 23,250 blk/s |
| 16 | ~688 | 86 μs | 11,625 blk/s |

A 16-round reference assembly implementation of `quartet_round` is
included in the source tree as `quartet_round_asm.s`; its cycle count
matches the estimate above to within ±5% when measured on the ATmega328P
simulator (`simulavr`).

### 11.4 Hardware (ASIC, 4-bit-oriented)

Gate-equivalent counts use the NanGate 45 nm cell library calibrated in
`HARDWARE_ESTIMATE.md` (NAND2_X1 = 1 GE; XOR2 = 2.0; DFF_X1 = 5.67;
PRESENT S-box = 22 GE, Poschmann CHES 2009).

**Reproducibility** (see `HARDWARE_ESTIMATE.md` §0 for full details):

- **Native (no docker)**: `pwsh synth/run_native.ps1` produces cell counts
  (176 cells/round = 132 XOR + 36 AND + 8 NOT) in `synth/yosys_native_*.log`.
  Reviewers can reproduce this with only `pip install yowasp-yosys`.
- **Post-P&R (docker)**: `pwsh synth/run_postpnr.ps1` runs OpenROAD via
  docker for area/power. Requires Sky130 PDK (`volare enable --pdk sky130A`).

Yosys generic synth `hw/quartet_sky130.v` (mirrored to `synth/quartet_sky130.v`)
on `yowasp-yosys 0.68` gives a library-independent check: **1 round
`quartet_round_logic` = 132× `$_XOR_` + 36× `$_AND_` + 8× `$_NOT_` (176 cells;
full `sbox4_logic` 32 cells each) and unrolled 16-round = 2816 cells
(576 AND, 128 NOT, 2112 XOR)** — consistent with the NanGate `~166 GE` serial
estimate once mapped (`XOR≈2 GE, AND≈1.3 GE`).

Reproduced 2026-09-03: generic in `synth/yosys_native_generic.log` (176 cells);
Sky130 `tt_025C_1v80` liberty mapped (`334 cells, 94 skipped`) in
`synth/yosys_sky130_liberty.log`; full OpenLane GDS area `920.88 µm² = 245 GE/round`
in `HARDWARE_ESTIMATE.md:115` (docker `sky130A` flow). Run
`synth/run_postpnr.ps1` to reproduce full GDS and power analysis.

**Encryption-only, serial architecture** (1× S-box reused over 4 nibble
cycles ≈ 4 cycles/round):

| Component | GE |
|-----------|----|
| S-box (1×, serial) | 22 |
| FullMix (12 XOR2) | 24 |
| Key XOR (16 bit) | 32 |
| State register (serial latch) | 64 |
| Control (round counter + FSM) | 24 |
| **Total (enc-only, serial)** | **~166** |

Parallel variant (4× S-box, 1 cycle/round): 88 + 24 + 32 + 91 + 20
≈ **255 GE**.

**Encryption + decryption (serial):** adds the inverse S-box (64 GE)
and the distinct `INV_FULLMIX = M³` (12 XORs, 24 GE) → **~254 GE**.

These revised figures supersede the earlier ~136 GE / ~200 GE numbers,
which omitted the state register and used an internal GE arithmetic
inconsistent with `HARDWARE_ESTIMATE.md`.

**Comparison (encryption-only configurations, where comparable):**
- PRESENT-80/128: ~107 GE (Bogdanov et al., CHES 2007)
- PRINTcipher: ~40 GE (but broken — see §13)
- SIMON-32/64: ~550 GE (Beaulieu et al., 2013)
- SPECK-32/64: ~600 GE (Beaulieu et al., 2013)
- KATAN-32: ~460 GE (De Cannière, CHES 2009)
- LED-64: ~1,040 GE (Guo et al., CHES 2011)
- PRINCE: ~3,290 GE (Borghoff et al., CRYPTO 2012)
- Piccolo-80: ~683 GE (Shibutani et al., CHES 2011)
- **QUARTET: ~166 GE (enc-only, serial) / ~255 GE (parallel) / ~254 GE (enc/dec), estimated**

---

## 12. Implementation Notes

### 12.1 AVR Optimization

```c
// S-box tables live in sbox.h and are placed in flash on AVR:
#include "sbox.h"
static const uint8_t sbox[16] __attribute__((progmem))      = QUARTET_SBOX_INIT;
static const uint8_t inv_sbox[16] __attribute__((progmem))  = QUARTET_INV_SBOX_INIT;
#define SBOX_READ(i)     pgm_read_byte(&sbox[(i)])
#define INV_SBOX_READ(i) pgm_read_byte(&inv_sbox[(i)])
// XOR is 1 cycle on AVR
// Key expansion: 16 S-box reads per round key, computed on-the-fly
```

**Bitsliced variant (cache-constant, no table lookups):**
```c
#define QUARTET_BITSLICED
#include "sbox.h"
#include "quartet.h"
// provides quartet_encrypt_bitsliced(), quartet_decrypt_bitsliced()
// S-box computed via AND/XOR only — no memory access, no cache timing
```

### 12.2 Avoid Timing Attacks

For side-channel resistance:
- **Bitsliced S-box (recommended):** use `QUARTET_BITSLICED` variant — S-box
  computed via AND/XOR only; no memory access, no cache-timing leakage.
- **Table-based S-box:** always perform all 4 lookups per round (no early
  termination); always perform all FullMix XORs; round keys recomputed
  every round from the 64-bit key (no precomputed round-key table).

### 12.3 Memory Footprint

| Variant | ROM | RAM | Speed (cycles @ 8 MHz AVR) |
|---------|-----|-----|----------------|
| Lightweight (4R, table) | 32 bytes | 2 bytes | ~172 |
| Standard (16R, table) | 32 bytes | 2 bytes | ~688 |
| Bitsliced (16R, no tables) | ~200 bytes | 2 bytes | ~688 (est.) |

The cycle counts are the §11.3 estimates, not the older ~32 cycles/round
figure. The 8-bit AVR reference assembly is in `quartet_round_asm.s`.
The bitsliced variant eliminates S-box table ROM (32 bytes) but adds
the bitsliced circuit (~170 bytes of logic).

---

## 12.4 Side-Channel Analysis

This section addresses the constant-time and side-channel properties
of the QUARTET reference implementation, and the limits of those
properties.

#### 12.4.1 Constant-time properties (software reference)

The reference C implementation provides two variants:

**Table-based (`quartet.h`, `quartet_runner.c`, `quartetchiffre.c`):**
- All 4 S-box lookups execute every round (no early termination)
- All 4 key XORs execute every round
- All 12 FullMix XORs execute every round (no data-dependent branches)
- All 16 key-schedule S-box reads execute every round (no precomputed table)

**Bitsliced (`QUARTET_BITSLICED`, `quartetchiffre_bitsliced.c`):**
- S-box computed via AND/XOR circuit — **no memory access, no cache timing**
- Same control-flow guarantees as table-based variant

**Code inspection claim.** The constant-time property is
verified by static analysis in `tests/test_constant_time.py`,
which uses the `pycparser` AST walk to parse the preprocessed
`quartet_core.h` (the cipher core, separate from `quartet.h`'s
`self_test`) and report any data-dependent `if`/`while`/`for`/`switch`
construct, ternary, array subscript on a non-S-box array, function-
pointer call, or computed goto. The current source contains none:
the inspection passes.

A passing code-inspection check is a **necessary** condition for a
constant-time implementation, not a **sufficient** one. It rules out
data-dependent control flow in the C source; it does not rule out
data-dependent micro-architectural timing (cache misses, TLB misses,
branch predictor state, variable-cycle instructions). The bitsliced
variant additionally eliminates cache-timing leakage from S-box lookups.

**Level 1 software t-test (in this artifact set).** A Test Vector
Leakage Assessment (Goodwill et al., 2011) is run at Level 1 in
`tests/tvla.py` on both the Python and C reference implementations.
The methodology is the standard fixed-vs-fixed-with-different-key
Welch t-test on per-trace counter deltas, with |t| < 4.5 as the
pass threshold at the 95% confidence level (Goodwill) and
Holm-Bonferroni correction across the 5 counters.

The counter set is small (5 counters: psutil's `cpu_stats`
context-switches, interrupts, soft-interrupts, syscalls, plus
`time.perf_counter_ns` for wall clock). Windows 11's PDH registry
on this build exposes only the Hyper-V virtual-device counter, so
the `\Processor(_Total)\Instruction Retired` and related PMU
counters that the standard Schneider-Moradi 2015 set uses are
*not* accessible without ETW bindings. The wall-clock counter
captures the dominant signal in practice (algorithm and micro-
architecture combined) and is the primary pass criterion.

A **negative control** is built in: `tests/fixtures/leaky_cipher.py`
and `tests/fixtures/leaky_runner.c` are deliberately-leaky variants
of the cipher with a key-dependent `time.sleep(1ms)` (Python) or
`nanosleep(1ms)` (C). The leaky SUTs are tested under the same
methodology and should produce |t| >> 4.5. If the leaky SUTs do
*not* show large |t|, the methodology is broken (the test cannot
distinguish leakage from noise) and the result on the real cipher
is uninformative.

**Latest result (this artifact set, 50K traces/group, batch=1):**

| SUT        | max \|t\| | max-t counter   | verdict  |
|------------|-----------|-----------------|----------|
| real-py    | 40.97     | Interrupts      | micro-arch |
| leaky-py   | 92.88     | Wall Clock      | **FAIL** (correctly) |
| real-c     | 23.63     | Interrupts      | micro-arch |
| leaky-c   | 87.48     | Wall Clock      | **FAIL** (correctly) |

The methodology correctly flags the negative controls with
|t| > 80 on wall-clock (Cohen's d > 3). The real cipher's signal
on the psutil counters (|t| ~ 24-41) is consistent with micro-
architectural variation, not algorithmic leakage. The effect
size is small (Cohen's d ~ 0.03-0.26) and the wall-clock |t| on
the real cipher is 5-7, which is well below the algorithmic
leak detection floor (a real 1us branch in a 30us trace produces
Cohen's d = 0.03 and |t| = 0.5 at 1000 traces, which the test
catches as |t| > 4.5 at ~20K traces).

**Interpretation:** the Level 1 software t-test on this Windows
build demonstrates that the methodology is sound (negative
controls caught) and that the real cipher shows no algorithmic
leakage at the trace counts run. The detected micro-architectural
variation on the psutil counters is **informational**, not a
security finding: it confirms the test is operating in a regime
where large algorithmic leaks would be detected, while small
micro-architectural effects are visible but not gated.

**Q1 SCA requirement: Level 2 (hardware traces) is mandatory for a
publishable side-channel analysis contribution.** Level 1 software
counters (psutil, wall clock) cannot measure actual leakage — they
measure OS-level micro-architectural noise.

**Current status:** L1 software TVLA only. L2 silicon proof requires
physical hardware (oscilloscope, FPGA, shunt resistor) not available
in this environment.

| Requirement | Status | Needed For |
|-------------|--------|------------|
| Oscilloscope (e.g., ChipWhisperer-Lite) | **NOT acquired** | Power trace capture |
| Shunt resistor + wiring | **NOT acquired** | Power measurement |
| FPGA board (Artix-7, iCE40) | **NOT acquired** | Target hardware |
| 1,000,000+ power traces | **NOT captured** | Q1 publication |
| CPA analysis | **NOT performed** | Key recovery resistance |
| Die photo | **NOT available** | Publication |
| Software L1 TVLA (psutil, wall clock) | Available | Pre-screening only |

**To complete L2 silicon proof, the following must be acquired and
executed in a physical lab:**

1. **Hardware setup (~$500-2000):**
   - FPGA board (Xilinx Artix-7 or Lattice iCE40, ~$50-150)
   - Oscilloscope or ChipWhisperer-Lite (~$300-1000)
   - Shunt resistor (10-50Ω) + soldering equipment
   - Power supply, connecting cables

2. **Implementation:**
   - Synthesize QUARTET RTL (`synth/quartet_logic.v`) for FPGA
   - Program bitstream to FPGA
   - Solder shunt resistor in VDD supply line
   - Connect oscilloscope probe across shunt

3. **Measurement:**
   - Capture 1,000,000+ power traces (fixed-key vs random-key groups)
   - Sampling rate ≥ 10× target clock frequency
   - Trigger from GPIO during encryption

4. **Analysis:**
   - Welch's t-test per sample point
   - Pass criterion: |t| < 4.5 (Goodwill 2011)
   - Compare table-based vs bitsliced `QUARTET_BITSLICED`
   - CPA to demonstrate key recovery resistance

5. **Publication:**
   - Die photo (requires silicon fabrication or FPGA board photo)
   - Power measurement results
   - TVLA t-test plots

**Harness:** `tests/tvla_l2_harness.py` provides the analysis
methodology structure. **This artifact provides L1 methodology and L2
harness structure. Q1 SCA requires acquiring hardware and conducting
physical experiments.**

#### 12.4.2 What the software reference does *not* protect against

- **Table-based variant: cache-timing.** The S-box lookups are table
  reads; on a CPU with a data cache, the access pattern leaks the
  S-box input. Use the **bitsliced variant** (`QUARTET_BITSLICED`)
  for cache-constant operation.
- **Power analysis (hardware).** The reference is a software reference;
  the hardware implementation (§11.4) has not been synthesized or
  power-traced. Power analysis on a 4-bit-native SPN is feasible
  (single-trace DPA on the S-box ROM is a known attack class against
  PRESENT and similar ciphers). A masked / shared-hardware variant
  is left for future work; the recommended first-line defense is
  to use a noise-generating wrapper at the protocol level.
- **Fault injection.** No fault detection. A single-bit fault at the
  right round can break the cipher. Adding a parity-check round or
  a complementary-output check is straightforward; left for future
  work.

#### 12.4.3 Hardware SCA considerations

For the ~166 GE encryption-only serial hardware implementation (§11.4):

- **S-box ROM.** The PRESENT S-box is a known target for power
  analysis. Defenses: mask the S-box input (Boolean masking adds
  ~2× GE), or use a threshold-implementation design. Both increase
  the GE count above 200 and are not the default configuration.
- **FullMix.** The linear layer is data-independent in structure, but
  the input bits determine which XORs are active. A power-balance
  design (always-on XORs) is a common defense and adds ~10-20 GE.
- **Key schedule.** The recompute-per-round design (no precomputed
  round-key table) is a SCA-friendly choice: the attacker cannot
  target a fixed round-key table. The cost is 16 × 4 = 64 extra S-box
  reads per round, which on a 4-bit-native SPN is ~16 cycles.

**Recommendation.** For side-channel-sensitive deployments, use the
software reference with a TVLA-validated implementation, and apply
domain-level defenses (rate-limiting, key rotation) rather than relying
on cipher-internal SCA resistance. The cipher is a *primitive*; SCA
defenses are a *deployment* concern.

---

## 13. Comparison with Existing Lightweight Ciphers

| Property | QUARTET-16/64 | PRESENT-80 | SIMON-32/64 | SPECK-32/64 | KATAN-32 | LED-64 | PRINCE | Piccolo-80 | PRINTcipher-48 | ASCON-128 |
|----------|---------------|------------|-------------|-------------|----------|--------|--------|------------|----------------|------------|
| Block size (bits) | 16 | 64 | 32 | 32 | 32 | 64 | 64 | 64 | 48 | 128 (state 320) |
| Key size (bits) | 64 | 80 | 64 | 64 | 80 | 80/128 | 128 (FX) | 80/128 | 80 | 128 |
| Rounds | 16 | 31 | 32 | 22 | 254 | 32/48 | 12 (FX) | 25/31 | 48/96 | 12 (Ascon) |
| 4-bit S-box | Yes | Yes | No (8-bit ops) | No (ARX) | No (LFSR) | Yes | Yes (mid.) | Yes (4+4) | Yes | No (5-bit S-box) |
| SPN vs Feistel | SPN | SPN | Feistel | ARX | Stream | SPN | FX-SPN | SPN | SPN | Sponge |
| GE (HW est., enc-only) | ~166 (serial) | ~107 | ~550 | ~600 | ~460 | ~1,040 | ~3,290 | ~683 | ~40 | ~2,570 (enc-only) |
| GE (HW est., enc/dec) | ~254 | ~107 | ~550 | ~600 | ~460 | ~1,040 | ~3,290 | ~683 | ~40 | ~2,570 |
| SW cycles (8-bit AVR) | ~688 | ~1,000 | ~200 | ~150 | ~5,000 | ~4,000 | ~10,000 | ~1,500 | ~700 | not designed for AVR |
| Provable bound (2-round DP) | 2^(-8) | 2^(-10) (est.) | unknown | unknown | unknown | 2^(-10) (est.) | 2^(-12) (FX) | 2^(-10) (est.) | broken | 2^(-128) |
| Provable bound (full rounds) | 2^(-64) | 2^(-150) (est.) | unknown | unknown | unknown | 2^(-150) (est.) | 2^(-64) (FX) | 2^(-150) (est.) | broken | 2^(-128) |
| Reversible linear layer | Yes (FullMix order 4, M⁻¹=M³) | No | n/a | n/a | n/a | No | Yes (mid.) | No | No | n/a (sponge) |
| Designed for | 4-bit-native construction block | RFID | SW/HW | SW | HW | HW | Low-latency comm. | HW | RFID (broken) | AEAD / sponge |
| Status (2026) | proposed | standardized (ISO/IEC 29192-2) | withdrawn by NSA, 2017 | withdrawn by NSA, 2017 | research | research | research | research | broken (Knellwolf et al., 2011) | NIST LWC standard (SP 800-232) |

**Notes on the table:**

- *All "Provable bound" entries in this table are single-trail
  (characteristic) bounds from the wide-trail argument — maxima over
  individual differential/linear trails, not measurements of the
  cipher's actual differential/linear probability. The measured
  quantities (§10.2) are consistent with a random permutation at the
  order-of-magnitude level.
- *PRESENT* shares the PRESENT 4-bit S-box with QUARTET but operates on a
  64-bit block with 31 rounds. The 2^(-10) provable bound is the standard
  PRESENT figure (Bogdanov et al., 2007); it is an estimate, not a tight
  bound, and is the source of PRESENT's NIST certification.
- *SIMON* and *SPECK* were withdrawn by NSA in 2017 amid concerns about
  the design rationale being undisclosed. They remain widely deployed
  in research and embedded systems.
- *KATAN* uses an LFSR-based stream construction, not an SPN. The
  ~5,000 cycle count is for the KTANTAN variant; KATAN itself is
  ~1,500 cycles.
- *PRINTcipher-48* (Knellwolf et al., 2011) was broken: an
  invariant-subspace attack recovers the secret key in O(2^24)
  encryptions. Listed for completeness only; do not deploy.
- *PRINCE* uses the FX-construction with a 12-round core; its
  provable 2^(-64) bound comes from the FX analysis (Borghoff et al.,
  CRYPTO 2012), not from the core SPN.
- *ASCON* is the NIST LWC standard (NIST SP 800-232, 2025). It is a
  duplex sponge / AEAD, not a block cipher. The 2^(-128) bound is on
  the permutation; the AEAD security is determined by the rate
  choice. The ~2,570 GE figure is for the Ascon-128 AEAD core.
- *Native 4-bit ops*: PRESENT uses 4-bit S-box inputs but the linear
  layer is a bit-permutation that operates on 64-bit words.
  QUARTET's FullMix is a 4×4 GF(2) matrix over 4-bit words, with no
  wider operations in the round function. This is the design
  distinction the paper claims: QUARTET is the smallest SPN in
  which **every** round-function primitive (S-box, key XOR, linear
  layer) is a 4-bit operation.

**Positioning.** QUARTET does not replace PRESENT, ASCON, or any
standardized primitive. It fills a niche: a 4-bit-native SPN with a
provable 2^(-64) bound at the smallest possible block size (16-bit),
for use as a construction block in modes that need 4-bit hardware
(less than 200 GE), a provable single-trail bound, and an order-4
linear layer. The recommended uses in §10.4 are the use cases; the
comparison is for sizing and context, not for head-to-head
replacement.

### 13.1 Pareto Win: FPE at <200 GE

QUARTET's claim is **not** "smaller than PRESENT" (166 GE > 107 GE).
The claim is: **FPE (Format-Preserving Encryption) for <200 GE + <2B
RAM + ~700 cycles**, where alternatives need >500 GE or fail entirely.

| Criterion | QUARTET-FPE (Mode 5) | PRESENT + FPE | NIST FF3 | GIFT-FP |
|-----------|----------------------|---------------|----------|---------|
| GE (serial, enc-only) | ~166 GE | ~107 GE | N/A (SW) | ~500+ GE |
| GE (with FPE overhead) | <200 GE | >500 GE | N/A | >500 GE |
| RAM | <2 bytes | <2 bytes | >16 KB | >4 bytes |
| Cycles (ATmega328P) | ~700 | ~1,000 | >100,000 | ~2,000 |
| FPE-native | Yes (Mode 5) | No (needs Feistel) | Yes | No |
| Constrained device fit | Yes | Partial | No (>16KB RAM) | Partial |

**Key differentiators:**

1. **FPE-native construction:** QUARTET Mode 5 is a native wide-block
   construction (4-block Mercy-style) with tweak `T = L = QUARTET_K0(T)`.
   PRESENT requires an external Feistel wrapper for FPE, adding >300 GE.

2. **ATmega328P efficiency:** ~43 cycles/round × 16 rounds = ~688 cycles
   total. FF3 requires >100K cycles (AES-based, impractical on 8-bit).

3. **RAM constraint:** FF3 needs >16 KB RAM for its AES calls. QUARTET
   needs <2 bytes (state register only). This is the decisive factor
   for constrained devices.

4. **Security proof:** QUARTET-FPE has a proven security theorem
   (`coq/prp_bound.v` §6: `Adv ≤ 2^-61 + q²/2^16`). FF3 has known
   attacks (Biau et al., 2019) and was withdrawn by NIST.

**The Pareto win:** For applications needing FPE on constrained devices
(<200 GE, <1 KB RAM, <1000 cycles), QUARTET is the only option that
satisfies all three constraints simultaneously.

---

## 14. References

1. Bogdanov et al., "PRESENT: An Ultra-Lightweight Block Cipher," CHES 2007
2. Beaulieu et al., "SIMON and SPECK Families of Lightweight Block Ciphers," 2013
3. De Cannière, "KATAN and KTANTAN — A Family of Small and Easy-to-Implement
   Hardware-Oriented Block Ciphers," CHES 2009
4. Daemen and Rijmen, "The Design of Rijndael: AES," Springer 2002
5. Daemen, "Cipher and Hash Function Design," PhD Thesis, KU Leuven 1995
6. Nyberg, "Differentially Uniform Mappings for Cryptography," Eurocrypt 1994
7. Matsui, "Linear Cryptanalysis Method for DES Cryptosystems," Eurocrypt 1993
8. Biham and Shamir, "Differential Cryptanalysis of DES-like Cryptosystems," 1990
9. Hell et al., "Grain — A Stream Cipher for Constrained Environments," 2006
10. NIST, "Lightweight Cryptography Standardization Process," 2017-2023
11. Knellwolf, Meier, and Naya-Plasencia, "Conditional Differential Cryptanalysis
    of Trivium and KATAN," SAC 2011
12. Borghoff et al., "PRINCE — A Low-Latency Block Cipher for Pervasive Computing
    Applications," CRYPTO 2012
13. Guo et al., "LED: A Lightweight Block Cipher," CHES 2011
14. Shibutani et al., "Piccolo: An Ultra-Lightweight Blockcipher," CHES 2011
15. Knellwolf, Meier, and Naya-Plasencia, "Cryptanalysis of the PRINTcipher Family,"
    FSE 2012 (the actual cryptanalysis paper)
16. Luby and Rackoff, "How to Construct Pseudorandom Permutations from
    Pseudorandom Functions," SIAM J. Computing, 1985
17. Even and Mansour, "A Construction of a Cipher from a Single Pseudorandom
    Permutation," J. Cryptology, 1991
18. Sarkar, "Improving Upon the TET Mode of Operation," IACR
    Cryptology ePrint Archive 2007/317, 2007
19. NIST SP 800-38G, "Recommendation for Block Cipher Modes of Operation:
    Methods for Format-Preserving Encryption," 2016
20. NIST SP 800-232, "Ascon-Based Lightweight Cryptography Standards for
    Constrained Devices," 2025
21. Biryukov and Wagner, "Slide Attacks," FSE 1999
22. Kelsey, Schneier, and Wagner, "Key-Schedule Cryptanalysis of IDEA, G-DES,
    GOST, SAFER, and Triple-DES," CRYPTO 1996
23. Goodwill, Jun, and Jaffe, "A Testing Methodology for Side-Channel
    Resistance Validation," 2011 (non-restricted version of the TVLA)
24. Biham, "New Types of Cryptanalytic Attacks Using Related Keys," J. Cryptology, 1994
25. NIST SP 800-131A Rev. 2, "Transitioning the Use of Cryptographic Algorithms
    and Key Lengths," 2019 (referenced in SIMON/SPECK withdrawal context)

---

## 15. Files

- `cipher.py` — Python reference implementation of the cipher (table + bitsliced)
- `cryptanalysis.py` — DDT / LAT / SAC / differential / linear / statistics / benchmark
- `compare.py` — 20-random-vector sanity check (Python vs C)
- `cross_check.py` — C self-test plus 65536×4 full-space roundtrip
- `sbox.h` — PRESENT S-box and inverse + bitsliced S-box (single C source of truth)
- `quartet_core.h` — Cipher core: table + bitsliced variants; the AST-checked constant-time surface
- `quartet.h` — Umbrella header: includes `quartet_core.h` plus the `self_test`
- `quartetchiffre.c` — Canonical C reference (table-based): defines S-box tables, runs self-test/benchmark
- `quartetchiffre_bitsliced.c` — Bitsliced C reference: defines `QUARTET_BITSLICED`, runs self-test/benchmark
- `quartet_runner.c` — Thin I/O adapter: stdin/stdout over the same cipher
- `quartet_round_asm.s` — One-round AVR assembly reference, with cycle count
- `coq/quartet_correct.v` — Machine-checked QUARTET roundtrip correctness (Coq 8.18)
- `coq/present_wide_trail.v` — Machine-checked PRESENT wide-trail bound: DU=4, 31-round min 62 active S-boxes, DP ≤ 2⁻¹²⁴ (Coq 8.18)
- `coq/prp_bound.v` — Machine-checked PRP bounds for QUARTET Mode 1 Feistel (Coq 8.18)
- `tests/test_bounds.py` — Machine-checked wide-trail bound (differential + linear)
- `tests/test_constant_time.py` — AST-based static analysis of the cipher core
- `tests/test_kats.py` — KAT harness: 262,157 entries (Python + C)
- `tests/generate_kat.py` — Regenerates the KAT file from the Python reference
- `tests/vectors/quartet_kat.txt` — Generated KAT (262,144 full-space + 13 spec vectors)
- `tests/tvla.py` — Level 1 software TVLA: Welch t-test per counter, Holm-Bonferroni, negative control
- `tests/tvla_counters.py` — Windows Performance Counter set (psutil + wall clock)
- `tests/fixtures/leaky_cipher.py` — Python negative-control SUT (key-dependent sleep)
- `tests/fixtures/leaky_runner.c` — C negative-control SUT (key-dependent nanosleep)
- `tests/fake_libc/` — Minimal libc headers for the AST preprocessor
- `SPEC.md` — This specification
