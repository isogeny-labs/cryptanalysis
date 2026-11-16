# Actual group hits obey the label-fiber collision bound

The checked `next_group_hit_mem_collision_set` theorem connects an actual
group-oracle hit to the symbolic affine collision set. It assumes the
scalar-to-generator map is injective and the label-selected new form differs
from every prior form. The checked `actual_group_hit_fiber_mass_le` theorem
then bounds the encoding mass of these actual group hits on a fixed
collision-free label fiber by `(n+1)²` times one eligible scalar's encoding
count, for `n` prior forms and one new form. The new form may depend on the
complete prior visible label tuple.

The frozen Z/7 replay used prior group points `(G,wG)` with `G=1`, six
eligible scalars `w≠1`, and all 7! bijective encodings. It chose `G+wG`
when the first label was smaller and `wG+wG` otherwise. Across **30,240**
scalar-encoding pairs, actual group equality and symbolic affine equality
agreed on every event: **7,560** hits and **zero** mismatches. The result
retains one row per 42 ordered visible-label pairs. An independent group
table audit reproduced both branch candidate sets, `{0}` and `{0,4}`, and
every row's count.

This closes the one-step representation gap identified in PR #1635. The
next proof step is an induction over oracle commands and label-dependent
choices, with explicit accounting at the first collision. Curve-coordinate
observations require a separate model of the rational-lift procedure.

The formal project pins Lean v4.35.0-rc4 and Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9. `lake build
GroupTraceInvariant` passed 3,141 jobs; all six new `#print axioms`
reports contain standard Lean foundations only. `SEAL.sha256` binds the
protocol, source, 42-row replay, independent audit, build receipt, and
proof map.
