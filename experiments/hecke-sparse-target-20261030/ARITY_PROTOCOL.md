# Continuation: reuse the original pair index for higher-arity target queries

Fixed after trace-growth and matched-base controls. Exploratory on the same
large-f6 public target; no fresh-target or performance claim. Preserve all
previous attempts and costs.

Rebuild exactly the original signed base plus zero and its pair index. Use
sorted point order (zero first), retain the first witness per pair sum, and
check all propagated labels. Record the pair-index point-set digest, actual
entry count and construction additions; do not build a new larger base.

Three-term arm: for each signed base point D (zero first), try Q-D in the
existing pair index. Cap at the number of signed base points plus zero65.
Four-term arm: for the first256 pair-sum points T in sorted order (zero
first), try Q-T in the same index. These are independent arms; do not carry
failed work from one into the other. Recover a scalar and replay it in both
curve implementations if a match occurs. Retain capped failures.

Compare index/setup and query counters with the original256-offset arm and
the201-point growth arms. All share the same charged original generic
base-log bootstrap. This is generic higher-arity decomposition, not algebraic
PDP progress. A success is a finite target-oracle implementation improvement
candidate; fresh single-target checks, complete phase costs, a calibrated
benchmark host and matched strong rho remain required for a speed claim.
Apply the same600-second and checkpoint rules. Stop after these two arms.
