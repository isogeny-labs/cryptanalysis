# Level-432 image and fiber census at p=887

An exact second-prime census maps **872 noncuspidal** points of
\(X_0(432)(\mathbf F_{887})\) to **109** points of
\(B:y^2=x^3-16\). The rational fibers have sizes 6 through 9:

| Rational points per B fiber | Number of fibers | Source points |
| ---: | ---: | ---: |
| 6 | 1 | 6 |
| 7 | 2 | 14 |
| 8 | 102 | 816 |
| 9 | 4 | 36 |
| Total | **109** | **872** |

The eight rational cusps map to the identity under the normalized map
identified by the [Sturm certificate](../hecke-432-map-identity-20261025/RESULT.md).
That point is absent from the noncuspidal image. Thus the entire rational
source image has **110** points; \(B(\mathbf F_{887})\) has 888 points, so
**778** B points have no rational level-432 preimage. The 24-fold rational
fibers measured at \(p=883\) are not a general fiber law: the geometric
modular degree is 24, while the number of rational points in a fiber can
vary by reduction prime.

## Exact source and image construction

`census_sage.py` scans all 887 j-values and enumerates nonbacktracking
cyclic 16- and 27-isogeny chains. It records 888 raw chain pairs. The two
special j-values each have a base and a quadratic-twist representative;
retaining one representative for each removes 16 duplicate pairs, leaving
872. Generic quadratic-twist chain counts agree whenever a pair occurs.
Independently, the trace of \(T_{887}\) on the 55-dimensional weight-two
space is 8, giving \(888-8=880\) total rational modular-curve points.
The cusp denominator criterion gives eight rational cusps, independently
recovering 872 noncuspidal points. All raw models and routes are in
`census.json`.

The original two-j-value coordinate inversion leaves 792 rows with one B
candidate, 64 with two, and 16 with three. `derive_intermediate_sage.py`
therefore derives the exact functions \(j(3\tau)\) and \(j(9\tau)\) on
\(X_0(27):y^2+y=x^3-7\) by rational q-series interpolation. Both
interpolation kernels are one-dimensional and their identities vanish on
held-out exponents 100 through 149. The respective poles at infinity are
3 and 9; the source and target j-projections have degree 36, so the
nonzero identity combinations have pole degree at most 69 and 63. Their
vanishing order past 100 proves the rational-function identities.

For every shifted cyclic 27-isogeny, `evaluate_sage.py` computes the actual
intermediate j-values from its transported kernel polynomial: intersect
the 27-kernel with 3-torsion, quotient once for \(j(3\tau)\), push the
remaining 9-kernel, and quotient again for \(j(9\tau)\). Matching both
invariants selects exactly one level-27 coordinate point on each side
of every one of the 872 source records. Frobenius conjugacy, the exact
twist, and the unique rational dual-isogeny preimage then give one B
point per source. `image_jpair_only.json` preserves the unresolved
two-j run; `image.json` records the resolved run. `audit.py` checks every
source key, B equation, candidate count, fiber count, cusp count, and
target group order by independent finite-field enumeration.

## Proof map and replay

| Result | Evidence and formalization |
| --- | --- |
| Intermediate j-functions on \(X_0(27)\) | Unique rational q-series interpolation, held-out coefficients, and pole-degree argument; Lean modular-function bridge remains open. |
| Exact 872-point source census | All 887 j-values scanned, trace and twist receipts, independent Hecke point count and cusp enumeration. |
| 109 noncuspidal images and fiber distribution | All 872 source routes evaluated with j3/j9 disambiguation; independent `audit.json` checks. |
| Full image 110 and gap 778 | Normalized-map and cusp proof from the preceding experiments; `Prime887ImageGap.exactly_778_missing` checks the final finite-set implication in Lean. |

The Lean toolchain and mathlib revisions are pinned in `formal/`; the
reported proof uses only standard Lean foundations. Formal definitions of
the modular map and source curve remain an open bridge, while the exact
computations and written modular arguments are retained here. This is a
finite-field correctness and coverage comparison, with no CPU wall-time
speedup or IC candidate assigned.

Replay from the repository root through the checked launcher with
`./sage -python experiments/hecke-432-prime887-20261025/census_sage.py`,
`derive_intermediate_sage.py`, and `evaluate_sage.py`, then run
`python3 experiments/hecke-432-prime887-20261025/audit.py`. The Sage
runtime receipt and checksum seal bind the persisted artifacts.
