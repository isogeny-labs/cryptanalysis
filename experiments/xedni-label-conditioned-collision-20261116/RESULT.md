# Collision-free labels give equal scalar encoding weights

The checked `fiber_count_eq` theorem says that any two target scalars whose
prior group traces are injective have the same number of bijective encodings
for a specified visible label tuple. The checked `collision_fiber_mass_le`
theorem then bounds the encoding mass of eligible scalars whose next
label-selected affine forms collide by `m²` times one scalar's label-fiber
weight, where `m` is the number of forms. The symbolic forms may depend on
the complete visible label tuple. This joins the random-label coupling to
the pair-candidate collision bound at one transcript fiber.

The complete Z/7 control used prior forms `(1,w)`, six eligible scalars
`w≠1`, and all 7! bijective encodings. The next form was `w+1` when the
first label was smaller than the second, and `2w` otherwise. Each of the
**42** ordered distinct label pairs had **120** encodings per eligible scalar,
or **720** eligible scalar-encoding pairs. In the first branch the next form
collided for one eligible scalar and contributed **120** encoding pairs per
label tuple. In the second it collided for two and contributed **240**.
The exact aggregate was **7,560** collisions among **30,240** eligible
scalar-encoding pairs, a conditional fraction of **1/4**. The independent
audit derived the candidate sets `{0}` and `{0,4}` algebraically and checked
every saved row.

The theorem is conditional on the prior trace being injective and on
target-dependent choices coming from abstract labels. The next step is a
checked invariant connecting the symbolic forms to the oracle's group trace,
followed by a recurrence across transcript depths that includes the
first-collision branch. A public-coordinate rational-lift algorithm needs a
separate observation model.

The formal project pins Lean v4.35.0-rc4 and Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9. `lake build
LabelConditionedCollision` passed 3,140 jobs; the new `#print axioms`
reports contain standard Lean foundations only. `SEAL.sha256` binds the
protocol, sources, full 42-row census, independent audit, build receipt,
and proof map.
