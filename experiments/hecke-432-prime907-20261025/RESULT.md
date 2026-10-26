# A second uniform 24-point level-432 fiber census at p=907

The normalized level-432 map to \(B=432a1:y^2=x^3-16\) sends the **720**
noncuspidal points of \(X_0(432)(\mathbf F_{907})\) to **30** B points,
with **24 rational source points in every fiber**. The 24 rational cusps
map to the identity under the [certified modular map](../hecke-432-map-identity-20261025/RESULT.md),
which is absent from the noncuspidal image. Thus the full rational image
has **31** points. Direct enumeration gives \(\#B(\mathbf F_{907})=889\),
so **858** B points have no rational level-432 preimage.

| Prime | \(p\bmod24\) | Noncuspidal sources | Noncuspidal image | Rational fiber sizes | Rational cusps | Full image / \(\#B(\mathbf F_p)\) |
| ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 883 | 19 | 864 | 36 | \(24:36\) | 24 | 37 / 931 |
| 887 | 23 | 872 | 109 | \(6:1,7:2,8:102,9:4\) | 8 | 110 / 888 |
| **907** | **19** | **720** | **30** | **\(24:30\)** | **24** | **31 / 889** |

The two tested primes congruent to 19 modulo 24 have uniform rational
24-point fibers, whereas the tested prime congruent to 23 does not.
This is a measured finite-field pattern. A congruence criterion for fiber
splitting would require a structural proof or further prime controls.

## Source and image construction

The [frozen image protocol](protocol.json) selected 907 to repeat the
residue class of 883 and fixed the source and image gates before image
evaluation. `census_sage.py` scans all 907 \(j\)-values and enumerates
nonbacktracking cyclic 16- and 27-isogeny chains. It retains one model
per generic quadratic-twist pair and checks equal chain counts on its
twist. There are 30 contributing generic curve classes, with traces
\(-44\) and \(44\); the special \(j=0,1728\) classes contribute no
paired chains. The resulting **720** chain pairs match an independent
weight-two Hecke point count: \(\operatorname{Tr}(T_{907})=164\), hence
\(\#X_0(432)(\mathbf F_{907})=907+1-164=744\). The cusp denominator
criterion gives 24 rational cusps, so \(744-24=720\).

`evaluate_sage.py` transports every recorded kernel chain through the
quarter-shift construction. The exact rational functions
\(j(3\tau)\) and \(j(9\tau)\), whose frozen coefficients are copied
from the [p=887 derivation](../hecke-432-prime887-20261025/RESULT.md),
select one level-27 coordinate point for each of the two shifted
quotients. Frobenius conjugacy selects one pair; the twist and rational
dual 3-isogeny then give one B output per source. The source and target
groups have order 889, coprime to 3, so the dual isogeny is bijective on
rational points. All 720 rows pass those checks.

`audit.py` independently checks the source-key set and ordering, the
Hecke-minus-cusps equality, all B equations, the fiber histogram, and
\(\#B(\mathbf F_{907})\) by enumerating finite-field squares. It finds
30 distinct nonidentity outputs, each with 24 sources. The identity is
supplied by the cusps, giving the 31-point full image.

## Proof map and replay

| Result | Evidence and formalization |
| --- | --- |
| Exact 720-point noncuspidal source count | All \(j\)-values and kernel routes in `census.json`; independent Hecke count 744 and cusp count 24; quadratic-twist parity checks. |
| Uniform 24-point fibers and 30 B outputs | Every source in `image.json`; independent `audit.json` checks source identity, curve equations, and histogram. |
| Full image 31 and complement 858 | Prior cusp-image theorem, direct target order 889, and `Prime907ImageGap.exactly_858_missing` for the finite-set complement implication. |
| \(24\cdot30=720\) | `Prime907ImageGap.uniform_fiber_total` checks the numerical fiber total. |

The Lean module builds with the pinned Lean and mathlib revisions, and
`#print axioms` lists only standard foundations. Its image-gap theorem
is conditional on the measured image and target cardinalities. The
faithful Lean definition of the modular map, its source curve, and the
Sturm-bound identity remains an open formalization bridge; the written
proof and exact computation are retained in the linked predecessor
experiments.

Replay from the repository root with the checked launcher:

```sh
./sage --runtime-info
./sage -python experiments/hecke-432-prime907-20261025/census_sage.py
./sage -python experiments/hecke-432-prime907-20261025/evaluate_sage.py
python3 experiments/hecke-432-prime907-20261025/audit.py
```

The saved runtime receipt, protocol, full JSON rows, Lean build output,
and checksum seal bind this run. The next prime control should keep
\(p\equiv1\pmod3\) while changing the residue modulo 8; \(p=919\)
is a candidate after checking its source and target arithmetic.
