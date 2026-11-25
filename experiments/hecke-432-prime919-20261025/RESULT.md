# Level-432 fibers remain uniform at p=919 with a different mod-8 residue

The normalized level-432 map to \(B=432a1:y^2=x^3-16\) sends the
**1,296** noncuspidal points of \(X_0(432)(\mathbf F_{919})\) to **54**
B points, with **24 rational source points in every fiber**. The 24
rational cusps map to the identity, which is absent from the
noncuspidal image. Thus the full rational image has **55** points.
Direct enumeration gives \(\#B(\mathbf F_{919})=868\), leaving **813**
B points outside the rational image.

| Prime | \(p\bmod24\) | Noncuspidal sources | Noncuspidal image | Rational fiber sizes | Rational cusps | Full image / \(\#B(\mathbf F_p)\) |
| ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 883 | 19 | 864 | 36 | \(24:36\) | 24 | 37 / 931 |
| 887 | 23 | 872 | 109 | \(6:1,7:2,8:102,9:4\) | 8 | 110 / 888 |
| 907 | 19 | 720 | 30 | \(24:30\) | 24 | 31 / 889 |
| **919** | **7** | **1,296** | **54** | **\(24:54\)** | **24** | **55 / 868** |

The [protocol](protocol.json) fixed this prime before either producer
ran. It keeps \(p\equiv1\pmod3\) and changes \(p\bmod8\) from 3 to 7.
The uniform result rules out a rule limited to \(p\equiv19\pmod{24}\)
for these tested primes and supports testing a broader 3-part criterion.
The four-prime table is an exact finite-field comparison, not a proof of
a general splitting law.

## Source and image construction

`census_sage.py` scans all 919 \(j\)-values and enumerates
nonbacktracking cyclic 16- and 27-isogeny chains. It retains one model
per generic quadratic-twist pair and checks equal chain counts on the
twist. There are 60 contributing generic classes, with traces
\(\pm16\) and \(\pm56\); special \(j=0,1728\) classes contribute no
paired chains. Their **1,296** chain pairs agree with an independent
Hecke count: \(\operatorname{Tr}(T_{919})=-400\), so
\(\#X_0(432)(\mathbf F_{919})=919+1-(-400)=1320\). The cusp
denominator criterion gives 24 rational cusps; \(1320-24=1296\).

`evaluate_sage.py` transports every kernel chain through the certified
quarter-shift map. The exact rational functions \(j(3\tau)\) and
\(j(9\tau)\) select one level-27 coordinate point for each shifted
quotient. Frobenius conjugacy, the exact twist, and the dual 3-isogeny
give one B output per source. Because \(\#B(\mathbf F_{919})=868\)
is coprime to 3, the rational dual isogeny is bijective. All 1,296
rows pass these checks.

`audit.py` checks the frozen intermediate-map hash, all source keys,
the Hecke-minus-cusps equality, every B equation, the fiber histogram,
and the B group order by an independent finite-field square count. It
finds 54 distinct nonidentity outputs, each with 24 source points.
The cusp-image result from the [map identity experiment](../hecke-432-map-identity-20261025/RESULT.md)
adds the identity.

## Proof map and replay

| Result | Evidence and formalization |
| --- | --- |
| Exact 1,296-point noncuspidal source count | Full `census.json` routes, Hecke count 1,320, cusp count 24, and quadratic-twist parity checks. |
| Uniform 24-point fibers and 54 B outputs | Every source in `image.json`; independent `audit.json` checks source identity, equations, and histogram. |
| Full image 55 and complement 813 | Prior cusp-image theorem, direct target order 868, and `Prime919ImageGap.exactly_813_missing` for the finite-set complement. |
| \(24\cdot54=1296\) | `Prime919ImageGap.uniform_fiber_total` checks the numerical fiber total. |

The Lean module builds with pinned Lean and mathlib revisions.
`#print axioms` lists only standard foundations. Its image-gap theorem
uses the measured image and target cardinalities as hypotheses. The
modular-map and source-curve definitions and the Sturm identity remain
the explicit open Lean bridge; the written proof and exact computation
are retained in the predecessor experiments.

Replay from the repository root with the checked launcher:

```sh
./sage --runtime-info
./sage -python experiments/hecke-432-prime919-20261025/census_sage.py
./sage -python experiments/hecke-432-prime919-20261025/evaluate_sage.py
python3 experiments/hecke-432-prime919-20261025/audit.py
```

The saved runtime receipt, frozen protocol, full JSON rows, Lean build
output, and checksum seal bind this run. The next structural test is a
prime such as \(p=937\), where the rational degree-three kernel is
present; that case requires direct B-map evaluation to resolve the
three rational preimages of a transported E point.
