# Proof map

Toolchain: `formal/lean-toolchain`; dependency revisions: `formal/lake-manifest.json`. Build with `cd experiments/xedni-group-fiber-bound-20261116/formal && lake build GroupFiberBound`. The build output and `#print axioms` receipts are kept in `formal/build-output.txt`.

| Mathematical result | Lean declaration | Hypotheses | Status |
| --- | --- | --- | --- |
| Eligible scalar fibers have equal weight | `XedniGroupFiberBound.eligible_group_fiber_eq` | Finite field and group/label sets; module action; injective scalar map; both scalars eligible for the same affine forms and labels | Checked |
| Weighted candidate bound in one fixed bucket | `XedniGroupFiberBound.weighted_group_next_candidate_bound` | Same ambient assumptions; arbitrary next affine form | Checked |
| Adaptive execution prefix encoding fiber equals reconstructed group fiber | `XedniGroupFiberBound.adaptive_encoding_fiber_eq_group_fiber` | Typed label-adaptive program; prefix length at least two; fixed scalar and visible labels | Checked |
| Total program first-hit probability bound | None yet | Requires summing the bucket inequality through `execution_live_card_eq_bucket_mass` and `execution_hit_card_eq_bucket_mass` | Open |

The checked declarations use Lean's standard `propext`, `Classical.choice`, and `Quot.sound` foundations. No custom research axioms or admitted proofs are used. The module prints each new declaration's axioms after the proof.
