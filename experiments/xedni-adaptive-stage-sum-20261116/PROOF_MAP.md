# Adaptive stage aggregation proof map

Lean 4 v4.35.0-rc4; Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Mathematical result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Live executions split into continuations and first hits | `live_step_partition` | Finite execution type and first-hit-time function |
| The two parts are disjoint | `live_hit_disjoint` | Same execution type and first-hit-time function |
| Cardinal flow equation | `stop_flow` | Same; no separate flow hypothesis |
| Terminal live plus all first hits equals initial count | `stopped_mass_identity` | Same, for any finite stage count |
| Weighted bound across all visible buckets at one stage | `stage_bucket_mass_bound` | Finite field, label and bucket types; fixed old-form length; each bucket's first-hit set contained in eligible next candidates |
| Aggregate square-over-gap count bound | `aggregate_bucket_bound` | `N≤m`, each old-form length `n(k)≤m`, first-hit inclusion, and exact live/hit execution-to-bucket mass identities at each stage |

`liveSet` and `hitSet` are definitions indexed by the earliest informative
hit time. They make the stopping partition exact even when an execution
never hits. The stage theorem sums the already checked
`weighted_first_hit_bound` over bucket keys. The aggregate theorem then
uses the resulting per-stage bound and the stopping ledger.

The whole-program bridge remains open at the two mass identities in
`aggregate_bucket_bound`: every live or first-hit pair of scalar and
encoding must occur in exactly one compatible visible-prefix fiber with
forms selected by that same observed prefix. The Z/7 audit checks those
identities for one adaptive program, including known repeats, but does not
supply the universal Lean derivation. The theorem also starts with an
initial execution space; a full public-input statement must account for
the initial `G=Q` event and specify the adversary's output rule.

`lake build AdaptiveStageSum` completed 3,146 jobs. All eight new
`#print axioms` receipts contain only `propext`, `Classical.choice`, and
`Quot.sound`. The theorem source has no placeholder, custom research
axiom, or native evaluation. `lean4checker --fresh` is unavailable on
this host.
