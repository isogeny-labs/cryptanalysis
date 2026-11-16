# First-hit proof map

Lean 4 v4.35.0-rc4 and Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9`.

| Result | Lean declaration | Hypotheses |
| --- | --- | --- |
| Select earliest hit from finite stage set | `hitStages`, `firstHit` | Arbitrary hit predicate on `Fin m` and execution type |
| First-hit time iff current hit and no earlier hit | `firstHit_eq_some_iff` | Arbitrary finite stage predicate |
| Live membership iff no earlier hit | `mem_live_iff_no_prior` | Finite execution space |
| Initial point equality iff scalar one | `initial_group_equality_iff_one` | Field/module and injective `s ↦ s • G` |
| Eligibility iff no distinct-form raw hit | `eligible_iff_no_raw_hit` | Finite field, affine form family |
| Prefix eligibility iff no earlier raw hit in full list | `eligible_prefix_iff_no_prior` | Prefix cutoff `k≤m` |
| Pointwise live/eligible bridge for execution-dependent forms | `mem_live_raw_iff_eligible_prefix` | Finite execution space and field |
| Actual group hit iff affine raw hit | `groupRawHit_iff_rawHit`, `dlp_group_raw_hit_iff` | Injective scalar-to-group map; complete actual label transcript for program theorem |
| Actual live set iff eligible visible prefix | `execution_live_iff_eligible_prefix` | `Program L 2 m`, finite scalar, group, label and encoding spaces; injective scalar-to-group map |
| Raw hit iff next-candidate root | `rawHit_iff_nextCandidates` | Finite field, full affine form list |
| Earliest actual hit iff eligible next-root | `execution_first_hit_iff_eligible_next` | Same finite execution and injectivity hypotheses |
| Stage and total first-hit mass conservation | `execution_stage_mass_flow`, `execution_total_mass_identity` | Finite scalar-and-encoding execution space |

`executionLabels`, `executionForms`, and `executionHit` construct the
observed labels, reconstructed forms, and actual group hit predicate for
one execution. The actual-run theorem includes the first two seed forms,
so stage 1 accounts for `G = Q`.

Every declaration above has a `#print axioms` receipt in `formal/build-output.txt`.
The only dependencies listed are `propext`, `Classical.choice`, and
`Quot.sound` where applicable. There are no placeholders, custom research
axioms, or unverified native evaluation in the new module.
`lean4checker --fresh` is unavailable on this host.
