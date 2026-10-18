# Proof map for direct second-product derivation

The rotated second-pair law is `C₂ z² + q z + H₂ = 0`, where
`z=1/x(D)` and `D` is the residual target point after subtracting a
first-pair state. Thus, when `x(D)z=1` in characteristic two, its
product coefficient is `q=C₂z+H₂x(D)`.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Pair quadratic determines the second product | `DirectProductLaw.product_from_residual` | Any field `F`, `(2:F)=0`, `x*z=1`; both directions of the displayed equivalence. Checked. |

`lean-toolchain` pins Lean 4.34.1. Running
`lean DirectProductLaw.lean` builds the theorem; `lean_check.log`
records `#print axioms` with only standard `propext`,
`Classical.choice`, and `Quot.sound`. There is no `sorry`, `admit`,
custom research axiom, native proof shortcut, or kernel bypass.
`lean4checker --fresh` was unavailable on this host.

The source-pair curve construction, Frobenius rotation, residual point
subtraction, and the reduction of the elliptic-curve sum to the pair
quadratic are checked computationally for every recorded N41 and N131
case. They are not yet formalized as one curve-level Lean theorem. The
generic resultant shared-root implication is in the earlier
[N41 proof map](../n41_w11_freecode_resultant_20261018/PROOF_MAP.md).
For every recorded case the four derived products are distinct, each
zeros the exact degree-four resultant, and the independently frozen
quartic run reports four roots; these facts exhaust that polynomial's
field roots without a separately formalized quartic factorization.
