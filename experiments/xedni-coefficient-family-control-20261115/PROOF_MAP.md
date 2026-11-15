# Proof map

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| Two distinct coefficient directions cannot share an admissible hit | `XedniCoefficientFamily.distinct_directions_force_zero` | Any field, two coefficient pairs with nonzero determinant, and two simultaneous linear relations. Checked in the pinned build. The application excludes the common zero-scalar pair. |
| A zero-sum pair does not hit distinct sampled scalars | `XedniCoefficientFamily.zero_sum_pair_relation` | Any field, nonzero coefficient and distinct sampled scalars. Checked in the pinned build. |
| Each nonzero-sum direction has `|F|−1` admissible hits | `XedniCoefficientFamily.admissible_hit_count` | Any finite field, `a≠0`, `b≠0`, and `a+b≠0`; sampled scalars are `w−t₁`, `w−t₂` and admission means both nonzero and distinct. Checked in the pinned build. |
| Projection parameterizes a relation line | `XedniCoefficientFamily.relation_iff_second`, `lineHitEquiv`, `line_hit_count` | Any field with `b≠0`; the finite count also assumes `Fintype F`. Checked in the pinned build. |
| A relation-line point with `t₁≠w` is admissible | `XedniCoefficientFamily.line_hit_admissible` | Any field with `a≠0`, `a+b≠0`. Checked in the pinned build. |

The field list, input law, generator, public point, and scalar replay are
bound to the frozen `protocol.json` and result digests. The exact per-field
counts are also independently replayed computational evidence. The union
count `13(r−1)` uses the checked per-direction count and disjointness
lemmas plus the audited fact that this frozen family has 13 nonzero-sum,
pairwise distinct directions; that finite-family corollary is not separately
stated as a Lean theorem.
