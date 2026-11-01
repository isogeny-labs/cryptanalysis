# H111 independent replay: first-layer p² halving carry

This draft freezes an independent replay before the canonical implementation runs.

For `Q=[k]G`, form `H=[(r+1)/2]Q`, lift `H,Q` by the coordinate-fixed
Hensel section, and measure `C₂(Q)=[2]s₀(H)-s₀(Q)` in the reduction kernel.
Exactly 24 public predicates of the formal coordinate are frozen as parity
candidates.  No formula may be added after observation.

The replay covers all 28 rows and 9,096 targets, independently recomputes the
carry and predicate scores, checks random-section, matched-label,
coordinate-isomorphism, torsion-section, and generic controls, and requires
complete parity-guided reconstruction plus EC verification for any exact row.

Status: protocol frozen; measurement not run. External novelty and any
subexponential claim are not established.
