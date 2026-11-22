# Split-minor affine certificate proof map

Let (M) be the seven-point evaluation matrix of
(1,x,y,x^2,xy,x^3,x^2y), with six source points and (-Q).
Split its rows into the first three source points and the other three
source points plus (-Q). The characteristic-two Laplace expansion
across any three columns gives

\[
  \det M = \sum_{S\in\binom{[7]}3}
       \det(M_{L,S})\det(M_{R,S^c}) = B(L,R),
\]

where (L,R\in\mathbb F_{2^{41}}^{35}) are the two minor vectors and
(B) is their coordinate dot product. Every genuine six-point
relation to (Q) has determinant zero on the recorded distinct-x
chart.

For source families inside affine spaces (L_0+U) and (R_0+V),
a binary-linear functional ℓ on the field certifies a whole-box
rejection if ℓ(B(L_0,R_0))=1 and it kills
(B(U,R_0)), (B(L_0,V)), and (B(U,V)). Bilinearity then makes
ℓ(B(L,R))=1 for every family pair, so every determinant is
nonzero. The worker checks whether the base determinant lies outside
the field-bit span of those three difference families.

| Result | Lean declaration | Exact scope | Status |
| --- | --- | --- | --- |
| Affine bilinear separator implication | `SplitCertificate.affine_bilinear_separation` | Arbitrary left/right types, additive operations, Boolean-valued bilinear evaluation, explicit base and annihilation hypotheses | Built |
| Seven-row Laplace factorization | No declaration yet | Actual seven-row RR matrix over characteristic two | Partial formalization; 69 first assignments match the previous independent determinant, and the auditor recomputes 3,664 determinants by Gaussian elimination |
| Relation implication and chart | No declaration yet | N41 curve, subgroup point, six signed source points and distinct x | Partial formalization; the prior independent group audit checked the recorded assignments |

`lean-toolchain` pins Lean 4.34.1. `lean.stdout` retains the
`#print axioms` output, which lists `propext` for the structural
theorem; the module has no `sorry`, `admit`, `sorryAx`, or custom
claim axiom. `lean4checker --fresh` was unavailable. The missing
formal bridge is the field-valued determinant factorization and the
curve-to-evaluation-matrix implication, not the affine separator
logic.
