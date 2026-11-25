# Proof map for the linked-root circuit

The frozen Boolean circuit shares the first two slots' 17-bit source code,
unrotated pair-output reciprocal `1/x`, and endpoint inverse witnesses.
The two output coordinates are then separately Frobenius-rotated by 0 and
16. Thus every assignment uses one source edge and one pair-output x root
in both slots. The circuit does not bind the point-output signs. When the
algebraic x-root solution lifts, the second output can be `τ¹⁶P` or
`−τ¹⁶P`; each corresponds to valid endpoint signs for the same source
edge. The prior N41 same-sign linked relation is contained in this domain.

Let `λ` be the subgroup action of Frobenius. In a signed-Frobenius-folded
factor-base row, the repeated columns receive `λᵃ ± λᵃ⁺¹⁶` times their
original signed coefficient. [`LinkedSign.lean`](LinkedSign.lean) proves
the general factorization

`λᵃ + ε λᵃ⁺ᵏ = λᵃ(1 + ε λᵏ)`

for integer `λ, ε`, including same and opposite signs. It compiled with
pinned Lean 4.34.1; `#print axioms` in [`lean.stdout`](lean.stdout) reports
only standard `propext`. The first generic-ring draft failed because this
standalone `Std` environment did not provide its requested type class;
[`lean_attempt1.stdout`](lean_attempt1.stdout) preserves that build.
The integer identity's transport to `Z/rZ`, the actual Koblitz Frobenius
action, and point-sign lift are concrete bridges checked below rather than
additional kernel-level theorems. `lean4checker --fresh` is unavailable
on this host.

The prior projection supplies both roots of `X²+X+2` modulo the prime
subgroup order. The first coefficient script incorrectly required both
roots to satisfy `λ¹³¹=1`; its [raw failure](link_coefficients_attempt1.stderr)
is preserved. Exactly one root has that property. The corrected
[`link_coefficients.json`](link_coefficients.json) checks both ± coefficients
are nonzero for both roots. Independent checked Sage uses the frozen
public subgroup point to identify the actual root as
`196511074115861092422032515080945363956`, verifies `τQ=[λ]Q`, and
checks `Q±τ¹⁶Q=[1±λ¹⁶]Q` in
[`lambda_sage_result.json`](lambda_sage_result.json).

The source-to-group control independently reconstructs all ten pair sums
from the W18 masks and endpoint roots in checked Sage, checks 18 distinct
folded columns after the intentional duplication, and verifies their raw
sum and subgroup projection in
[`control_sage_audit.json`](control_sage_audit.json).
The constructed complete circuit assignment checks every emitted clause
and native-XOR row. A solver model, if produced by a future variant, must
still be lifted to signed source points and replayed against the public
point and folded relation row; the bounded query produced no model.
