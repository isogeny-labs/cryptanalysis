# Factored hash for the j=0 rho orbit

## Frozen mechanism

The reference `glv_class_reduce` hashes each of six successive powers of
`psi(x,y)=(beta*x,-y)` and picks the first minimum. Its ordered orbit is
`(x0,y0)`, `(x1,-y0)`, `(x2,y0)`, `(x0,-y0)`, `(x1,y0)`, `(x2,-y0)`, where
`x1=beta*x0` and `x2=beta*x1`. Reuse the three x words and two y hashes,
then evaluate the same six complete point hashes in the same order with the
same strict `<` tie break. Return the same representative and `k` as the
reference. The output is therefore bitwise identical for every valid j=0
input, including identity, x=0, y=0, and rare hash ties. Rho walks, group
operation counts, collision policy, and recovered scalars should match.

The reference computes five field multiplications for the five endomorphism
applications and six inner y mixes. The candidate computes two field
multiplications and two inner y mixes; since 2026-11-10 it computes one
multiplication, forming `x2 = -(x0 + x1) mod p` from `1 + beta + beta^2 = 0`
(same canonical word), and hands the chosen hash back so the walk does not
hash the point again. Both evaluate six outer point mixes;
the candidate's small orbit arrays and index arithmetic may cost time.
These are operation-count expectations, not CPU timing claims.

## Acceptance criteria

1. Compare every output word and returned `k` with the legacy hash loop for
   all six rotations of 128 deterministic subgroup points on each named j=0
   test curve, plus identity, x=0, and y=0 cases.
2. Build with `CA_RHO_J0_FACTORED_HASH=ON` and pass curve/rho correctness
   suites in release and UBSan. The option was off by default until
   2026-11-10; it is now on by default, and `-DCA_RHO_J0_FACTORED_HASH=OFF`
   (C macro `CA_RHO_J0_LEGACY_HASH`) builds the legacy loop. An existing
   build directory keeps its cached value until it is reconfigured.
3. On one frozen target point, both builds must recover the same scalar,
   independently replay it, and report identical group operations for each
   walk seed. A 32-seed operation panel is a secondary equality diagnostic,
   never a wall-time speedup estimate.
4. Promote a CPU speedup only after paired full one-target rho solves on an
   accepted isolated host, using `make_rho_orbit_manifest.py` and the gate in
   `docs/ISOLATED_BENCHMARKS.md`. Keep all raw failures and the exact online
   interval, from before target-dependent solver work through scalar replay.

The coordinate-minimum proposal in `RHO_J0_COORDINATE_ORBIT.md` changes walk
trajectories and is evaluated separately. This factored-hash proposal keeps
the legacy trajectory. Neither proposal carries an academic novelty claim.
