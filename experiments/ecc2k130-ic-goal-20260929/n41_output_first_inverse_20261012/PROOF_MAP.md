# Proof map: reciprocal linear-span gate

| Result | Lean declaration or receipt | Hypotheses and status |
| --- | --- | --- |
| A binary-linear test that vanishes on a sampled spanning set vanishes on every vector in the trace kernel | `ResidualSpan.no_additional_linear_test` in `ResidualSpan.lean` | Checked in Lean 4.34.1 for XOR-linear tests on natural-number bit vectors, conditional on an explicit XOR representation of every trace-zero vector by sample members. `#print axioms` reports only `propext`. |
| A binary-linear test vanishes on any XOR sum of members on which it vanishes | `ResidualSpan.linear_test_zero_on_xor_sum` | Checked in the same module; only `propext`. |
| Every exact suffix reciprocal has trace zero and 4,096 selected reciprocals have rank 40 over `GF(2)` | `suffix_analysis.json`, `verify.py` | Checked Sage computes the declared field, source points, sums, reciprocals, and rank. Separate Python elimination rechecks rank, trace, and canonical pair indices. The finite field/source-to-Lean representation and machine-checked rank certificate are not yet formalized; thus the full concrete rank theorem remains open in Lean. |
| The sampled residuals have rank and affine rank 40; the archived positive/negative statuses match | `analysis.json`, direct/S3 receipts, `verify.py` | Checked Sage reconstructs all 1,712 points and reciprocal values; separate Python field multiplication and elimination replay the values and rank. The concrete bridge remains outside Lean. |

Pinned toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`.
Run `lean ResidualSpan.lean` in this directory; `lean_check.txt` records both
`#print axioms` outputs. `lean4checker --fresh` was not available on this
host. The Lean theorem is a faithful structural implication; its spanning
hypothesis is supplied by the finite rank audit, not silently assumed as a
proved property of the frozen curve in Lean. The readable proof is in
`RESULT.md`.
