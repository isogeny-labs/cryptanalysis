# Proof map for the free-code two-pair resultant

The first pair has reciprocal `w` satisfying
`f(w)=C₁w²+p₁w+H₁=0`. The prior eliminated-pair quartic
`R(w;t,p₂,H₂,C₂)` contains the target reciprocal `t` and the still-free
second source product `p₂`. The checked Sage producer divides `R` by
`f` over the actual bivariate polynomial ring `F[p₁,p₂]`, verifies
the symbolic remainder `r₀+r₁w` for each of 25 target points, and
emits `C₁r₀²+p₁r₀r₁+H₁r₁²`. All emitted polynomials have 13 nonzero
monomials and bidegree `(4,4)`.

| Result | Lean declaration | Hypotheses and scope |
| --- | --- | --- |
| Linear remainder norm equals the explicit eliminated value | `FreeCodeElimination.split_quadratic_norm` | Any commutative ring; both Vieta coefficient identities stated explicitly. |
| Eliminated value zero exactly when the split first quadratic and quartic share a field root | `FreeCodeElimination.eliminated_zero_iff_shared_root` | Any field; nonzero leading coefficient, explicit split factorization, Vieta identities, and exact linear remainder identity. |

`lean FreeCodeElimination.lean > lean_check.log 2>&1` builds both
declarations with pinned Lean `4.34.1`. The file contains `#print axioms`
for each theorem; the log records standard `propext`,
`Classical.choice`, and `Quot.sound`, with no custom axiom, `sorry`,
native evaluation, or kernel bypass. `lean4checker --fresh` is not
available in this environment.

The concrete field is `GF(2)[u]/(u^41+u³+1)`. The 281 valid first
source codes have two rational reciprocal roots each, and the
checked-Sage producer verifies the exact bivariate polynomial
remainder. The source-pair coordinate law and its roots are supported
by the previous [exact pair oracle](../n41_w11_exact_two_pair_oracle_20261018/RESULT.md).
The reduction of the specific elliptic-curve Semaev equation to the
prior `R` formula is an explicit algebraic derivation in the
[two-quartic result](../n41_w9_two_quartic_resultant_20261017/RESULT.md),
but is not a Lean theorem over a formalized characteristic-two curve.
The 13-term expansion and SAT bit-blast equivalence are likewise
checked by frozen computation rather than a Lean polynomial or circuit
formalization. A full curve-level Lean theorem remains open on those
definitions and identities; the two structural implications above are
checked.
