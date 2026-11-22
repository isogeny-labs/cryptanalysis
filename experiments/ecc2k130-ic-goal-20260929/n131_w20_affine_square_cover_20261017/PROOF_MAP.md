# Proof map

The Lean toolchain is pinned to `leanprover/lean4:v4.34.1` in
`lean-toolchain`. `lean AffineChart.lean` exited 0. `#print axioms` reports
`propext` for `map_two_bit_chart` and `propext, Classical.choice,
Quot.sound` for `pair_product_add`. The module contains no `sorry`, `admit`,
custom research axioms, or native evaluation.

| Result | Declaration or finite check | Exact scope |
| --- | --- | --- |
| Four-code affine chart passes through an additive source map | `AffineChart.map_two_bit_chart` | Any two additive commutative groups and a function with explicit additivity and zero hypotheses |
| Fixed-seed pair product `x(x+s)` is additive | `AffineChart.pair_product_add` | Any commutative ring with explicit characteristic-two assumption |
| Every weight-two group is a four-corner XOR affine square | `audit_v2.py` and `audit_result_v2.json` | Every frozen N131 W20 group in `groups_v2.tsv` |
| Every valid selected code occurs once | `audit_v2.py` reconstructs codes from the source support and checks disjoint union | All 132,045 frozen selected W20 codes |

The source-specific bridge uses the archived representation in which the
20-bit mask encodes an element of a binary-linear x subspace and the
fixed-seed partner is `mask XOR seed`. The checked source census supplies
membership and distinct folded columns; the Lean polynomial theorem gives
additivity of the corresponding pair product. Formalizing the exact
binary-field mask encoding and all source-table construction steps in Lean
remains open. The current finite audit checks code coverage and affine
geometry, not the full elliptic-curve output of each pair or an unpinned
public-target decomposition.
