# Why Camellia-s1 Fails Fourier Vanishing — Structural Analysis

**Author:** Mano H. | 2026-09-12

## Summary

Camellia-s1 (an 8-bit S-box used in the Camellia block cipher) does **not** satisfy the Fourier vanishing property required by the spectral hull method. This document explains why, at both empirical and structural levels.

---

## Empirical Evidence

| Property               | Camellia-s1   | AES        |
|------------------------|---------------|------------|
| Construction type      | Composite     | Inversion  |
| Bit-width              | 8             | 8          |
| Differential uniformity (DU) | 10        | 4          |
| Nontrivial nonzero $\hat{S}(\chi)$ | 202/255 | 0/255      |
| Max $|\hat{S}(\chi)|$ for $\chi \neq 0$ | ≈ 2⁻⁸·⁸³ | exactly 0 |

Both S-boxes have acceptable differential uniformity (DU ≤ 8 is standard for 8-bit ciphers). DU alone **cannot** distinguish between passing and failing S-boxes. The difference lies entirely in the **Fourier spectrum of the DDT**.

For an S-box satisfying Fourier vanishing, *every* nontrivial character $\chi \neq 0$ produces a coefficient of exactly zero. Camellia-s1 has 202 out of 255 such coefficients strictly nonzero — the DDT column sums do not balance under most characters.

---

## Structural Explanation

### Field Inversion → Symmetric Derivatives → Fourier Vanishing

AES and 11 of the other 12 passing S-boxes are derived from field inversion over $\text{GF}(2^m)$:

$$f(x) = x^{2^m - 2} = x^{-1}$$

with $f(0) = 0$ defined artificially.

This map has a key property: its derivatives

$$D_a f(x) = f(x + a) + f(x)$$

produce output distributions with **strong regularity**. Specifically, for each nonzero input difference $a$, the set $\{D_a f(x) : x \in \text{GF}(2^m)\}$ contains each possible value either $\lambda$ or $\lambda+1$ times (where $\lambda$ depends on $m$). This "almost-biased" distribution means the column sums of the DDT are perfectly balanced under any nontrivial character $\chi$:

$$\sum_{dx, dy} D[dx][dy] \cdot (-1)^{\langle \chi, dy \rangle} = 0 \quad \forall \chi \neq 0$$

This is because the derivative functions of an inversion map over a characteristic-2 field have **affine-invariant symmetry**: they behave like almost-bent (AB) permutations when restricted to certain subspaces, and their Walsh-Hadamard transforms vanish identically for most characters.

### Composite Field Construction → Broken Symmetry

Camellia-s1 uses a **composite field construction** over $\text{GF}((2^4)^2)$. Concretely:

1. View $\text{GF}(2^8)$ as $\text{GF}((2^4)^2)$ via a polynomial basis
2. Map the input to $\text{GF}(2^4)$ coordinates
3. Apply multiplication-by-inverse in the smaller field
4. Apply affine transformations and mixing polynomials
5. Map back to $\text{GF}(2^8)$ representation

This chain of operations introduces multiple layers of algebraic complexity that **break** the strong regularity property of pure field inversion:

- The coordinate mapping itself distorts the output distribution of derivatives
- The mixing polynomials (which ensure diffusion) add nonlinear terms that prevent the "λ or λ+1" uniformity
- There exists no theoretical guarantee that the DDT column sums balance under arbitrary characters

The result is that individual DDT entries can be quite varied for different output differences, leading to nonzero Fourier coefficients across most characters.

### Mathematical Formulation

For a field inversion S-box $f(x) = x^{-1}$ over $\text{GF}(2^m)$, consider the character sum for a fixed input difference $\Delta_x \neq 0$ and character $\chi$:

$$\Sigma_\chi(\Delta_x) = \sum_{y} \left| f^{-1}(\Delta_x + y) \cap f^{-1}(y) \right| \cdot (-1)^{\langle \chi, y \rangle}$$

For field inversion, this sum evaluates to zero due to the identity:

$$x^{-1} + (x + \Delta_x)^{-1} = \frac{\Delta_x}{x(x + \Delta_x)}$$

The right-hand side maps $x \mapsto \frac{1}{x(x + \Delta_x)}$ (up to scaling), which is a rational function whose image distribution under any additive character is perfectly balanced. This is a known result in finite field theory related to the fact that Kloosterman sums over $\text{GF}(2^m)$ have specific structural properties.

No such identity exists for the composite-field construction used in Camellia-s1. Its S-box cannot be expressed as a single rational function over the base field; instead it involves nested field operations that break this algebraic structure.

---

## Practical Implications

1. **Fourier vanishing is not universal.** It correlates strongly with S-boxes constructed from field inversion or APN-like permutations. Composite-field constructions, despite being cryptographically valid, do not inherit this property.

2. **The failure identifies a design criterion.** When choosing or designing an S-box, designers who need the spectral hull bound should prefer inversion-based or equivalently structured S-boxes. Camellia-s1 demonstrates that even well-respected, widely-deployed S-boxes may not satisfy the condition.

3. **Non-vanishing does not mean insecure.** Camellia-s1 has DU=10, which is acceptable (even if higher than ideal). The Fourier non-vanishing simply means the spectral hull method gives a looser bound or is inconclusive. Other security guarantees (single-trail bounds, linear cryptanalysis bounds) may still apply strongly.

4. **Quantitative impact.** For Camellia-s1, the maximum nonzero Fourier coefficient is approximately $2^{-8.83}$, which translates to a worst-case hull accumulation factor of roughly $2^{8.83}$ per S-box layer. While weaker than the exact-zero case, this is still far more constraining than no analytical bound at all. Future work could develop a generalized hull bound for the non-vanishing case that incorporates the actual magnitude of the largest coefficients.

---

## References

- Bogdanov et al., "PRESENT: An Ultra-Lightweight Block Cipher," CHES 2007 — describes the 4-bit inversion S-box
- Daemen & Rijmen, "The Design of Rijndael," Springer 2002 — AES S-box construction via inversion over GF(2⁸)
- Fukuda et al., "Camellia: a 128-bit Block Cipher for General Purposes," FSE 2001 — original specification, Section 4 describes the composite-field S-box
- Nyberg, "Differentially Uniform Mappings for the Construction of Invertible Filters," Journal of Cryptology 1994 — establishes connections between differential uniformity and Fourier-analytic properties of S-boxes
