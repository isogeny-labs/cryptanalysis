# Proof map

| Mathematical result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| A right triple formed by an additive image equals the image of the corresponding left triple sum | `FoldedJoin.right_triple_from_left` | Additive commutative group, function additive on all pairs, and pointwise equality of three source states | Checked in Lean 4.34.1; no axioms |
| Folded target lookup is equivalent to the full target equality | `FoldedJoin.folded_target_lookup` | Additive commutative group; any function applied to the triple sum | Checked in Lean 4.34.1; no axioms |

`lean-toolchain` pins `leanprover/lean4:v4.34.1`; there are no external Lean dependencies. Command: `cd experiments/ecc2k130-ic-goal-20260929/n41_frobenius_folded_join_20261016 && lake env lean FoldedJoin.lean`. Output is retained in `lean_check.stdout` and `lean_check.stderr`. `lean4checker --fresh` is unavailable on this host. The theorem module contains no `sorry`, `admit`, custom claim axiom, or native proof evaluation.

The Lean statements cover the structural group implication. The concrete identification of coordinate-wise eighteenth Frobenius with the elliptic-curve group endomorphism is not in the Lean kernel; the producer and independent auditor check all 480 finite source states, and the auditor checks the recovered point sum and source-column conditions. The native 6×256 lookup implementation is additionally checked against the direct eighteenth-power computation for each input state and against the group sum for the recovered relation. Formalizing the finite field and curve implementation itself remains the open bridge for a fully formal end-to-end theorem.
