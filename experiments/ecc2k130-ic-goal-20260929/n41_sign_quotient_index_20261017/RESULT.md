# Sign quotient halves the exact N41 three-pair index

On the frozen unpinned six-pair public-point query, storing one left triple
per simultaneous-negation orbit reduced the index from **3,750,144 to
1,875,072 rows**. The resulting exact join returned the archived state IDs
`(12,122,116,47,128,34)` and passed independent checked-Sage curve and
column replay. In the first same-host alternating pair, the complete sorted
lookup took **2.984 s** versus **2.033 s** for the sign quotient, and sampled
combined peak RSS fell from **145,817,600 B** to **85,950,464 B**. These are
ordinary-host component measurements on the same raw public point, input,
one worker, 60 s wall cap, and 4 GiB RSS cap.

## Exact construction

Each source state has a unique same-column partner representing its negative
point. The native program checks this involution for all 960 states. It stores
only triples whose first state ID is smaller than its sign partner. Every
omitted admissible triple is the simultaneous negation of exactly one stored
triple; the folded columns remain unchanged. For a right partial sum `R`
and target `Q`, the lookup searches both `Q-R` and `-(Q-R)`. A hit in the
second key flips all three stored state IDs to their checked partners before
testing the raw group equation and twelve-column disjointness.

The [Lean theorem](NegationQuotient.lean) proves triple negation and the
either-sign target lookup in an additive commutative group. Its `#print axioms`
output is saved in [lean.stdout](lean.stdout). The source-state involution
and binary-curve bridge are finite checks of the frozen input and independent
[Sage replay](audit_result.json), respectively; see [proof map](PROOF_MAP.md).

## Frozen evidence

The [protocol](protocol.json) pins the N41 field/curve source, input and
target, C++ source and runner hashes, compiler command, and resource caps.
The checked [Sage runtime receipt](sage_runtime_info.json) was saved before
the measured runner. The [capped run](run_result.json) returned the same
archived relation in 2.402 s parent wall, with 86,065,152 B sampled combined
peak RSS; its monitor recorded a sample failure. The
independent Sage audit reconstructed all
twelve curve points from the original source geometry, checked pair sums,
distinct columns, raw target equality, and subgroup target projection.

The alternating [comparison](bench_result.json) used already compiled,
hash-checked binaries and the same input. Every run returned the identical
six state IDs. The wall interval includes process launch, input read, left
index build, right query, and native replay; it is a component interval, not
the one-target IC online metric.

| Order | Index | Left rows | Parent wall | Sampled combined peak | Monitor |
| ---: | --- | ---: | ---: | ---: | --- |
| 0 | Full sorted | 3,750,144 | 2.984 s | 145,817,600 B | healthy |
| 1 | Sign quotient | 1,875,072 | 2.033 s | 85,950,464 B | healthy |
| 2 | Sign quotient | 1,875,072 | 2.030 s | 85,966,848 B | healthy |
| 3 | Full sorted | 3,750,144 | 3.018 s | 145,948,672 B | monitor race at process exit |

The first healthy pair yields a **1.468 times** component wall ratio and a
**41.1%** lower sampled combined memory peak. The final baseline run's
transient monitor flag is retained; its successful exit, hit, and native
self-peak are present in the raw output, while its combined peak is
descriptive. `candidate_id` remains `null` because this is an index-stage
variant, not a fully specified IC pipeline.

## Next exact gate

The quotient is a factor-two reduction. Applied literally to the frozen
N131 W23 source's three-pair side, the `(4E)^3/2` count remains about
`3.70e19` rows before cross-column exclusions for `E=1,049,218`, outside
the 4 GiB and 600 s relation gate. The next iteration should use this
quotient inside a target-conditioned constraint that rejects families of
three still-free pair sources before their sums are enumerated. Test its
losslessness and cost on this same unpinned N41 public point before a frozen
N131 ordinary relation query.
