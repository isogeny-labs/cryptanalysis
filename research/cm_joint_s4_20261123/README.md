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

An [exhaustive three-sum support audit](EXACT_THREE_SUM_SUPPORT.md) of
this fixed eight-point base finds 92 decomposable points among the
1068 nonzero targets, a natural hit probability of `23/267`. It also
checks every source and endpoint multiplicity under the horizontal
map. The four-query timing panel below deliberately balances two
positives and two negatives; its positive share is not a yield
estimate. [pcc:unverified]

The [general transport gate](TRANSPORTED_RELATION_GATE.md) now proves
that any injective additive map preserves every indexed zero-sum and
target-sum witness of an unchanged labelled base. It therefore
preserves point-level relation yield, coefficient informativeness, and
rank under the prime-to-order horizontal map. The endpoint can still
change the cost of solving the coordinate equations; that is the
distinct question measured by the panel. The group statement is also
checked in [Lean](formal/TransportGate.lean). The scoped statement is
`PCC-20261125-9f930e`, with unverified standing. [pcc:unverified]

The [frozen native-base census](NATIVE_THREE_SUM_REPORT.md) selects the same eight-point low-`x` factor-base shape independently on each curve of this `p=1009` horizontal pair. Among all 1068 nonidentity targets, source support is `96` and codomain support is `92`; transporting the source base retains `96`. Same-size random-base controls put the four-point native difference within ordinary finite-instance variation. Producer claim `PCC-20261125-560b99` is unverified. [pcc:unverified]

The [same-target native S4 cost screen](NATIVE_THREE_SUM_COST_REPORT.md) explicitly corrects the yield-only stopping rule: lower yield could be offset by cheaper coordinate solving. On four frozen 64-target streams with seven interleaved repeats, every algebraic verdict matches exact rational membership, but the endpoint/source **exact-yield-adjusted** solve-work ratios are `1.0199–1.0842`, above one in all streams. This fixed native base has no supported component gain; setup, collection, and rho costs are still outside the panel. Producer claim `PCC-20261125-c94c66` is unverified. [pcc:unverified]

This pointwise invariant and the separate coordinate-shape question
were already stated in the earlier
[`IDEA-20260906-5b4930`](https://github.com/isogeny-labs/crypto-autoresearcher/blob/main/ledger/proposals/IDEA-20260906-5b4930.yaml)
proposal. The [coset transport and label screen](COSET_TRANSPORT_LABEL_GATE.md)
checks that this fixed degree-five edge turns every fully liftable
`B=4,6,7,8` coset in the enumerated cells from a two-term source
vanishing polynomial into a dense endpoint polynomial. It also prices
uniform rejection sampling as a way to attach APS labels to a
preselected coordinate base; at the stated P-192 memory cap, the
expected draw count for one accepted labelled point already exceeds
the rho reference. These are scoped shape and sampling results, not a
solver or full-log speed claim. The record is `PCC-20261125-b8dbb8`,
with unverified standing. [pcc:unverified]

The fixed-instance count is recorded as `PCC-20261124-89e12e` with
unverified standing. [pcc:unverified]

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

The [target-dependent orbit audit](TARGET_DEPENDENT_ORBIT_GATE.md)
identifies a generic point relation already present in Amadori,
Pintore, and Sala's prime-field work. It also shows why one CM
orbit of a single seed `[a]G+[b]Q` gives only predetermined zero
sums: the coefficient of both `G` and `Q` vanishes together.
Distinct seed coefficient vectors or a different coordinate
construction are required before an orbit relation can carry `d`.
Their CM-specific relation yield and charged solve cost remain open. [pcc:unverified]

The [frozen two-seed orbit census](TWO_SEED_ORBIT_REPORT.md) tests the first exception on `D=-19`: signed three-sums across length-three arcs of `G` and supplied `Q`, generated through the degree-five CM endomorphism. It obtains 216 informative indexed relations across all 60 target labels, covering 46 labels, while the preselected `d=3` target yields none. The `d=4` row gives the explicit verified relation `13G+12Q=O`. The matched scalar `[7]` orbit is identical point by point, so it has exactly the same relation supply; a 78-entry explicit pair table already exceeds the roughly 6.92-addition rho reference on this small group before other costs. The two-seed mechanism carries the unknown scalar, but this fixed implementation has no CM-attributable yield or complete-cost advantage. [pcc:unverified]

The [two-seed support bound](TWO_SEED_ORBIT_SUPPORT_BOUND.md) shows why its cubic count of indexed triples overstates target reach. For any two independent public seed vectors and a shared length-`L` geometric orbit, the informative three-sum support outside at most two zero-seed labels is at most `8L(2L-1)`: ratios of orbit powers retain only two exponent differences. Under an optimistic P-192 1 PiB materialized-base cap, `L<=2^43` and a fixed arc reaches fewer than `2^90` of roughly `2^192` target labels. A target-independent schedule needs about `2^101` arc tests to cover half the labels, above the `2^95.826` rho reference if each test costs at least one addition equivalent. The bound leaves coordinate-selected seeds, larger implicit bases, more seed blocks, higher arity, and batch oracles outside its scope. [pcc:unverified]

The [multi-seed common-shift bound](MULTI_SEED_ORBIT_SUPPORT_BOUND.md) extends the homogeneous zero-sum count to `s` publicly labelled orbit blocks: at most `binom(2sL+2,3)-binom(2s(L-1)+2,3)` distinct target labels can have an informative relation. Under the same materialized-base cap and one-addition-equivalent test assumption, its optimistic 50% coverage threshold exceeds rho for every `s<=36`; `s=37` is the first count it does not exclude. The result does not apply to an **inhomogeneous** query `P1+P2+P3=[a]G+[b]Q`, because the fixed right-hand side breaks common scaling. That target-sum mechanism remains a separate candidate requiring a relation oracle and full cost accounting. [pcc:unverified]

The [frozen inhomogeneous screen](INHOMOGENEOUS_ORBIT_REPORT.md) checks that exception on the same `D=-19` base. The preselected `d=3` target, missed by homogeneous zero sums, has an informative relation on 31 of 32 fixed target-sum queries, including the first: `15G+56Q=O`. Across all 60 target labels, 1,884 of 1,920 fixed queries have an informative witness; coefficient-only replay checks every count. The horizontal and native-scalar orbit points are identical, so this is a point relation without an isogeny-attributable yield gain. At P-192 scale and the optimistic `B=2^45` materialized-base cap, the generic triple-count ceiling requires about `2^59.585` uniform queries per hit and a complete per-query oracle below `2^36.241` addition equivalents merely to leave room beneath the `2^95.826` rho reference. An explicit pair scan exceeds that budget. [pcc:unverified]

The [pair-orbit descriptor gate](ORBIT_PAIR_DESCRIPTOR_GATE.md) compresses an indexed pair table into `O(B)` exponent-gap arcs, with a 42-descriptor/78-pair replay on the same finite base. A direct point-query scan still costs `B*D` arc-membership tests. Charging descriptor storage inside the same optimistic 1 PiB allowance tightens the uniform-query room beneath rho to `2^29.275` additions per complete query. The missing construction is a collective membership oracle with a matched native-scalar control, not more principal ideals. [pcc:unverified]

The [transposed orbit-membership gate](TRANSPOSED_ORBIT_MEMBERSHIP_GATE.md) hashes descriptor seeds and checks `B*L` transformed points per target-sum query. Its Sage replay matches all 1,920 fixed finite queries, including indexed witnesses. Under the same optimistic P-192 memory cap, that is still about `2^83.356` lookups per query, far beyond the complete-query budget. The gate also connects the method to the earlier implicit orbit-membership proposal and the existing point-to-ray homomorphism obstruction, so the remaining lead is explicitly a nonadditive coordinate-based oracle. [pcc:unverified]

The scoped prior-art and orbit-algebra record is
`PCC-20261125-c8e274`, with unverified standing. [pcc:unverified]

A related graph-wide study is already tracked at
`crypto-autoresearcher:problems/isogeny-graph-wide-relation-solver.md`
and in its [phased executor PR](https://github.com/isogeny-labs/crypto-autoresearcher/pull/2495).
It distinguishes coordinate-native bases from transported source bases
and specifies a same-point finalist solve with transfer, setup,
relations, rank, verification, and matched rho charged. Its bounded
controls do not replace the still-unadmitted common-target graph run
or a completed cost comparison. The screens in this PR are narrower;
they do not supersede that program. [pcc:unverified]

The existing [Crypto APS-E3 orbit-base study](https://github.com/isogeny-labs/crypto/blob/5097d0d45c46c72041ddacca012fe694252ded6d/research/aps_extensions_20261026/README.md)
already rejects an intrinsic automorphism-orbit zero sum with
`A=B=0` and retains an informative relation across orbit blocks on
its fixed finite fixture. The Lean result in this PR extends that
algebraic null to arbitrary finite signed lists from **one**
known-scalar orbit; it is not a new orbit attack. The existing
[APS complete-cost problem](https://github.com/isogeny-labs/crypto/blob/5097d0d45c46c72041ddacca012fe694252ded6d/problems/aps-single-relation-complete-cost.md)
tracks the missing setup, decoding, retries, independent metric
validation, and matched-rho comparison. A CM-specific successor
should use that cost contract and show what the horizontal map changes
relative to its matched known-scalar control. [pcc:unverified]

The [exact APS orbit witness](APS_ORBIT_POINT_WITNESS.md) pins that
prior result to its retained transcript and separate affine replay.
On its fixed `r=97` curve, three points from different orbit blocks
give `76G+64Q=O`, so the nonzero target coefficient recovers the
public fixture scalar. The transcript hash, point labels, and current
independent arithmetic check are recorded there. This establishes a
concrete point-dependent relation at that fixed scale; it does not
attribute a relation or cost gain to P-192 horizontal isogenies.
The scoped record is `PCC-20261125-b88d6d`, with unverified standing.
[pcc:unverified]

The [ramified degree-five orbit gate](HORIZONTAL_FIVE_ORBIT_GATE.md)
rules out a direct transfer of the APS-E3 same-curve automorphism
orbit to the degree-five map in either screen here. In both maximal
CM orders, 5 ramifies and its prime ideal is nonprincipal. Every
pure degree-five closed path therefore acts as an integer power of
5, up to sign; an odd-length path does not return to the source
isomorphism class. Mixed-degree pointed relations remain a distinct
question and still require target-coordinate dependence and a fully
charged cost comparison. [pcc:unverified]
The scoped statement is `PCC-20261125-746072`, with unverified
standing. [pcc:unverified]

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

The [prime-to-order isogeny descent gate](PRIME_TO_R_DESCENT_GATE.md)
shows that a smooth horizontal chain whose degree is coprime to the
prime rational-group order is bijective on rational points. Its standard
isogeny-descent cokernel is zero, so that construction supplies no
point label for `Q`. This leaves coordinate-dependent solver-cost and
relation-yield effects open, as well as the degree-`r` preimage torsor
examined below. [pcc:unverified]
The scoped theorem record is `PCC-20261124-921ac2`; its producer
attestation is not independent verification. [pcc:unverified]

The [composite-kernel cohomology check](COHOMOLOGY_COMPOSITION_GATE.md)
strengthens this statement: for a separable prime-to-`r` chain,
Frobenius minus one is invertible on its finite kernel, so its full
`H^1(F_p, ker(phi))` vanishes. For `1-pi`, the kernel is instead the
order-`r` rational group and the class of `Q` survives as `-Q`,
still without an integer label relative to `G`. [pcc:unverified]
The scoped cohomology claim is `PCC-20261124-fb5fa8`, with
unverified standing. [pcc:unverified]

The [squared-ray point bridge](SQUARED_RAY_POINT_BRIDGE.md) identifies a precise exception to the additive homomorphism obstruction: modulus `(pi-1)^2` has an `r`-element principal-unit subgroup, and `(pi)` generates its `r`-primary ray class on P-192. Exact Sage arithmetic checks this on P-192 and the `D=-19` control. Mapping a supplied `Q=[d]G` to its corresponding class remains the missing coordinate operation; the defining formula itself uses `d`. Direct reduction of a generic ray-class-field generator has residue degree `r` at `(pi)`, so the full-field route is not a cheap evaluator. [pcc:unverified]

The [coordinate-to-ray ideal screen](COORDINATE_IDEAL_RAY_SCREEN.md) tests a literal point-dependent assignment `P -> ((x(P)-pi)/(x(P)-1))` into the squared-ray principal units, with coefficient `-1/(x(P)-1) mod r` wherever defined. Exhaustive `D=-19` and same-order horizontal-pair checks find no additive scalar rule or exact character law. The endpoint model has higher raw character agreement, but its paired difference is exceeded by 20/128 isomorphic-coordinate controls; this retrospective screen supplies neither a relation in `d` nor an attributable CM gain. [pcc:unverified]

The [x-only ray sign gate](X_ONLY_RAY_SIGN_GATE.md) strengthens the additive-law conclusion: an `x`-only map has equal values at `P` and `-P`, whereas a nontrivial additive label in an odd-order ray subgroup must invert or negate. Thus the coordinate ideal above cannot satisfy the desired additive scalar law on any such curve where it is defined at `G`; its quadratic-character screen remains a separate question. [pcc:unverified]

The [signed three-sum ceiling](SIGNED_THREE_SUM_CEILING.md) counts forced cancellation collisions in any `2m`-point signed base: at `m=4`, no more than 96 distinct nonidentity three-sums are possible. The fixed source base attains 96, and a new exact source/degree-5-endpoint mixed-base census gives `92,92,96,96,96` as the number of source pairs rises from zero to four. This closes a same-size signed-base yield gain on this fixed pair; solver-cost changes remain separate. [pcc:unverified]

The [frozen equal-yield mixed-base cost panel](MIXED_EQUAL_YIELD_COST_REPORT.md) measures the remaining S4 solver-cost question for the two-source/two-endpoint base. Across 64 matched natural queries, three isomorphic coordinate models, two equal-support random controls and an admitted A/A control, the mixed/source CPU solve ratio is `0.984–0.993`; it misses the prespecified `0.90` component-gain threshold. Raw per-solve records and a complete process receipt are retained. [pcc:unverified]

The outstanding [CM point-to-ideal scalar bridge](../../problems/cm-point-to-ideal-scalar-bridge.md) records the missing construction, acceptance criteria, and next discriminating experiment. [pcc:unverified]

The [ray-class reduction audit](RAY_CLASS_REDUCTION_AUDIT.md) checks a proposed obstruction in the existing lead atlas. The identity `pi = 1 mod (pi-1)` correctly gives trivial Artin symbol at the relevant prime, but it does not identify the reduced Weber values: prime-to-`p` torsion reduction is injective. A class-number-one `D=-19`, `p=47`, `r=61` control gives 30 distinct reduced x-values, contradicting the older proposal's one-value prediction. The ray labels of those values remain unknown from their coordinates; this repairs the search boundary without supplying a point-to-ideal algorithm. Producer claim `PCC-20261124-cc75fc` is unverified. [pcc:unverified]

The [ray-label character gate](RAY_LABEL_CHARACTER_GATE.md) gives an exact point-dependent baseline: a quadratic-character resolvent satisfies `R(Q)=chi_r(d)R(G)` when `Q=[d]G`, and the same `D=-19` instance checks all 60 nonzero scalars. Its direct target pass costs about `r/2` group additions, far above same-target rho at P-192, and the identity is generic rather than CM-specific. A single low-degree x-only rational map cannot replace the full sum. A future CM proposal must supply a compact, charged evaluation of a useful ray-label quotient and beat this generic construction and rho on the same target. Producer claim `PCC-20261124-943a1c` is unverified. [pcc:unverified]

The [Gauss-resolvent orientation audit](GAUSS_RESOLVENT_ORIENTATION.md) identifies the close published prior art: universal elliptic Gauss sums compute character-invariant powers for Frobenius-eigenvalue point counting, while the target's character is the orientation that powering discards. In the finite control `R(G)^2=R(2G)^2=7 mod 47` although the unsquared values have opposite signs. The published construction retains cost proportional to its torsion prime `ell`; using `ell=r` does not supply the missing cheap oriented evaluator. The source-specific claim `PCC-20261124-e77745` is unverified. [pcc:unverified]

The [Frobenius-minus-one gate](FROBENIUS_MINUS_ONE_GATE.md) checks a degree-`r` horizontal endomorphism with a rational-point kernel. The map `1-pi` is cheap to evaluate but sends every rational point, including `G` and `Q`, to `O`; its dual acts on them by the known scalar `1-p mod r`. This corrects the inference that large isogeny degree alone forces expensive evaluation, while showing that this particular fast map erases the needed point distinction. Producer claim `PCC-20261124-f14459` is unverified. [pcc:unverified]

The same gate now checks the preimage fiber of `1-pi`: if `(1-pi)T=Q` and `Q` has order `r`, then `pi^m T=T-[m]Q`, so `T` has exact field degree `r` and every nonzero target gives an unlabelled `r`-cycle. Its cohomology class is `-Q=-[d]G`; expressing that class as `-d` requires the missing orientation. This is an exact point relation, not a cheaper scalar extraction. Producer claim `PCC-20261124-f773c1` is unverified. [pcc:unverified]

The [ray-kernel residue gate](RAY_KERNEL_RESIDUE_GATE.md) makes the pointed/unpointed split exact: for `n=(pi-1)` of prime norm `r`, the relative ray-class kernel is `F_r^*/{+1,-1}`. A smooth principal relation `alpha=a+b*pi` contributes the public residue `a+b mod r`. On the `D=-19` control, `1+pi` has smooth norm `35=5*7`, residue `2 mod 61`, and sends `G` to `[2]G`. This confirms the relation mechanism while locating the missing operation: assigning a ray residue or character to an independently supplied `Q` from its coordinates. Producer claim `PCC-20261124-01af6e` is unverified. [pcc:unverified]

The [additive point-to-class gate](POINT_TO_RAY_HOMOMORPHISM_GATE.md) proves a separate order obstruction on P-192: `h_K<2^104<r`, while the ray group has order `h_K(r-1)/2`. Hence every group homomorphism from the prime-order rational point group to either class group is trivial. A useful point-to-ray orientation must read coordinates through a nonadditive operation; the result leaves such maps and point-decomposition relations open. Producer claim `PCC-20261125-af70a5` is unverified. [pcc:unverified]

The [division-derivative screen](DIVISION_DERIVATIVE_SCREEN.md) tested one compact-circuit candidate for that missing character: the Legendre sign of the derivative of the full `r`-division polynomial at `x(Q)`, relative to `G`. On the `D=-19` control it agrees with the scalar's quadratic character for 28 of 60 nonzero scalars, and `d=4` is an explicit counterexample to exact equivariance. The derivative of the rational-line kernel polynomial gives the same 28/60 count there. This rejects the stated identity, without a P-192 cost claim or a general bound on other circuits. Producer claim `PCC-20261124-cc7020` is unverified. [pcc:unverified]

The [quadratic ray-subfield audit](QUADRATIC_RAY_SUBFIELD.md) identifies an explicit degree-two field `K(sqrt(1-pi))` with relative discriminant `(1-pi)` on both `D=-19` and P-192. It is a quadratic subfield of the ray class field, with a quartic defining polynomial over `Q` and a character on principal-ideal residues matching `chi_r`. Thus the full ray-field degree is not a construction-cost floor for **naming this one-bit quotient**. The construction itself uses only Frobenius and does not show a horizontal-isogeny advantage. The missing work remains a coordinate-dependent method that assigns the correct local root to `Q`, a matched ordinary-curve attribution control, and a full recovery cost case. Producer claim `PCC-20261124-cc257a` is unverified. [pcc:unverified]

The [ray-character factor map](RAY_CHARACTER_FACTOR_MAP.md) gives an exact coordinate-dependent one-bit bridge: split the nonzero subgroup x-coordinates by the quadratic character of their scalar labels, form two monic factors `F_+` and `F_-`, and evaluate `(F_--F_+)/(F_-+F_+)` at `x(Q)`. On the `D=-19` control it returns the right sign for all 60 nonzero scalars. Its rational-map degree is exactly `(r-1)/4`, attaining the earlier direct-map bound. At P-192 this is about `2^190`, with direct setup requiring about `2^191` group additions and dense evaluation requiring `Theta(2^190)` field multiplications per target. The identity is generic to prime-order subgroups; it exposes the precise object a CM-specific compression would have to evaluate, with setup and full-log cost charged. Producer claim `PCC-20261124-a61662` is unverified. [pcc:unverified]

The same note now checks horizontal transport: for an isogeny `phi` of degree coprime to `r`, the oriented label satisfies `f_{phi(G)}(x(phi(Q)))=f_G(x(Q))`. The existing `p=1009`, `r=1069` degree-5 horizontal instance checks this for all 1068 nonzero scalars; both factor maps retain degree 267. A smooth principal endomorphism acting as a known scalar only multiplies the same-source label by its known quadratic sign. This exact relation does not lower the factor degree or establish a cheaper evaluator on the codomain. Producer claim `PCC-20261124-0f2381` is unverified. [pcc:unverified]

The [bounded outer-character screen](LOW_DEGREE_OUTER_CHARACTER_SCREEN.md) tests a class outside the direct rational-map degree argument: `chi_p(h(x(Q)))` for all monic linear and quadratic `h` over `F_47`, including quadratic characters of defined linear-fractional maps. None gives the exact scalar character on either the `D=-19`, `r=61` instance or a different `D=-163`, `r=53` ordinary instance. A same-order degree-5 source/codomain comparison at `p=1009`, `r=1069` also finds no exact linear predicate on either curve. Best agreements are post-selected and cannot be promoted as predictors. This closes only the enumerated finite class, not compact circuits in general or the P-192 cost question. Producer claim `PCC-20261124-254331` is unverified. [pcc:unverified]

The [outer-character degree gate](OUTER_CHARACTER_DEGREE_GATE.md) supplies a separate exact-form bound: if `chi_p(f([d]G))=chi_r(d)` at every nonidentity point, then on P-192 the rational-map degree of `f` is at least `3961408125713216879677197517` (about `2^91.68`). A multiplier-averaged double-cover argument also bounds **full-group correlation**: when `deg(f)<=10` and `f` has no zero or pole on the nonidentity rational points, the best agreement after choosing either output sign is below `0.50002`. The proof uses Riemann--Hurwitz, Hasse--Weil, and Cauchy--Schwarz; it does not bound a high-degree compact circuit, adaptive combinations, or evaluation time. The [full-log gate](RAY_CHARACTER_FULL_LOG_GATE.md) observes that a hypothetical exact evaluator on translated points returns the shifted Legendre sequence `chi_r(d+a)`; the published classical hidden-shift route still has about a `sqrt(r)` work exponent and about `r^(1/4)` oracle queries, up to logarithmic factors. A CM benefit therefore needs a charged evaluator and full recovery comparison, not just one exact character bit. These deductions await independent review. [pcc:unverified]

The [aggregate-view character gate](AGGREGATE_VIEW_CHARACTER_GATE.md) applies the existing degree and correlation result to a fixed product of quadratic signs read through horizontal maps. For up to 100 maps of degree at most 100 and endpoint functions of degree at most 100, the product has degree at most one million. It cannot be an exact ray-character evaluator on P-192, and its best full-group agreement is below `1/2+1/7200` under the stated regularity assumptions. This derived bound leaves sequential high-degree circuits and target-adaptive rules open. [pcc:unverified]

The [smooth-kernel character screen](SMOOTH_KERNEL_CHARACTER_SCREEN.md) tests one high-degree function that can have a short isogeny-chain description. On the `D=-19` control, `1+pi` has norm `35=5*7`, and the quadratic character of its 17-degree x-kernel polynomial agrees with `chi_61(d)` on only 32 of 60 nonzero points after the best global sign choice. A separate `D=-163` control gives 28/52. On the same-order `p=1009` degree-5 horizontal source and codomain, both best sign choices give 538/1068, so this finite control shows no endpoint gain. The exact kernel and character censuses reproduce; the failed identity does not screen other smooth elements, combined predicates, or a P-192 compact evaluator. [pcc:unverified]

The subsequent [y-normalized EDS ray test](NORMALIZER_Y_RAY_REPORT.md) rejects another exact scalar-character candidate: 28/60 agreement on the frozen `D=-19` census, with the first mismatch at `d=4`. Its raw sign agrees with the anti-Frobenius kernel sign on that census. [Independent finite controls](NORMALIZER_KERNEL_EQUIVALENCE_REPORT.md) then found kernel-versus-normalizer character agreement on 52/52 points of `D=-163` and all 1068/1068 points on each endpoint of the `p=1009` horizontal edge. The later [exact value identity](EDS_KERNEL_NORMALIZER_IDENTITY.md) proves `K(x(P))=2y(P)Phi(P)^r` under the stated prime-order and coprimality hypotheses, so the character orientation is `chi_p(2)` and the two predicates are not independent. A `p=43` opposite-sign control checks that constant on all 46 nonzero points. Separately, the [generic kernel-value identity](GENERIC_KERNEL_EVALUATION_IDENTITY.md) proves `K(x(P))=-psi_2(P)psi_h(P)/psi_(h+1)(P)` for `h=(r-1)/2` on any prime-order short-Weierstrass curve. This permits `O(log r)` evaluation by standard division-polynomial recurrences without a smooth CM chain. Its exact values were checked on both complete `p=47` controls and eight points on each `p=1009` endpoint. The value identities remove a CM-specific evaluation premise; they do not compute the hidden scalar or improve the horizontal relation yield. [pcc:unverified]

The [EDS smooth-scalar gate](EDS_SMOOTH_SCALAR_GATE.md) checks a different published point-dependent bit, the field quadratic character of the division-polynomial term at the unknown scalar index. The composition identity gives `chi_p(W_G(2d))=chi_p(psi_2(Q))` for the `D=-19` smooth-norm scalar `1+pi`, but this cancels the unknown absolute EDS sign rather than computing it. The EDS sign is also not the ray character: their values disagree already at scalar two on that control. On P-192, even-index division-polynomial signs change under point negation while the ray character does not. Lauter–Stange's conditional reduction makes an absolute EDS-residue evaluator a meaningful full-log target, but the current smooth relation does not supply one. Producer claim `PCC-20261124-17c073` is unverified. [pcc:unverified]

The gate now instantiates one prerequisite of that published reduction: on the exact P-192 generator, the EDS normalizer `Phi(G)` is a quadratic nonresidue. Evaluated division-polynomial recurrences give `Phi(G)=0x1d10735da9aeffd5b5f65e3aca48654bbbf69949c49f14c0`; the defining ratio, a separate Ward-shift character formula, and a doubling identity agree. Thus the normalizer condition is met for a hypothetical absolute-residue evaluator on this generator. This is a known-point arithmetic check, not such an evaluator. Producer claim `PCC-20261124-202050` is unverified. [pcc:unverified]

The same normalization identity now makes the remaining bit explicit: for `Q=[d]G` on P-192, `chi_p(W_G(d))=chi_p(Phi(Q))*(-1)^d`. The point value `Phi(Q)` is computable without the scalar; the absolute EDS residue differs from it by the parity of the canonical `d`. The identity holds on all 60 nonzero labels of the `D=-19` control and on four known P-192 multiples. A smooth endomorphism acting as a known scalar obeys the generic identity `Phi([m]Q)=Phi(Q)^(m^2)psi_m(Q)`, so that action supplies no independent parity constraint. Producer claim `PCC-20261124-bf468c` is unverified. [pcc:unverified]
