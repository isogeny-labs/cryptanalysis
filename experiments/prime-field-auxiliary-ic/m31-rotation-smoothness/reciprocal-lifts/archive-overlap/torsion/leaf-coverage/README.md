# Descendants of reciprocal-smooth nodes in the depth-five M31 fiber

The level-two hit at bound 211 selects four original coordinates.
Exactly one lifts on the public target cubic; its canonical point is
(98625645, 439352624). Lift.lean proves that these are the only four
possible nonzero preimages over the field, exhibits the square root,
and uses Euler's criterion to exclude the other three coordinates.
The archived basis contains 17 columns.

For the wider finite search a selection accepts a leaf if any of its five
ancestor sibling pairs meets the smoothness bound in a chosen compatible
orientation. Each level may be disabled, use one of the two scale signs,
or (in the expanded family) use both. Rotating a compatible scale preserves
orbit membership. A schedule uses one common inclusive smoothness bound.
This search does not change the auxiliary chain, shift, or field.

In both families the earliest bound covering all 17 columns is 1811. Every
full-coverage schedule also retains every one of the 32 original coordinates.
Thus these filters cannot skip a target-cubic lift test while preserving this
entire archived basis. This is an exact statement about the archived fiber
and the defined schedule families, without a timing inference.

Run python3 audit.py to reconstruct all leaf masks from the pinned manifest
and test each schedule at each of the 30 admission thresholds. For each
orientation the admission threshold is the larger of the two least rotation
smoothness bounds. result.json records the first full-coverage bound and
each later strict improvement in retained leaf count. Run python3 verify.py
with SymPy for an independent leaf-first replay. It computes each leaf's
first admission under a schedule and checks the first bound admitting all
17 required columns. Acceptances are monotone at higher bounds. Replay
Lift.lean in the Lean 4.34.1 mathlib environment.
