# Proof map

Toolchain and dependency revisions are pinned in `formal/lean-toolchain` and `formal/lake-manifest.json`. `formal/build-output.txt` records `lake build AdaptiveTotalBound` and each new declaration's `#print axioms` output. The proofs use Lean's standard `propext`, `Classical.choice`, and `Quot.sound` foundations.

| Result | Lean declaration | Hypotheses and event | Status |
| --- | --- | --- | --- |
| Bucket mass decomposes into exact encoding fibers | `XedniAdaptiveTotalBound.bucketMass_eq_fiber_sum` | Finite scalar, encoding, and bucket types; arbitrary bucket function and accepted scalar sets | Checked |
| Pointwise fiber inequalities sum over all visible buckets | `XedniAdaptiveTotalBound.summed_fiber_bound` | Finite types and a bound in every bucket | Checked |
| Actual adaptive first-hit stage bound | `XedniAdaptiveTotalBound.execution_stage_weighted_bound` | Finite field/module/labels; bijective encodings; injective scalar map; typed label-adaptive program; `2≤k<m` | Checked |
| Aggregate late first-hit bound | `XedniAdaptiveTotalBound.execution_late_total_bound` | Same ambient assumptions; stages `2≤k<m` | Checked |

The first-hit event uses distinct affine forms that evaluate to the same group point. The encoded program starts from `G,w•G` and adds or subtracts previously computed points according to the visible label prefix. Extensions with additional information channels require formal semantics and a separate proof obligation.
