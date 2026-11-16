# Stage-hit proof map

Lean 4 v4.35.0-rc4; Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9`.

| Mathematical result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Eligible scalar iff evaluated old-form equality matches symbolic form equality | `eligible_iff_eval_pattern` | Finite field, affine form family, scalar; known repeats included |
| New informative scalar equality iff next-candidate membership | `next_hit_iff_candidates` | Finite field, old form family, new form, scalar |
| Actual old group equality pattern iff eligibility | `group_pattern_iff_eligible` | Additive module, injective scalar multiplication by `G` |
| Actual new informative group equality iff candidate membership | `group_next_hit_iff_candidates` | Same module and injectivity condition |
| Actual adaptive program stage event iff eligible candidate root | `dlp_stage_hit_iff_eligible_next` | `Program L 2 m`; complete actual label transcript; `2≤k<m`; injective scalar multiplication by `G`; typed prefix extraction |

The central theorem tracks the actual group program and the forms
reconstructed from the same visible label transcript. Prior module
`TypedPrefixProgram` contains the prefix extraction and exact actual/symbolic
encoding-fiber equality. The structural bridge here follows from those
declarations and the group equality lemmas above.

`lake build StageHitEquivalence` builds the theorem module. Each new
declaration has a `#print axioms` receipt in the saved build output. The
standard foundations are `propext`, `Classical.choice`, and `Quot.sound`
where applicable. `lean4checker --fresh` is unavailable on this host.
