# Equal-rotation source-order proof map

The first two N41 pair slots have the same Frobenius rotation and the
same source construction. Their pair-output roots enter the first-three
source F4 equation symmetrically. Exchanging their complete signed pair
states swaps their source codes, preserves the first-three group sum and
its reciprocal, and leaves the later fourth and fifth pair states and
the public target unchanged. Valid source pairs in those slots have
distinct codes under the frozen disjoint-column constraint, so exactly
one ordering satisfies `code0 < code1`.

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| Exact F4 polynomial symmetry in the first two roots | `OrderSymmetry.f4_swap` | Arbitrary commutative ring; kernel checked. |
| Equal-source predicates and F4 gate survive exchange | `OrderSymmetry.exchange_preserves_gate` | The two slots share a source predicate; kernel checked. |
| Two distinct natural-number codes have an increasing orientation | `OrderSymmetry.ordered_orientation` | Code inequality; kernel checked. |
| Full N41 curve/source/collision bridge | Open Lean bridge | Requires the exact `GF(2^41)` field, Koblitz pair-state map, equal rotation, disjoint-column implication of distinct codes, group sum, and the Boolean circuit interpretation. The frozen [builder](build.py) checks all 65,536 code pairs and the archived positive control; the baseline Sage replay supplies the original group witness. |

The actual theorem module is [OrderSymmetry.lean](OrderSymmetry.lean)
with pinned [Lean 4.34.1](lean-toolchain). `lean OrderSymmetry.lean`
returned exit code zero. [lean_check.log](lean_check.log) records
`#print axioms`; each declaration uses standard `propext`,
`Classical.choice` where applicable, and `Quot.sound`. No `sorry`,
`admit`, custom research axiom, or unverified native evaluation is used.
`lean4checker --fresh` was unavailable on this host.
