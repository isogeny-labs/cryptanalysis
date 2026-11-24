# Joint horizontal S4 component screen

## Question

Can redundant equations from a degree-5 horizontal isogeny make a three-summand S4 membership query cheaper than solving on the source curve alone? This is a retrospective exploratory screen prompted by one unusually fast joint solve. The script fixes one curve, one signed factor base, and a seeded natural query stream, then compares five polynomial systems. [pcc:unverified]

## Exact instance and formulations

- Source: `E/F_1009: y^2 = x^3 + 4x + 10`, with prime group order `1069`; `G = E.gens()[0]`, `Q = [271]G`.
- Map: `E.isogenies_prime_degree(5)[0]`, including its computed codomain and rational x-map. The sorted first eight nonzero points by `(x(phi(P)), y(phi(P)))` form a signed base of size eight. Its source x-coordinates are `307, 478, 489, 742`.
- Here the Frobenius trace is `1009 + 1 - 1069 = -59` and its discriminant is `(-59)^2 - 4(1009) = -555`, a fundamental discriminant. Thus the endomorphism order is maximal and this degree-5 ordinary isogeny is horizontal.
- Queries: seeded Python PRNG `20261123`; each query is `R = [a]G + [b]Q`, with `a` uniform in `[0,1068]` and `b` in `[1,1068]`. The first two positive and first two negative nonzero queries in that stream are retained. The displayed cohort is balanced for diagnosis, so its positive fraction is not a yield estimate.
- `source`: source S4 and three source x-base polynomials. `endpoint`: endpoint S4 and three endpoint x-base polynomials. `wires`: source S4, source x-base polynomials, and three rational-map x-wire equations. `joint`: `wires` plus endpoint S4. `joint_no_source`: source x-base polynomials and wires plus endpoint S4.
- Each membership verdict is compared with exact group enumeration of triples from the same signed base. The Gröbner calculation is over `F_1009`; the script checks whether the ideal contains one. This algebraic-closure test can differ from `F_1009` rational-point membership in general, so the four matched truths do not establish a universal decision procedure.

The source S4 is the resultant of two standard third summation polynomials. This follows the summation-polynomial setup used in [Petit, Kosters, and Messeng, *Algebraic Approaches for the Elliptic Curve Discrete Logarithm Problem over Prime Fields*](https://people.maths.ox.ac.uk/petit/files/16PKC_primeECDLP.pdf). The additional endpoint equations reuse the same source coordinates through the explicit isogeny; they do not supply independent relations or enlarge the factor base. [pcc:unverified]

The repository's [PKM auxiliary-curve study](../pkm_aux_curve_odd_isogeny_20261123/README.md) tests odd-degree isogeny towers for a different factor-base construction. This screen asks specifically whether adding transported endpoint equations helps a fixed source-curve membership system. [pcc:unverified]

## Reproduce

From the repository root on the accepted local Sage installation:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info
/Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/panel.py --repeats 11
```

`runtime.json` records the checked launcher result; `results.json` contains the full emitted JSON. SHA-256 of `panel.py`: `c5399547f8832efc46234188ca97ced27f49257847503fcc52706b607617a3b1`. SHA-256 of `results.json`: `55696c0425762b3d0e8c9e4ba078bf34e59d2fd900dfdbe18b5c5f89391a9f94`. Timing values are from one local run with 11 shuffled, interleaved repeats per arm and query; no host isolation or confidence interval was established. [pcc:unverified]

## Observations and decision

| Trial | `(a,b)` | Exact triple? | Source median (ms) | Endpoint median (ms) | Joint median (ms) |
| ---: | :--- | :---: | ---: | ---: | ---: |
| 1 | `(1011,328)` | no | 1.502 | 1.419 | 2.365 |
| 2 | `(355,182)` | no | 1.315 | 1.327 | 2.269 |
| 16 | `(1062,758)` | yes | 1.317 | 1.361 | 2.408 |
| 41 | `(144,457)` | yes | 1.359 | 1.296 | 2.673 |

All five arms agree with exact group truth on these four queries. The sum of per-query solve medians is 5.493 ms for source, 5.403 ms for endpoint, 9.715 ms for joint, 9.771 ms for wires, and 9.750 ms for joint without source S4. Thus the joint arm is about 1.77 times the source solve cost in this run, before charging map construction (86.042 ms) or equation building. The earlier single-query indication of an advantage did not persist on the repeated panel. This is a component result; it excludes relation collection, witness extraction, linear algebra, descent, and a matched rho run. It gives no same-target cold cost advantage. The producer attestation is `PCC-20261124-01f3eb`; it has no independent verification standing. [pcc:unverified]

The next discriminating test would pre-register several curves, base sizes, and held-out query streams, include rational witness extraction, and charge full relation throughput. Such a test is only justified if an equation-system change first produces a robust component gain under repeated paired measurements. [pcc:unverified]
