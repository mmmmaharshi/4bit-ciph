# MILP vs Spectral Hull Bound — A Practical Comparison

**Author:** Mano H. | 2026-09-12

## Summary

MILP-based single-trail enumeration (Bai et al., CHES 2014; Sun et al., FSE 2014) and the spectral hull method address different aspects of differential cryptanalysis. This document quantifies their relationship and shows why both are needed.

---

## The Two Directions of the Bound

For any input/output difference pair $(d_{in}, d_{out})$, the actual differential probability is:

$$P(d_{in}, d_{out}) = \sum_{\text{trails } \tau: d_{in} \to d_{out}} P(\tau)$$

This sum has two components:

| Component | Bounded by | What it captures |
|-----------|-----------|------------------|
| Maximum trail probability | MILP | The single most probable path |
| Sum over ALL trails | Spectral hull | Aggregate mass from thousands of paths |

A tight $P(d_{in}, d_{out})$ requires BOTH bounds. MILP alone can underestimate by many orders of magnitude when moderate-probability trails accumulate.

---

## Concrete Examples

### QUARTET-16 (n=16, 4 rounds)

| Bound | Value | Notes |
|-------|-------|-------|
| Single-trail (MILP) | ~2⁻⁶⁴ | Tight but only one path |
| Empirical max DP | ~2⁻⁶·³⁸ | Actual observed value |
| Spectral hull | 2⁻⁸ | Analytical upper bound on sum |

Gap (MILP → empirical): **~2⁵⁷·⁶ ≈ 10¹⁷×**

Spectral hull closes virtually all of this gap (factor of ~3.07×).

### PRESENT (n=64, 31 rounds)

| Bound | Value | Notes |
|-------|-------|-------|
| Single-trail (MILP) | ~2⁻¹²⁴ | Based on min 42 active S-boxes |
| Empirical max DP | ~2⁻³² | Birthday limit observation |
| Spectral hull | 2⁻³² | Independent of rounds |

At 31 rounds, MILP gives a very strong single-trail bound (2⁻¹²⁴) but still misses the true probability (2⁻³²) by a factor of 2⁹² ≈ 10²⁸. The spectral hull gives exactly the birthday limit (2⁻³² for n=64), independent of round count.

**Note:** For PRESENT at 31 rounds, both MILP and spectral give useful information — MILP is stronger for single trails, spectral correctly identifies the hull limit. Neither alone tells the whole story.

### AES-128 (n=128, 10 rounds)

| Bound | Value | Notes |
|-------|-------|-------|
| Single-trail (MILP) | Extremely small | Many active S-boxes |
| Spectral hull | 2⁻⁶⁴ | Birthday limit for 128-bit |
| Actual security | Much higher | Diffusion layer is very strong |

For AES at full round count, MILP bounds dominate spectral bounds for the specific cipher in question. But the spectral bound still matters as a universal ceiling: no matter how you optimize MILP modeling, the total differential probability cannot exceed 2⁻⁶⁴ for a 128-bit block cipher regardless of diffusion quality.

---

## When Spectral Outperforms MILP

The spectral hull bound dominates MILP single-trail bounds in these regimes:

### 1. Small block sizes / few rounds

At small block sizes (n ≤ 16–32 bits) and low round counts, the MILP single-trail bound can itself be close to 2⁻ⁿ (essentially vacuous), while the spectral bound remains fixed at 2⁻ⁿ/². For designers of extremely constrained devices (RFID tags, sensor nodes), this matters.

### 2. Unknown or poorly understood linear layers

MILP requires precise modeling of the linear diffusion layer. If the linear layer structure is complex, partially unknown, or uses non-standard mixing (e.g., sparse matrices without good branch numbers), MILP bounds degrade rapidly. The spectral bound is **independent** of the linear layer structure — it holds for ANY invertible M.

### 3. Rapid design-space exploration

When exploring many candidate ciphers during the design phase, running MILP optimization for each is expensive (integer programming can take minutes to hours per instance). Computing Fourier coefficients of the S-box takes milliseconds and gives an immediate lower bound on achievable security.

### 4. Certification and auditing

For security certification purposes, having a machine-checked proof (Coq) that the hull does not exceed 2⁻ⁿ/² provides an independent verification channel alongside MILP-derived bounds. Regulators and standardization bodies value orthogonal verification methods.

---

## When MILP Outperforms Spectral

The spectral bound is a constant 2⁻ⁿ/² regardless of round count. In contrast, MILP single-trail bounds decay exponentially with the number of rounds:

$$P_{single}(R) \leq 2^{-c \cdot R}$$

where $c > 0$ depends on the cipher's minimum active S-box count per round.

Therefore, for ciphers with:
- Large block sizes (AES, 128+ bits)
- Strong diffusion (branch number ≥ 4)
- High round counts (> 6–8 rounds for 8-bit S-boxes)

...the MILP single-trail bound will typically be much tighter than 2⁻ⁿ/² and remains the binding security guarantee.

---

## Practical Recommendations

### For Cipher Designers

1. **Compute both.** Run MILP analysis AND check Fourier vanishing for your S-box.
2. **Use spectral as a floor.** Even if MILP is tighter, know that the spectral bound sets the absolute ceiling on hull accumulation.
3. **Exploit independence.** Since the spectral bound holds for ANY linear layer, you can fix the S-box first and then optimize the linear layer for MILP bounds. The spectral property won't change.
4. **Design-time filter.** Check Fourier vanishing before investing effort in MILP modeling — if it fails, the spectral bound is inconclusive and you must rely entirely on MILP + empirical analysis.

### For Standardization Bodies

1. Request BOTH single-trail (MILP) and hull (spectral) bounds for submission packages.
2. Use spectral bounds as a sanity check against reported empirical probabilities.
3. Consider Fourier vanishing as a new S-box evaluation criterion alongside DU, LAT, and algebraic degree.

---

## Mathematical Complementarity

The relationship can be expressed formally. Let $\mathcal{T}$ be the set of all trails connecting $d_{in}$ to $d_{out}$ over R rounds:

$$P(d_{in}, d_{out}) = \sum_{\tau \in \mathcal{T}} P(\tau)$$

We can bound this using:

1. **MILP (single-trail):** $\max_{\tau \in \mathcal{T}} P(\tau) \leq \epsilon^{B \cdot R / 2}$
2. **Spectral (hull):** $\sum_{\tau \in \mathcal{T}} P(\tau) \leq 2^{-n/2}$

By Cauchy-Schwarz (used in the hull proof):

$$\sum_{\tau \in \mathcal{T}} P(\tau) \leq |\mathcal{T}|^{1/2} \cdot \sqrt{\sum_{\tau \in \mathcal{T}} P(\tau)^2} \leq |\mathcal{T}|^{1/2} \cdot 2^{-n/2}$$

where $|\mathcal{T}|$ is the number of distinct trails. The MILP bound controls the maximum term $P(\tau)$; the spectral bound controls the sum via collision probability analysis. Neither subsumes the other.

---

## References

- Bai et al., "Automatic Search-Based Metaheuristic Construction of Security Bounds," CHES 2014
- Sun et al., "Automatic MILP Modeling for the Analysis of Substitution-Permutation Networks," FSE 2014
- Daemen & Rijmen, *The Design of Rijndael*, Springer 2002
- Nyberg, "Differentially Uniform Mappings for the Construction of Invertible Filters," Journal of Cryptology 1994
