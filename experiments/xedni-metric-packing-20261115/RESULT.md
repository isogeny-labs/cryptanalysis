# A basis-free metric-cover bridge for xedni height balls

The checked theorem `XedniMetricPacking.bounded_relation_of_labelled_metric_cover` gives a basis-free route from geometric counting to a bounded integer relation. Let `values` be the distinct sums from the full radius-`K` coefficient box. Project them to a metric space and cover the projected values by a finite set of radius-`ε` balls. If distinct projected values are more than `2ε` apart, each center serves at most one projected value. A finite label set distinguishes values in the same projection fiber. The resulting bound is

`|values| <= |centers| * |labels|`.

When `|centers|*|labels| < (2K+1)^r`, the existing finite pigeonhole theorem yields a nontrivial lifted relation with integer coefficients bounded by `2K`. The label hypothesis is exact: equal projections and equal labels must imply equal original values. In a canonical-height application, the projection can target the torsion-free Mordell–Weil quotient and labels can account for torsion fibers. The project does not identify an elliptic-curve quotient or a concrete cover count; those remain the arithmetic and geometric steps to establish for the selected lift family.

The simpler `bounded_relation_of_metric_cover` handles a metric that already separates all distinct lifted values. Both versions use only finite covers and the triangle inequality, with no chosen lattice basis.

## Proof map

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| One value per small covering ball | `separated_values_card_le_centers` | Every value lies within `ε` of a listed center; distinct values have distance `>2ε` |
| Collision from an injective metric cover | `bounded_relation_of_metric_cover` | The preceding cover and separation for all distinct box sums; center count `<(2K+1)^r` |
| One labelled value per small covering ball | `labelled_values_card_le_centers` | Finite labels; equal projection and label identify a value; distinct projections have distance `>2ε`; finite cover |
| Collision from a torsion-aware cover | `bounded_relation_of_labelled_metric_cover` | Labelled cover of all distinct box sums; `|centers|*|labels| < (2K+1)^r` |

`HeightPigeonhole.lean` is an exact source copy from PR #1560 commit `2ac7ee29f73bdaad8c9571eac158c81dd72e1498`, with its hash pinned in `DEPENDENCIES.json`. The formal project pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build MetricPacking` passed; `verify.py` checks all four new and nine imported `#print axioms` records against standard Lean foundations (`propext`, `Classical.choice`, `Quot.sound`) and seals the source and output hashes. `lean4checker --fresh` was unavailable on this host.

The next experiment is to derive or measure a finite covering-center bound for the relevant canonical-height ball at fixed rank and minimum positive height, retaining the torsion-fiber count. This would replace the coordinate-radius premise in the xedni rank-gap route.
