# Frozen exact isogeny-network hit panel

This protocol is frozen before computing the network-hit output. It tests the
specific best-of-five assertion in the supplied Track 3 on one public
prime-order fixture; it does not estimate an asymptotic cost or solve a
discrete logarithm. Local output has producer-only standing
`[pcc:unverified]`.

## Fixed instance and arm construction

- Base field: `GF(10007)`.
- Curve: `EllipticCurve(GF(10007), [-3, 7])`, order `10193` prime.
- Rational isogenies: every result of `E.isogenies_prime_degree(ell)` in
  degree order `ell = 2, 3, 5, 7, 11, 13, 17, 19`. The expected degree list
  is `[7, 11, 11, 19, 19]`; abort if it changes.
- Coordinate bound: `0 <= int(x) < 20`, with both rational ordinates and no
  point at infinity. Apply this bound independently on the base curve and
  each isogenous codomain.
- Pull each codomain point `Q` back to the base group as
  `[ell^(-1) mod 10193] dual_phi(Q)`. This is the unique `P` with `phi(P)=Q`.
- A two-summand hit for target `R` means `R=P+Q` for an ordered pair from
  that arm's pulled-back factor base; repeated points are permitted. The hit
  set is evaluated exactly over all `10193` rational base-group elements,
  including the identity. There is no sampled target or solver call.

## Predeclared outputs

Record per-arm factor-base sizes, their true union and pairwise overlaps;
per-arm two-summand hit-set sizes, their true union and pairwise overlaps;
the ratio of union hit probability to the largest single-arm probability;
and the independent-hit counterfactual
`1 - product_i(1 - |hit_i|/10193)`. Include the base curve as a separately
identified reference, and report network-only and base-plus-network unions.
The counterfactual is diagnostic; exact hit-set intersections determine the
observed correlation. Do not infer a speedup without relation collection,
solver, and linear-algebra costs on the same target workload.
