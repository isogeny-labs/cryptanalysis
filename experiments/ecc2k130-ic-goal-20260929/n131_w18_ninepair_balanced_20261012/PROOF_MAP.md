# Balanced nine-pair addition proof map

`BalancedTree.nine_sum_eq_serial` in [BalancedTree.lean](BalancedTree.lean)
proves, for every type `G`, binary operation `add`, and nine elements, that
the eight-link balanced tree and serial left fold have equal outputs if
`add` is associative. This is the exact tree implemented by `TREE` in
`balanced.py`: four first-level pair additions, two second-level additions,
one third-level addition, then addition of the ninth pair output. The
theorem has no commutativity, identity, characteristic, curve, or subgroup
assumption. Its use for elliptic-curve points requires the standard
associativity of point addition.

`lean-toolchain` pins Lean 4.34.1. Run `lean BalancedTree.lean`; the saved
`lean_check.txt` includes the `#print axioms` audit. Its only reported Lean
foundation is `propext`. `lean4checker --fresh` was unavailable on this host.

The prior `NinePairOrbit.relation_pullback` theorem in the adjacent orbit
experiment conditionally transports a valid raw-point relation through
inverse Frobenius and cofactor projection. Its concrete binary-curve and
factor-base bridge remains open. The present theorem establishes the tree
topology identity; it does not by itself prove the Boolean XCNF link encoding
equivalent to the full curve group law. That link is checked on the complete
constructed N131 assignment, including all eight branch bits, and any
ordinary solver model still requires independent signed-point replay.

The circuit requires every intermediate reciprocal to represent a finite
point with nonzero affine `x`. Therefore the two topologies can exclude
different exceptional intermediate sums despite sharing the same nine
pair domains and exact distinct-column shield. The uniform source census
remains an upper bound for either circuit, not a fixed-point yield measure.
