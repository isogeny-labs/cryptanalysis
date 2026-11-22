# Source-product recovery and family rejection

For the fixed-seed reciprocal pair equation over a field of characteristic
two,

`C z² + p z + H = 0`,

the pair output has nonzero reciprocal coordinate `z`. Solving the equation
for its source product gives `p = C z + H/z`. The admissible source products
lie in the span of the declared `PB` basis. Therefore, if the recovered
product lies outside that span, **no source pair in this family can have
that output coordinate**. A candidate inside the span is checked through
the source trace conditions and actual point reconstruction.

| Result | Lean declaration | Exact hypotheses | Checked status and implementation bridge |
| --- | --- | --- | --- |
| Recover the unique source product from a nonzero reciprocal pair coordinate | `SourceProductRecovery.recover_product` | Arbitrary field, characteristic two, `z≠0`, and the exact quadratic root equation | `lean SourceProductRecovery.lean` exits 0 with pinned Lean 4.34.1. The circuit's `C`, `H`, `PB`, and coordinate encoding are checked by the finite N41 runs. |
| Reject a whole second-pair source family when the recovered product is outside its span | `SourceProductRecovery.reject_outside_span` | Same field/root hypotheses; arbitrary `InSpan` predicate; source product belongs to it and recovered product does not | Lean proof exits 0. The N41 implementation computes the eight-bit product basis at full rank and carries a code witness through XOR reduction. |

The retained [Lean output](lean.stdout) from `#print axioms` lists
`propext`, `Classical.choice`, and `Quot.sound` for each theorem. The module
contains no admitted proof obligations or custom axioms. `lean4checker
--fresh` was unavailable on this host. The bridge to the concrete elliptic
curve, source trace constraints, and four leaf-sign combinations is checked
by [scan_oracle.py](scan_oracle.py), constructed SAT assignments, and the
independent exact [key census](keys.json); those finite checks are not a
generic Lean formalization of the curve implementation.

For the frozen W9 family, the source table contains no second-slot state
with zero `x` coordinate. The scanner checks infinity and `x=0` before
division. The span rule itself is conditional on `z≠0` and does not use an
exceptional-point assumption implicitly.
