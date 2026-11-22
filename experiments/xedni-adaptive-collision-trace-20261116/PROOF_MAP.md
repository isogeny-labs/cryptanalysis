# Equality-adaptive symbolic collision proof map

Lean toolchain: `v4.35.0-rc4`. Mathlib revision:
`021c46bdd042f67b538b9f9871d556a93713a9a9`.

| Result | Lean declaration | Exact assumptions |
| --- | --- | --- |
| Every all-miss Boolean transcript is unique at its length | `miss_history_unique` | Each element of the history is `false` |
| Pre-hit strategy output is the negative-path form | `prehit_strategy_fixed` | Strategy is a function only of that Boolean history |
| Distinct equal-slope forms do not collide | `same_slope_distinct_ne` | Field, same slope, distinct forms |
| Public point equality reflects scalar equality | `public_group_collision_iff` | Additive field module and injective scalar-to-point map at `G` |
| Informative collision identifies one candidate | `collision_iff_candidate` | Field and unequal slopes |
| Exact success set is the image of negative-path pair candidates | `adaptive_collision_success_set` | Finite field, Boolean-history strategy, all informative pairs among the first `n` forms |
| Coverage at most pair count and `n²` | `adaptive_collision_card_le_pairs`, `adaptive_collision_card_le_square` | Same |

The oracle reports one bit after each new form: whether it equals any
earlier form with a different slope. A hit stops the procedure. The formal
success set is the union of informative collisions along the unique pre-hit
trace; `miss_history_unique` and `prehit_strategy_fixed` justify that trace
for every target that has not yet hit. Symbolically identical forms are
uninformative. Distinct equal-slope forms cannot collide.

The theorem does not formalize a random-encoding generic-group oracle or a
strategy that reads concrete curve coordinates or group-element labels.
Those observations can affect the selected forms before a collision and
need a coupling or information argument of their own.

`lake build AdaptiveCollision` completed 3,138 jobs. All eight
`#print axioms` reports list only standard Lean foundations (`propext`,
`Classical.choice`, `Quot.sound` where used). No `sorry`, `admit`, custom
research axiom, or native evaluation occurs. `lean4checker --fresh` was
unavailable on this host.
