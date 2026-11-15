# Proof map

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| Two distinct coefficient directions cannot share an admissible hit | `XedniCoefficientFamily.distinct_directions_force_zero` | Any field, two coefficient pairs with nonzero determinant, and two simultaneous linear relations. Checked in the pinned build. The application excludes the common zero-scalar pair. |
| A zero-sum pair does not hit distinct sampled scalars | `XedniCoefficientFamily.zero_sum_pair_relation` | Any field, nonzero coefficient and distinct sampled scalars. Checked in the pinned build. |
| Each nonzero-sum direction has `r−1` admissible hits | Open finite-cardinality bridge | Written affine-line proof in `RESULT.md`; exhaustive modular audit for the eight specified subgroup orders. A Lean `Finset.card` or explicit bijection between the relation line and the field, followed by removal of `(w,w)`, is still needed for a fully formal statement. |

The field list, input law, generator, public point, and scalar replay are
bound to the frozen `protocol.json` and result digests. The Lean proof checks
the algebraic disjointness; the per-field counts are independently replayed
computational evidence.
