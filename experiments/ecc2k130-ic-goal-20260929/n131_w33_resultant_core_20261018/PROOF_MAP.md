# Proof map: quadratic source expansion

For source bits `b_i ∈ {0,1}` and field coefficients `a_i`, put
`q = Σ b_i a_i`. In characteristic two,
`q² = Σ b_i a_i²` and
`q³ = Σ b_i a_i³ + Σ_{i<j} b_i b_j(a_i²a_j+a_i a_j²)`.
Consequently, after fixing the first source product, the 13-term
resultant is quadratic in the 32 bits of the second source code.

| Statement | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Square expansion | `QuadraticSourceExpansion.weighted_square` | Commutative ring `F`; `(2:F)=0`; every listed weight idempotent (`b*b=b`). Checked. |
| Cube expansion, with singleton and pair terms | `QuadraticSourceExpansion.weighted_cube` | Same hypotheses; the recursive pair sum is `b*a²*S+b*a*Σb_j a_j²`. Checked. |

`lean-toolchain` pins Lean 4.34.1. `lean QuadraticSourceExpansion.lean`
builds the module; `lean_check.log` records `#print axioms` for both
theorems. The standard Lean foundations reported are `propext`,
`Classical.choice`, and `Quot.sound`. The final module contains no
`sorry`, `admit`, custom axiom, native proof shortcut, or kernel bypass.
`lean4checker --fresh` was unavailable on this host.

The exact N131 resultant coefficients, field representation, and its
link to the curve pair outputs come from the frozen Sage exporter in the
[earlier N131 preflight](../n131_w33_freecode_resultant_20261018/RESULT.md).
The generic norm and shared-root implications remain the checked Lean
theorems in the [N41 proof map](../n41_w11_freecode_resultant_20261018/PROOF_MAP.md).
The complete curve-level bridge to the symbolic resultant and the
concrete Boolean circuit is computationally checked but not formalized
in Lean. The public fixed-code unit-ideal report has no separately
checked Gröbner certificate.
