# Proof map: right-subspace norm and Boolean ANF

| Result | Formal or computational evidence | Exact scope |
| --- | --- | --- |
| `Res_Z(H,L_V mod H)=0` exactly when `H` has a root in `V` | Written proof below; 281 valid-code GCD equivalence checks per row in [run_sage.py](run_sage.py) | The exact N41 field and the constructed 10-dimensional product subspace. A field/resultant formalization in Lean remains open. |
| The ten-bit Möbius/ANF butterfly is involutive | `ANFButterfly.butterfly_involutive` in [ANFButterfly.lean](ANFButterfly.lean), checked Lean 4.34.1, no axioms | One Boolean butterfly. The finite ten-bit iteration and field-bit bridge are checked by the producer's inverse transform and the independent auditors; they are not encoded as a Lean theorem. |
| All 1,024 ANF coefficients are nonzero on each frozen residual | [result.json](result.json), full row-0 digest in [audit_result.json](audit_result.json), full row-1 digest in [audit_result_v3.json](audit_result_v3.json) | Two specific N41 residuals, 1,024 raw left codes each. This finite-instance statement is computationally audited, not proved by Lean term reduction. |

## Readable proof

Over a field, `L_V(Z)=∏_{q∈V}(Z+q)` is a product of distinct linear factors because the right-product map has ten independent basis vectors. The resultant is multiplicative in its second argument, so `Res_Z(H,L_V)` is a nonzero scalar multiple of `∏_{q∈V} H(q)`. A field has no zero divisors. Therefore this resultant vanishes exactly when at least one `H(q)` vanishes, including the case `H=0`. Replacing `L_V` with its remainder modulo nonzero `H` preserves the common-root test, although the resultant's field value can change by a nonzero leading-coefficient factor. The producer and auditors both use the **remainder** resultant for the measured ANF: the producer constructs the remainder by modular squaring, and the auditors construct the full product directly before division. The code checks zero-set equivalence with a GCD for every source-valid left code in both rows.

For a Boolean truth table `f`, one butterfly replaces `(f(S),f(S∪{i}))` by `(f(S),f(S) XOR f(S∪{i}))`. Applying the butterfly twice restores the pair, as the checked Lean lemma states. Iterating over ten bit positions computes and inverts the Boolean zeta transform, yielding the unique squarefree ANF coefficients. The producer explicitly inverts its transform and compares all 1,024 values; the auditors derive identical coefficient-array SHA-256 digests from a separate vanishing-polynomial construction.

## Formalization boundary

`lean ANFButterfly.lean` and its `#print axioms` audit pass under `leanprover/lean4:v4.34.1`; `lean4checker --fresh` is unavailable. The full theorem connecting the concrete field polynomial, the exact 13-term eliminant, Sage's resultant, and all 1,024 ANF coefficients is not yet a Lean declaration. A faithful completion would formalize the field representation and polynomial-resultant/root equivalence, then verify the finite coefficient array or a compact certificate inside Lean. The exact computational receipts preserve the current finite claim while that bridge remains open.
