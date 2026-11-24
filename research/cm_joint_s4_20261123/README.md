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

## Three-summand scaling gate for natural queries

There is also a relation-count gate before solver timing matters. For a signed base of `B` rational points, the number of unordered three-term multisets is at most `C(B+2,3)`. Each such multiset has one sum in the group of order `r`. If `R = [a]G + [b]Q` is uniform and independently sampled, the **expected number of decompositions**, even if an oracle returns every one, is exactly `C(B+2,3)/r` per query. If `U` independent base-log coordinates have to be determined, obtaining `U` rows therefore takes at least `U r / C(B+2,3)` queries in expectation; dependence among rows can only increase the requirement. This counts the full-rank relation-collection route, not an early target-span algorithm. The conditional derivation is recorded as `PCC-20261124-ce107f`, with unverified standing. [pcc:unverified]

At a favorable 1 PiB allowance of 32 bytes per signed base point, `B <= 2^45`. For P-192's prime order, the expected decompositions per uniform query are at most `2^-59.585`. If negation removes half the base-log unknowns but no further relations among them are known, `U=B/2=2^44`, giving at least `2^103.585` queries in expectation to obtain `U` rows. The reference `sqrt(pi*r/4)` is `2^95.826` group-addition equivalents: the query count alone is about 217 times this reference even at an optimistic one equivalent per query, before the solver, setup, memory traffic, and linear algebra. With a smaller base the bound worsens. This conditional gate rules out the present full-rank three-summand strategy at that memory cap; it is not a lower bound on every decomposition method. [pcc:unverified]

The exact order used is `r=6277101735386680763835789423176059013767194773182842284081`. The arithmetic is reproducible with `B=2**45`, `T=math.comb(B+2,3)`, `U=B//2`, `expected_queries=U*r/T`, and `rho=math.sqrt(math.pi*r/4)`; the resulting query-to-rho ratio is `216.6488001`. This is a count comparison, not a timed benchmark. [pcc:unverified]

The effective unknown dimension is the key exception. At `B=2^45`, a one-equivalent-per-query strategy would need `U < 2^36.241` to fit below that rho reference even before all other costs. A base made from known-scalar or CM-loop orbits could reduce `U`; the earlier [CM orbit-arc hypothesis](https://github.com/isogeny-labs/crypto-autoresearcher/blob/main/ledger/hypotheses/H-CMFB-7d4e1a.yaml) already studies the two-summand version and identifies its BSGS-equivalent decomposition search. A three-summand proposal must therefore provide both an efficiently described large base with genuinely reduced `U` and a coordinate-dependent oracle whose **fully charged** cost stays within the stricter inequality `setup + (U*r/C(B+2,3))*T + LA + descent < rho`. Horizontal transport of an unchanged base alone changes neither `U` nor its decompositions. [pcc:unverified]
