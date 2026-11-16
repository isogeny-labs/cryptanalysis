# Adaptive zero-test proof map

The formal project pins Lean `v4.35.0-rc4` and Mathlib commit
`021c46bdd042f67b538b9f9871d556a93713a9a9`.

| Mathematical statement | Lean declaration | Hypotheses |
| --- | --- | --- |
| One nonzero-sum scalar relation identifies one scalar | `XedniAdaptiveZeroTest.hit_iff_candidate` | Field `F`; `a+b≠0` |
| The same equivalence for public group points | `XedniAdaptiveZeroTest.group_hit_iff_candidate` | Field `F`; additive `F`-module; injective scalar-to-point map at `G`; `a+b≠0` |
| Exact success set of an adaptive one-bit strategy | `XedniAdaptiveZeroTest.adaptive_zero_test_success_set` | Finite field `F`; arbitrary strategy from prior Boolean answers to query; nonzero sum on each pre-hit query |
| At most `N` successful scalars in `N` tests | `XedniAdaptiveZeroTest.adaptive_zero_test_hit_bound` | Same; complete uniform target space gives success probability at most `N/|F|` |

The strategy's pre-hit transcript has `i` false answers at query `i`. It may
compute arbitrary functions of this transcript, but receives no other
target-dependent observation. The theorem identifies its exact success set
with the image of the `N` scalar candidates on that negative path. A hit
terminates the search. Group encodings, coordinates, timings, and curve-search
outputs are not inputs to this oracle model.

`lake build AdaptiveZeroTest` built all 3,138 jobs. The saved `#print axioms`
output for all four declarations lists only `propext`, `Classical.choice`, and
`Quot.sound`; source inspection finds no `sorry`, `admit`, `sorryAx`, custom
research axiom, or native evaluation. `lean4checker --fresh` was unavailable
on this host. The parent public-first PR contains a checked exact-order
certificate for the p=313 generator; the present source states the group
bridge with the precise injectivity premise instead of silently assuming it.
