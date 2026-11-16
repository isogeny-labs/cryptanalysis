# Group-trace collision invariant proof map

Lean toolchain v4.35.0-rc4; Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Actual prior group trace from affine forms | `groupTrace` | Field, additive group module, generator, indexed forms, target scalar |
| A new group hit is an informative affine collision | `next_group_hit_informative` | Injective scalar-to-`G` map; new form differs from every prior form; actual group hit |
| Actual hit belongs to symbolic candidate set | `next_group_hit_mem_collision_set` | Same, plus finite field and explicit appended form |
| Count bijective encodings of a group trace label tuple | `groupFiberCount` | Finite group and finite label set; the count is nonzero only when their cardinalities agree |
| Select eligible scalars with an actual next group hit | `actualGroupHits` | Finite field, affine prior and label-selected next form |
| Bound actual-hit label-fiber encoding mass | `actual_group_hit_fiber_mass_le` | Scalar-to-`G` injective; eligible reference scalar; collision-free actual prior trace for every eligible scalar; selected next form distinct from each prior form |

The central proof first reflects equality of group points to equality of
field scalars using the injective scalar map. Equal-slope, distinct affine
forms cannot meet, so an actual hit has an unequal-slope pair in the
symbolic collision set. The imported collision theorem bounds that set by
`(n+1)^2` for `n` prior forms and one new form. The imported random-label
coupling equates encoding counts across eligible collision-free traces.
Summing those equal fiber weights over the actual-hit subset yields the
stated bound.

The theorem is one adaptive step at a fixed prior symbolic node. A complete
generic-group lower bound still needs a checked induction that constructs
the affine forms through every addition and scalar operation, tracks the
transcript tree, and accounts for entry into the first-collision branch.
Concrete elliptic-curve coordinates are outside this random-label model.

`lake build GroupTraceInvariant` completed 3,141 jobs. The six new
`#print axioms` reports list only `propext`, `Classical.choice`, and
`Quot.sound` where used. No placeholder or custom research axiom occurs.
`lean4checker --fresh` was unavailable on this host.
