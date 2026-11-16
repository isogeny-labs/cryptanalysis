# Label-conditioned collision proof map

Lean toolchain v4.35.0-rc4; Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Result | Lean declaration | Hypotheses |
| --- | --- | --- |
| Count encodings yielding one visible label tuple | `fiberCount` | Finite scalar and label sets; target-indexed trace |
| Equal encoding counts across target scalars | `fiber_count_eq` | Both target traces injective; bijective random encodings; fixed label tuple |
| Upper bound on next-collision encoding mass | `collision_fiber_mass_le` | Finite field; eligible scalar set with injective trace for each member; one eligible reference scalar; next affine forms determined by visible label tuple |

The last theorem intersects eligible scalars with the informative collision
set for the label-selected affine forms. The imported symbolic theorem bounds
that set by at most `m*m` for `m` forms. The imported random-label theorem
equates the number of bijective encodings in each eligible scalar's label
fiber. Summing equal weights over the candidate intersection gives the mass
bound. Symbolically identical forms are excluded from the informative
collision set, consistent with the imported theorem.

This is a fixed-label-fiber statement, conditional on the prior trace being
collision-free. It supplies the posterior-count step for an adaptive oracle
argument. A checked link is still needed to show that `forms labels` encodes the same
prior trace and next oracle output as `trace`; that representation invariant
is required when applying the mass bound to an actual oracle execution. A
proof across all transcript depths also needs a recurrence that handles entry
into the first-collision event. The abstract encoding model does not include
finite-field curve coordinates.

`lake build LabelConditionedCollision` completed 3,140 jobs. `#print axioms`
for the three new declarations lists only `propext`, `Classical.choice`, and
`Quot.sound`. The module has no `sorry`, `admit`, custom research axiom, or
native evaluation. `lean4checker --fresh` was unavailable on this host.
