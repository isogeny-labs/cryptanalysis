# First-collision mass ledger proof map

Lean toolchain v4.35.0-rc4; Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Live mass never exceeds initial mass | `live_le_initial` | At each stage, next live mass plus first-hit mass equals current live mass |
| Terminal live plus disjoint first-hit buckets equals initial mass | `first_hit_mass_identity` | Same conservation equality for all stages |
| Aggregate first-hit bound over `N` stages | `first_hit_total_bound` | Conservation plus `d * firstHit(k) ≤ c * live(k)` at each stage |
| Sum equal-weight transcript buckets without pooling | `uniform_bucket_count_bound` | Every bucket has at least `d` eligible scalars, at most `c` next-hit scalars, and a nonnegative common encoding weight |
| Conditional square-over-gap bound | `conditional_square_over_gap` | `m² < q`; `m` stages of conservation; explicit per-stage condition `(q-m²) * firstHit(k) ≤ m * live(k)` |

The bucket theorem multiplies scalar counts by the number of encodings per
scalar in each visible-prefix bucket. It allows different weights across
buckets and establishes the summed inequality without pooling them. The stage
ledger then partitions executions by their **first** hit, so each execution
is charged once. The conditional corollary substitutes `d=q-m²`, `c=m`,
and `N=m` into that ledger. Its per-stage inequality is a hypothesis,
not an outcome of the preceding generic-group modules.

To discharge that hypothesis for an actual adaptive oracle program, the
next formal step must establish for every live prefix: a lower bound on
eligible scalars, an upper bound on the *new* informative collision
candidates, equal encoding weight per eligible scalar, and a partition of
all live executions by visible prefix. The earlier checked modules supply
form reconstruction, a per-transcript candidate set, and one-step label
coupling, but those pieces are not yet assembled into this universal
per-stage premise. Symbolically identical forms must be handled as known
repeats. Concrete curve coordinates are outside this abstract-label model.

`lake build FirstCollisionLedger` completed 3,144 jobs. All five new
`#print axioms` receipts contain only standard Lean foundations (`propext`,
`Classical.choice`, `Quot.sound` where applicable). The source contains no
placeholder, custom research axiom, or native evaluation. `lean4checker
--fresh` was unavailable on this host.
