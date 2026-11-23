# Proof map

The producer's two-sign enumeration uses simultaneous sign reversal. The
identity `-(a+b)=(-a)+(-b)` is formalized as `PairSigns.mirrored_sum` in
[PairSigns.lean](PairSigns.lean), under the sole assumption that the point
group is an additive commutative group. Lean 4.34.1 is pinned in
[lean-toolchain](lean-toolchain); `lean PairSigns.lean` succeeds and
`#print axioms` reports only standard `propext` in [lean_check.log](lean_check.log).

The specific ECC2K-130 point set and its injective two-slot sum map are
finite computational results. The producer enumerates all signed inputs;
the independent audit rebuilds each slot and enumerates the full Cartesian
product directly. A kernel proof of the binary-curve implementation and all
1,132,096 pair inequalities is not included. `lean4checker --fresh` was
unavailable in this environment.
