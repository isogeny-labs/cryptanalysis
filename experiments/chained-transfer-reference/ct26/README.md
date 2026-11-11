# CT26: independently computed seven-kernel Frobenius audit

**Scientific standing:** [pcc:unverified]. Public synthetic example, not a solver or speed claim. This is an executable differential *oracle* for the already selected CT20/CT21 kernel inputs, not a second Jacobian transfer implementation.

## Fixed inputs

Over `F_101` the two old elliptic components are

- `E109: y²=x³+x+46, #E(F101)=109, trace=-7`, kernel `h1=x³+35x²+100x+72`.
- `E113: y²=x³+44x+21, #E(F101)=113, trace=-11`, kernel `h2=x³+8x²+46x+59=(x-50)(x-68)(x-76)` modulo 101.

The independently implemented finite-field oracle uses `F101[t]/h1` and adjoins `s²=2`; the resulting field has 101^6 elements. It does not import any native FpR, Kohel, elliptic point, Jacobian or Richelot code.

## Local reproducible observations — not signed PCC

```sh
python3 -S -B experiments/chained-transfer-reference/ct26/seven_kernel_oracle.py
# Rejects optimization that disables assertions:
python3 -O -S experiments/chained-transfer-reference/ct26/seven_kernel_oracle.py
```

Source SHA256 `91f8a2bf09bfaf88e20a39b2cbe349c71fb01e7689de3e87dee0d423174f0de9`; Git blob SHA1 `77e27d57694305c62e63fbd9173e3f138600aaa3`. The producer local run used Python 3 with `-S -B` and printed:

| Observable | First factor E109 | Second factor E113 |
|---|---:|---:|
| Root field | x in F101³ | x in F101 |
| Full point field | F101⁶ | F101² |
| Frobenius on chosen cyclic 7-kernel | [5] | [6] |
| Frobenius order on generator | 6 | 2 |
| Exact subgroup and complete addition table | 7/7, 49 sums | 7/7, 49 sums |

Independent cubics are **not interchangeable**: the first kernel polynomial is irreducible, but the second splits over F101. An initial attempt to model both roots as cubic field generators failed its irreducibility guard. The corrected oracle handles the second kernel's rational abscissae and quadratic ordinate field explicitly. No unlogged assumption of irreducibility survives.

The product's 49 pairs are distinct, closed under componentwise addition and Frobenius, with action `(i,j) -> (5i,6j)`. Of its eight order-7 subgroups, exactly **two** are rational/Frobenius-stable (the coordinate axes). These are abstract product pairs; the script does **not** evaluate `P0` to produce 49 Jacobian divisor classes.

## Classification proof and exhaustive control

The Frobenius characteristic polynomials on full geometric 7-torsion are

```text
E109[7]: T² - (-7)T + 101 = (T-5)(T-2) modulo 7
E113[7]: T² - (-11)T + 101 = (T-6)(T-4) modulo 7
```

The spectra `{5,2}` and `{6,4}` are disjoint. Therefore any Frobenius-equivariant map `E109[7] -> E113[7]` is zero, and a Frobenius-stable subspace of the direct sum is a direct sum of coordinate eigenspaces. It cannot contain a new mixed-factor rational 7-kernel graph.

The oracle exhaustively enumerates *all* `[4 choose 2]_7=2850` rank-two planes in `F7^4` by reduced-row-echelon forms. Standard alternating product pairing gives `(7+1)(7²+1)=400` maximal isotropic planes. Six planes are Frobenius-stable, of which **four** are isotropic, with the other two full-single-factor planes excluded. The four admissible planes are precisely the four choices of one Frobenius eigenline on each elliptic component. This independently corroborates the existing four abstract degree-7 candidates; it is **not** a novel classification theorem.

Because the old HLP map `P0:E109×E113 -> J0` has 2-primary kernel, its restriction to geometric 7-torsion is an isomorphism. Under the previously stated HLP gluing hypotheses, this classification transfers to `J0[7]`. The oracle itself does not re-check the HLP quotient, polarization, coordinate maps or `P0`; that remains a cross-tool scientific dependence.

## Tests and negatives

The script verifies the cubic field's Frobenius degree, nonresidue, extension-field square roots, each generator's exact order seven, all 49 additions per factor, the 6-fold Frobenius identity, full 49-pair closure, eight rank-one lines, all 2850 planes, alternating isotropy and the two excluded nonisotropic invariant planes. Wrong scalar `[6]` is not zero on the chosen generator; a wrong Frobenius eigenvalue fails the generator comparison. Running with `-O` exits nonzero rather than silently skipping assertions.

No Jacobian-valued 49-point kernel, 64 four-torsion lifts, transported Richelot `R1`, next `Psi`, full-domain 12,317-class dual check or solving-cost measurement was carried out here.

## Sources / prior-work audit

- Existing `crypto:research/chained_jacobian_transfers_20261110/CT21_PLAN.md` and `SEVEN_JACOBIAN_PROOF.md` (parent crypto PR [#3877](https://github.com/isogeny-labs/crypto/pull/3877), frozen c1b9aa2).
- Existing `cryptanalysis:experiments/chained-transfer-reference/src/seven_glue.rs`, `SEVEN_TRANSFER.md` (consumer [#1484](https://github.com/isogeny-labs/cryptanalysis/pull/1484), frozen 2450815e2).
- Howe–Leprévost–Poonen, *Large torsion subgroups of split Jacobians*, [arXiv:math/9809210](https://arxiv.org/abs/math/9809210), §3.2 (2-torsion gluing; no novelty claim).
- [Sage elliptic isogeny documentation](https://doc-gitlab.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/ell_curve_isogeny.html) (kernel polynomials may encode rational/Galois-stable subgroups).
- Shared research-KB MCP tools were not exposed in this runtime and the repository CLI workspace was not available; **KB unavailable**. Existing pinned research notes were used instead; absence of hits is not claimed.

## Next acceptance criterion

Feed these two explicit generator points through the **unchanged native** `P0` / extension-product pull on all 49 pairs; compare 49 distinct Mumford classes, 49² sums, Frobenius action, order seven and compatibility with the existing `Phi` evaluation. Then compute the already planned 64 product four-torsion lifts and the `R0 -> R1` kernel transport. Use a separate independent verifier and PCC signed standing before promoting any claim. Budget gating for EKS/S3 remains unchanged; no paid job or benchmark is authorized here.
