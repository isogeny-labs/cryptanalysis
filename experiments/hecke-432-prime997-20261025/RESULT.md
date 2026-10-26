# Rational three-kernel projection splits into 12-, 24-, and 48-point fibers at p=997

The normalized level-432 map has **1,800 noncuspidal rational source
points** at p=997. Its composition with the dual degree-three isogeny
to \(E:y^2=x^3+432\) has **72** rational image points. Their
projected fiber sizes are **12 for six E points, 24 for sixty, and 48
for six**. Every projected E point has exactly three rational
preimages on \(B=432a1:y^2=x^3-16\), checked by the explicit isogeny
formula. The six 12-point projected fibers force at least one occupied
B fiber to have fewer than 24 rational source points. Thus uniform
24-point rational B fibers do not hold for all primes
\(p\equiv1\pmod3\).

The projection alone bounds the noncuspidal B image between **78 and
216** points. The 36 rational cusps add the B identity: the E identity
is absent from the noncuspidal projected image. Hence the full B image
contains **79 to 217** of the **1,008** B points, leaving **791 to
929** B points outside its rational image. These are structural bounds
from the known degree-24 modular map and the complete projected fiber
histogram. The source-to-B assignment within each three-point coset is
the remaining exact-image calculation.

## Frozen source and projection experiment

The [protocol](protocol.json) selected p=997 by the fixed
[next-prime screen](../hecke-432-prime937-20261025/screen_result.json)
before either producer ran. `census_sage.py` scans all 997 \(j\)-values,
including the sextic and quartic special twists, and enumerates
nonbacktracking cyclic 16- and 27-isogeny chains. Its **1,800** paired
chains come from 62 generic curve classes. Independently,
\(\operatorname{Tr}(T_{997})=-838\), so
\(\#X_0(432)(\mathbf F_{997})=997+1-(-838)=1836\); the cusp
criterion gives 36 rational cusps, recovering \(1836-36=1800\).

`evaluate_sage.py` uses both exact intermediate invariants
\(j(3\tau)\) and \(j(9\tau)\) to identify each shifted level-27
point. At p=997, \(i=\sqrt{-1}\) is rational, so each quarter-shift
coordinate is individually Frobenius-fixed. Their difference gives the
E output. The evaluator retains **all three** rational B preimages of
that E point, including the three-point kernel over the E identity.
It checks the B and E equations and the dual-isogeny map on every row.

`audit.py` independently replays the finite-field isogeny formula,
source identities, frozen intermediate-map hash, curve orders, and
projected histogram. The two isogenous groups both have order 1,008;
the rational dual kernel has three points. The audit finds 72 distinct
E outputs and the following complete source distribution:

| Rational sources over one E point | E-image points | Source points | Minimum occupied B lifts |
| ---: | ---: | ---: | ---: |
| 12 | 6 | 72 | 1 each |
| 24 | 60 | 1,440 | 1 each |
| 48 | 6 | 288 | 2 each |
| Total | **72** | **1,800** | **78** |

The normalized B modular map has geometric degree 24. At this good
prime, each B point therefore has at most 24 rational source points.
An E fiber is the disjoint union of the fibers over its three rational
B preimages. The table gives the lower image bound
\(6\cdot1+60\cdot1+6\cdot2=78\); three lifts per E point give the
upper bound \(72\cdot3=216\). A 12-point E fiber has positive source
count but cannot be composed solely of complete 24-point B fibers.
The cusp identity lies outside the noncuspidal E image, adding one B
image point to both bounds.

## Proof map and replay

| Result | Evidence and formalization |
| --- | --- |
| Exact 1,800-point noncuspidal source count | Full all-\(j\) `census.json`; independent Hecke count 1,836 and cusp count 36. |
| 72 E outputs and 12/24/48 projected fibers | All 1,800 rows in `image.json`; independent `audit.json` verifies source keys, equations, three-point cosets, and histogram. |
| A 12-point E fiber forces a partial B fiber | `Prime997FiberSaturation.twelve_forces_partial_lift` proves the three-lift implication. |
| A 72-point E fiber would saturate all three B lifts | `Prime997FiberSaturation.three_lifts_saturate` records the degree-bound implication for the next control. |
| Full B-image interval 79–217 and complement 791–929 | Degree-24 bound, three rational lifts per E point, cusp identity, and checked Lean lower-bound/complement arithmetic. |

The Lean module builds with pinned Lean and mathlib revisions; its
`#print axioms` output lists only standard foundations. The module
formalizes the finite three-lift implications conditional on the
degree bound and measured projected counts. A faithful Lean model of
the modular map, reduction, and source census remains open, with the
written proof and exact computational artifacts retained here.

Replay from the repository root through the checked launcher:

```sh
./sage --runtime-info
./sage -python experiments/hecke-432-prime997-20261025/census_sage.py
./sage -python experiments/hecke-432-prime997-20261025/evaluate_sage.py
python3 experiments/hecke-432-prime997-20261025/audit.py
```

The next implementation step is to resolve the \(\mathbf Z/3\)
choice within each rational preimage coset using a source-dependent
normalization or Hecke relation that is anchored at a known B image.
That calculation can turn the bounded B image into an exact count.
