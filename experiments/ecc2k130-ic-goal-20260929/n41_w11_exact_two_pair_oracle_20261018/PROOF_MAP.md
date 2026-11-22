# Proof map: source-product inverse and serial oracle work

The pair equation over a binary field is `C u²+p u+H=0`, with reciprocal
pair output `u≠0` and `x=u⁻¹`. Dividing by `u` gives
`p=C u+H x=C/x+H x`. Frobenius is a field automorphism, so rotating
both the output and coefficients preserves this identity. If the
product-code basis has full rank, the recovered product identifies at
most one source code. A valid code's four signed pair points are then
checked against the candidate curve point. Thus every successful
inverse-oracle row is an exact pair decomposition; a complete scan of
all first-pair states with no match is an exact miss for this two-pair
source.

| Result | Formalization and concrete status |
| --- | --- |
| Pair quadratic is equivalent to recovered product with an inverse witness | `OutputLinearization.pair_output_linear_iff` in the prior [checked theorem](../n131_w20_output_inverse_linear_20261012/OutputLinearization.lean); arbitrary characteristic-two commutative ring with the explicit inverse witness. |
| All 1,124 N41 W11 pair outputs obey that identity and the product map has 1,024 distinct codes | [inverse_result.json](inverse_result.json), recomputed through checked Sage on the frozen field and source. The concrete finite-field and code-map bridge is computationally checked rather than formalized in Lean. |
| Positive membership and ordinary-point miss | [inverse_audit_result.json](inverse_audit_result.json) independently applies the curve group law to the complete two-list source, obtaining one and zero compatible matches respectively. |
| Candidate count for repeated complete misses | `SerialOracleWork.missScan_count` in [SerialOracleWork.lean](SerialOracleWork.lean); structural recurrence, kernel checked. |
| Exact frozen-path total, 442,911,355 checks | `SerialOracleWork.frozen_serial_candidate_count`; kernel checked. [work_result.json](work_result.json) binds the numeric inputs to the prior native query. The source-to-loop-count bridge is checked by the work receipt and remains outside Lean. |
| At least 528,180 first-pair states in one complete N131 W33 serial miss | [n131_projection_result.json](n131_projection_result.json) combines the independently verified width-20 signed-state count with its exact inclusion in width 33. The concrete source inclusion and finite count remain computational certificates outside Lean. |
| Exact two-pair Boolean circuit | [build_result.json](build_result.json) checks its complete known-positive assignment against every clause and native XOR row. The gate-level circuit-to-curve bridge remains open in Lean. |

The new module uses pinned [Lean 4.34.1](lean-toolchain).
`lean SerialOracleWork.lean` built and [lean_check.log](lean_check.log)
records `#print axioms`; both declarations use only `propext`.
There are no `sorry`, `admit`, custom research axioms or unchecked
native-evaluation proof steps. `lean4checker --fresh` was unavailable
on this host.
