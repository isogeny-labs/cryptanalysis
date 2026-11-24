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

### Pricing the rank-one orbit exception

Suppose an orbit base has one unknown seed log. Its other logs are known multiples of that seed, so one base relation and one target relation can determine the seed log and `d` when their two coefficients are independent. If the seed is `G`, one target relation suffices. This is the precise rank reduction studied for two summands by the earlier CM orbit-arc hypothesis; the calculation below prices the standard explicit pair-table search for three summands. [pcc:unverified]

Precompute all unordered base-point pair sums, about `B^2/2` entries, then test `R-P` against that table for each of `B` points per query. For `h` required relations and natural uniform queries, the favorable leading work model is

```text
C_pair(B,h) = B^2/2 + (h*r/C(B+2,3))*B
            ~= B^2/2 + 6*h*r/B^2.
```

The minimum of this model is `2*sqrt(3*h*r)` at `B=(12*h*r)^(1/4)`. Against the negation-aware rho reference `sqrt(pi*r/4)`, the minimum is `4*sqrt(3*h/pi)` times larger: about `3.91` for one relation or `5.53` for two. On P-192 the corresponding bases have `log2(B)=48.896` and `49.146`, while their 32-byte pair tables alone require about `2^101.79` and `2^102.29` bytes. At the 1 PiB base cap `B=2^45`, the explicit pair table still needs about `2^94` bytes. These are optimistic counted-operation and table-size calculations for this **specific** lookup method, with no lookup, map, or linear-algebra charge; they are not a generic lower bound. The scoped cost statement is recorded as `PCC-20261124-cdbc5b`, with unverified standing. [pcc:unverified]

The remaining candidate is therefore narrower than merely reducing relation rank: it needs a compact coordinate-based three-sum oracle on a large, low-rank CM orbit base **without** materializing its pair table. The decisive experiment must compare a genuine CM orbit with a matched known-scalar orbit, measure natural-query relations and all setup, and show that the solver beats the per-query budget above on an identical base. A compact description of the orbit or a low-rank relation matrix alone does not supply that oracle. [pcc:unverified]

## P-192 four-summand horizontal endpoint screen

The follow-up script `p192_tower_horizontal_s5.py` compares three equations for the **same** P-192 source x-base and the same two queries. The base comes from the four-root fiber of a depth-2, 2-isogeny tower on `y^2=x^3+x`. Exactly two of its four x-values lift to P-192, giving four signed source points. This auxiliary tower defines the base; it is distinct from the horizontal degree-5 map used in two of the equation systems. `source` has eight auxiliary tower equations and three source S3 sum constraints; `mapped5` adds four degree-5 rational x-map wires and uses three endpoint S3 constraints; `joint5` retains both source and endpoint S3 constraints. The P-192 Frobenius discriminant is fundamental, so the degree-5 ordinary map is horizontal. [pcc:unverified]

The positive query is planted: `71 G + 83 Q` is defined as a four-term sum from that base. The negative query uses the fixed Python seed `20261124` for coefficients of the same `G,Q`. Exact point enumeration checks membership of both before algebraic solving. Each formulation was run three times serially, one process per query, under a 40-second wall cap. All 18 processes exited normally; the algebraic-closure SAT verdict matched exact point truth in all 18. The record `p192_tower_horizontal_s5_results.jsonl` contains every command's exit code, setup, solver time, wall time, inputs, and verdicts. [pcc:unverified]

| Formulation | Positive median solver / wall (s) | Negative median solver / wall (s) | Sum of wall medians (s) |
| :--- | ---: | ---: | ---: |
| `source` | 0.303 / 2.799 | 0.223 / 2.329 | 5.129 |
| `mapped5` | 0.279 / 3.240 | 0.217 / 2.667 | 5.906 |
| `joint5` | 1.989 / 5.273 | 1.727 / 4.337 | 9.611 |

The mapped system's small solver-time reduction did not survive process-level charging: the sum of its wall medians was 1.15 times source. The joint system was 1.87 times source. These are local exploratory component timings on one planted and one negative query with three repeats, without host isolation or a confidence interval. They do not measure natural-query yield, witness extraction, relation collection, linear algebra, descent, or an end-to-end same-target comparison. This fixed-base encoding provides no observed cold-cost gain. The producer claim is `PCC-20261124-ee500b`, with unverified standing. [pcc:unverified]

Reproduce with the checked Sage launcher, running each mode and query as separate processes:

```sh
gtimeout 40 /Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/p192_tower_horizontal_s5.py --mode source --query planted
gtimeout 40 /Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/p192_tower_horizontal_s5.py --mode mapped5 --query planted
gtimeout 40 /Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/p192_tower_horizontal_s5.py --mode joint5 --query planted
```

Repeat with `--query negative`. SHA-256 at the original depth-2 run: script `e6a9cd86b0be0cd7f5416a983862f94cfef911c12374559918cdcc87bb638470` (commit `0bee50b57`), raw JSONL `c4dbbd89e4f989062c425427ee4962e9ff5f827b5796a46c569d1edf90cc102e`. The current script extends that version to depth 3 and an identity-wire control; its SHA-256 is `af6fcf1ce32a8a5135c9b745041be5dad412efffe8202b3144362838091e503d`. The next discriminating step is a compact oracle for a large, low-rank **genuine CM orbit** with natural query yield and a matched known-scalar control; this two-liftable-x auxiliary fiber cannot supply that scale. [pcc:unverified]

### Depth-3 scale check and identity-wire falsifier

At depth 3 the same auxiliary construction gives eight x-fiber roots, four of which lift to P-192. The source system has 14 variables and 15 equations. The endpoint systems have 18 variables and 19 equations. A first capped six-cell pilot completed all modes on the same planted and seeded-negative queries; its raw record is `p192_tower_horizontal_s5_depth3_results.jsonl` (SHA-256 `884c8a944be2c3f325b1e49ac876fbfa241dcabb059139a2d4c53d7e790d3388`). This prompted a separate confirmation of the source versus mapped5 comparison. [pcc:unverified]

The confirmation protocol was written as the first JSONL record before any confirmation run: four paired blocks per query, ordered source/mapped5, mapped5/source, source/mapped5, mapped5/source; 60-second process cap; process wall time as primary; all eight mapped5/source pairs had to favor mapped5, with correct SAT verdicts and zero exits. All 16 runs completed and matched exact point truth. Mapped5 won seven of eight wall-time pairs, so the **predeclared all-pairs criterion failed**. The only losing pair was the first negative query, 24.671 s mapped5 versus 24.217 s source. Median wall times were 30.720 s source versus 21.609 s mapped5 on the planted query and 25.371 s versus 18.557 s on the negative query. These medians show a local presentation signal, not a criterion pass or a general speedup. Raw record: `p192_tower_horizontal_s5_depth3_confirm.jsonl` (SHA-256 `34b0de7dbcf65b78903739726e584834d7cd9004d7ee4e6c35ba4f7139d99c2d`). [pcc:unverified]

To test attribution, `identity` uses the same extra endpoint variables and four wire equations as `mapped5`, but sets each endpoint x equal to its source x and applies the source-curve S3 equations. The two fixed-query exploratory control runs took 14.153 s and 8.699 s process wall time; mapped5 took 26.138 s and 20.179 s in the matched order. All four verdicts matched exact point truth. Thus the observed source-to-mapped5 gain is also achieved, more strongly in this control, without a horizontal map. The data cannot attribute a cost improvement to isogeny structure. Raw record: `p192_tower_horizontal_s5_depth3_identity.jsonl` (SHA-256 `5107e6caa87011c56f7a411756b9dc267304bbcb92dee4029c39fb0f3f2c32a7`). The producer claim `PCC-20261124-bd9f3a` remains unverified. [pcc:unverified]

This screen still uses a four-signed-point base, one constructed positive query, and one negative query. It does not estimate natural-query yield, deliver enough independent point relations, extract a target scalar, or compare a complete cold ECDLP run against rho. The useful next construction must make either relation support or a **controlled** solver cost improve with genuine CM structure at a base size that can meet the full relation-count budget. [pcc:unverified]

## Ray-class bridge audit

The [ray-class reduction audit](RAY_CLASS_REDUCTION_AUDIT.md) checks a proposed obstruction in the existing lead atlas. The identity `pi = 1 mod (pi-1)` correctly gives trivial Artin symbol at the relevant prime, but it does not identify the reduced Weber values: prime-to-`p` torsion reduction is injective. A class-number-one `D=-19`, `p=47`, `r=61` control gives 30 distinct reduced x-values, contradicting the older proposal's one-value prediction. The ray labels of those values remain unknown from their coordinates; this repairs the search boundary without supplying a point-to-ideal algorithm. Producer claim `PCC-20261124-cc75fc` is unverified. [pcc:unverified]

The [ray-label character gate](RAY_LABEL_CHARACTER_GATE.md) gives an exact point-dependent baseline: a quadratic-character resolvent satisfies `R(Q)=chi_r(d)R(G)` when `Q=[d]G`, and the same `D=-19` instance checks all 60 nonzero scalars. Its direct target pass costs about `r/2` group additions, far above same-target rho at P-192, and the identity is generic rather than CM-specific. A single low-degree x-only rational map cannot replace the full sum. A future CM proposal must supply a compact, charged evaluation of a useful ray-label quotient and beat this generic construction and rho on the same target. Producer claim `PCC-20261124-943a1c` is unverified. [pcc:unverified]

The [Gauss-resolvent orientation audit](GAUSS_RESOLVENT_ORIENTATION.md) identifies the close published prior art: universal elliptic Gauss sums compute character-invariant powers for Frobenius-eigenvalue point counting, while the target's character is the orientation that powering discards. In the finite control `R(G)^2=R(2G)^2=7 mod 47` although the unsquared values have opposite signs. The published construction retains cost proportional to its torsion prime `ell`; using `ell=r` does not supply the missing cheap oriented evaluator. The source-specific claim `PCC-20261124-e77745` is unverified. [pcc:unverified]

The [Frobenius-minus-one gate](FROBENIUS_MINUS_ONE_GATE.md) checks a degree-`r` horizontal endomorphism with a rational-point kernel. The map `1-pi` is cheap to evaluate but sends every rational point, including `G` and `Q`, to `O`; its dual acts on them by the known scalar `1-p mod r`. This corrects the inference that large isogeny degree alone forces expensive evaluation, while showing that this particular fast map erases the needed point distinction. Producer claim `PCC-20261124-f14459` is unverified. [pcc:unverified]

The same gate now checks the preimage fiber of `1-pi`: if `(1-pi)T=Q` and `Q` has order `r`, then `pi^m T=T-[m]Q`, so `T` has exact field degree `r` and every nonzero target gives an unlabelled `r`-cycle. Its cohomology class is `-Q=-[d]G`; expressing that class as `-d` requires the missing orientation. This is an exact point relation, not a cheaper scalar extraction. Producer claim `PCC-20261124-f773c1` is unverified. [pcc:unverified]

The [ray-kernel residue gate](RAY_KERNEL_RESIDUE_GATE.md) makes the pointed/unpointed split exact: for `n=(pi-1)` of prime norm `r`, the relative ray-class kernel is `F_r^*/{+1,-1}`. A smooth principal relation `alpha=a+b*pi` contributes the public residue `a+b mod r`. On the `D=-19` control, `1+pi` has smooth norm `35=5*7`, residue `2 mod 61`, and sends `G` to `[2]G`. This confirms the relation mechanism while locating the missing operation: assigning a ray residue or character to an independently supplied `Q` from its coordinates. Producer claim `PCC-20261124-01af6e` is unverified. [pcc:unverified]

The [division-derivative screen](DIVISION_DERIVATIVE_SCREEN.md) tested one compact-circuit candidate for that missing character: the Legendre sign of the derivative of the full `r`-division polynomial at `x(Q)`, relative to `G`. On the `D=-19` control it agrees with the scalar's quadratic character for 28 of 60 nonzero scalars, and `d=4` is an explicit counterexample to exact equivariance. The derivative of the rational-line kernel polynomial gives the same 28/60 count there. This rejects the stated identity, without a P-192 cost claim or a general bound on other circuits. Producer claim `PCC-20261124-cc7020` is unverified. [pcc:unverified]
