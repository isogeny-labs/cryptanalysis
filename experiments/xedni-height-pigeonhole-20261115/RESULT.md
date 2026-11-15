# A checked pigeonhole bridge to bounded xedni witnesses

The Lean theorem `XedniHeightPigeonhole.bounded_relation_of_card_lt` proves the finite collision step in the bounded-witness argument. Let `box` be a finite set of integer coefficient vectors, each with coordinate magnitude at most `K`. Let `values` contain every lifted sum `Σ_i a_i P_i` for `a ∈ box`. If `|box| > |values|`, then two different vectors have the same sum. Their difference is a nontrivial relation with every coefficient bounded by `2K`.

The companion theorem `bounded_witness_of_card_lt_on_dependence` packages the same result when the cardinal inequality is available only for dependent lifted tuples. Its conclusion has the existential bounded-witness shape used by the corrected xedni reduction obstruction.

The extension counts the full coefficient box exactly: `coefficientBox_card` gives `(2K+1)^r` vectors. `bounded_relation_of_height_ball_count` therefore states a concrete threshold: if all box sums lie in a certified finite set with fewer than `(2K+1)^r` elements, a nontrivial relation exists with coefficients bounded by `2K`. The theorem does not assume dependence separately.

The rank-and-torsion extension makes that finite value set concrete. `latticeValues_card_le` counts values represented by one of `T` listed torsion elements plus a rank-`d` coordinate vector of radius `K`, obtaining at most `T(2K+1)^d` values. `bounded_relation_of_lattice_representation` then yields a relation of coefficient radius `2L` whenever every radius-`L` sum of the lifted points has such a representation and `T(2K+1)^d < (2L+1)^r`. The count is valid even if the listed basis is redundant; in an arithmetic application, `d` must be linked to the subgroup rank and the coordinate radius `K` must follow from height bounds.

`rank_gap_count` gives an explicit sufficient radius when the coordinate bound is linear: if `d < r`, `K <= cL`, and `L > T(2c+1)^d`, then `T(2K+1)^d < (2L+1)^r`. `bounded_relation_of_rank_gap` applies this inequality to the represented lifted sums. Thus any fixed rank drop and fixed torsion/coordinate constants give a finite coefficient threshold, while the height-to-coordinate premise remains visible.

## Proof and mathematical inputs

The proof applies `Finset.exists_ne_map_eq_of_card_lt_of_maps_to` to the finite evaluation map `a ↦ Σ_i a_i P_i`. The collision gives `a ≠ b` and equal sums. Function extensionality supplies a coordinate at which `a_i − b_i ≠ 0`; integer scalar and sum subtraction give `Σ_i (a_i − b_i)P_i = 0`; `Int.natAbs_sub_le` bounds each new coefficient by `2K`. These are structural implications, checked in Lean for arbitrary additive abelian groups and any finite number of lifted points.

For the [original xedni analysis](https://pages.cpsc.ucalgary.ca/~jacobs/PDF/xedni.pdf), Lemma 4.1 uses canonical height, the regulator, the discriminant comparison, Lang's lower-height conjecture, and a torsion bound to make the number of possible lifted sums smaller than the number of short coefficient vectors. The present theorem takes the resulting finite value set and strict cardinal inequality as explicit hypotheses. Formalizing those arithmetic estimates for the paper's lift family is the next proof step. The fixed-list finite-field sample count is separately checked in [the sampled-witness extension](../xedni-sampled-witness-20261115/RESULT.md).

## Proof map and verification

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| A finite image collision gives a bounded relation | `bounded_relation_of_card_lt` | `values.card < box.card`, all box sums in `values`, all box vectors bounded by `K` |
| Dependence supplies a bounded witness when it gives the count inequality | `bounded_witness_of_card_lt_on_dependence` | Dependence-conditional count inequality and the same box/value hypotheses |
| Exact short-vector count | `coefficientBox_card` | All `r` integer coordinates range from `-K` to `K` |
| Box entries obey the declared radius | `coefficientBox_bounded` | Membership in the full coefficient box |
| Concrete height-ball threshold | `bounded_relation_of_height_ball_count` | Every box sum belongs to `values`; `values.card < (2K+1)^r` |
| Rank-and-torsion value count | `latticeValues_card_le` | `T` listed torsion elements and radius-`K` coordinate vectors of length `d` |
| Collision from bounded lattice coordinates | `bounded_relation_of_lattice_representation` | Every radius-`L` lifted sum has a listed torsion-plus-coordinate representation; `T(2K+1)^d < (2L+1)^r` |
| Explicit rank-gap inequality | `rank_gap_count` | `d < r`, `K <= cL`, `L > T(2c+1)^d` |
| Relation at the rank-gap threshold | `bounded_relation_of_rank_gap` | The preceding inequality's hypotheses and bounded-coordinate representation of every short lifted sum |

The project pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. The saved `lake build HeightPigeonhole` output and `#print axioms` records are sealed by SHA-256 hashes and checked by `verify.py`. All nine declarations use only `propext`, `Classical.choice`, and `Quot.sound`. The source has no admitted proof, custom axiom, native evaluation, or kernel bypass. `lean4checker --fresh` was unavailable on this host.
