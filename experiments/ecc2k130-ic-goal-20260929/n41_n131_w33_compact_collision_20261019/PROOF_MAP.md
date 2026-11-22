# Proof map for the W33 collision and all-aligned circuit

| Claim | Formal or replay evidence | Exact boundary |
| --- | --- | --- |
| Frobenius is additive in characteristic two | `FoldedCollision.frob_add` in [FoldedCollision.lean](FoldedCollision.lean) | Any field with `x+x=0`; any natural Frobenius exponent |
| Endpoint collision is an affine equation in two source parameters | `FoldedCollision.collision_linearized` | Same field hypothesis; fixed seed and endpoint choices |
| W33 ranks, solution kernels, and 8,331 valid collision pairs are exact for the declared polynomial basis | [collision_result.json](collision_result.json), [filter_result.json](filter_result.json), and independent [verification_result.json](verification_result.json) | All 131 Frobenius powers and four endpoint choices; 32 free code bits; source trace validity checked in Sage |
| Sorting five equal-domain, equal-rotation pairs preserves every valid group sum | `AllAlignedOrder.sort_preserves_sum` and `sort_preserves_validity` in the prior [module](../n41_n131_all_aligned_20261019/AllAlignedOrder.lean) | Abstract commutative group and shared validity predicate; concrete folded-column distinctness checked by finite exclusions |
| N131 constructed assignment corresponds to five curve pair points summing to its raw target | [control_replay.json](control_replay.json) | Independently rebuilt using the checked Sage curve group; ten distinct signed-Frobenius orbit IDs |

The copied `FoldedCollision.lean` is byte-identical to the pinned prior
module and built under `leanprover/lean4:v4.34.1`. Its `#print axioms`
output in [lean.stdout](lean.stdout) contains only `propext`,
`Classical.choice`, and `Quot.sound`. The 524 concrete field matrices and
source-validity census are finite computational certificates with an
independent Sage replay; they are not kernel-formalized as a single Lean
theorem. The public query's bounded status is an empirical receipt.
