# Frozen native F4 network panel

This protocol is frozen before generating the native solver inputs or running
`msolve`. It checks per-arm decomposition-system cost on the prime-order
fixture used in the exact network census. It is a finite solver panel, not a
complete relation-collection run. All local observations have producer-only
standing `[pcc:unverified]`.

## Workload and selected cases

- Use `GF(10007)`, `E = EllipticCurve(GF(10007), [-3, 7])`,
  `G = E.gens()[0]`, `R = 137*G`, bound `x < 20`, and the five rational
  isogenies in the degree-list order of `NETWORK_PROTOCOL.md`.
- Include the base curve and each of the five codomains. The negative case
  for every arm is the same base target `R`, mapped through that arm's
  isogeny. The exact group-law hit census says it has no two-summand
  decomposition in any of these six coordinate-bound bases.
- For each arm, choose its positive case as the first `s*G` in ascending
  `s=1,...,10192`, excluding 137, that has a two-summand decomposition in
  that arm's normalized pullback base. Map that point to the codomain for
  the isogenous arms. Record `s` and the mapped target coordinates.

## Polynomial system and verification

For each curve `C: y^2 = x^3 + a*x + b`, let `F_C` be the distinct eligible
integer x coordinates in `[0,20)`, and let
`B_C(X) = product_{u in F_C}(X-u)`. For a mapped target x coordinate `z`,
the three-equation system in `x1,x2` is

```
f3(x1,x2,z) = (x1-x2)^2*z^2
              - 2*((x1+x2)*(x1*x2+a)+2*b)*z
              + (x1*x2-a)^2 - 4*b*(x1+x2),
B_C(x1),
B_C(x2).
```

Run `msolve -f INPUT -o OUTPUT -v 2` once for each of the 12 cases with one
thread, retaining exact inputs, compressed raw stdout/stderr, compressed raw
outputs, exit status, solver version, and wall/CPU timing. Parse the number
of F4 rounds, maximum round degree, maximum matrix shape, and ideal degree.
Independently enumerate all ordered coordinate pairs in `F_C^2` satisfying
`f3=0`, and all ordered actual curve-point pairs summing to the mapped target;
check the two x-pair sets agree. Record any difference between distinct
x-pair count and solver ideal degree as a multiplicity issue, not a failed
group-law validation.

The two cases per arm intentionally differ in decomposition outcome. Timing
from one short run is diagnostic only. The panel does not replace the three
missing Track 1 `.ms` files or support an 8-fold symmetry claim.
`[pcc:unverified]`
