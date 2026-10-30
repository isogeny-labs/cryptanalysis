# Prior-certificate order advances first rank gain on two fresh D79 classes

The 12 source indices learned from the p103357 rank certificate were frozen as a front-of-order priority on two new 40-point classes. On p122117, that order first gains rank after 20 sources, versus 28 in ascending order. On p123517, it first gains rank after 15 sources, versus 25 ascending. The full 40-source pools reach ranks 33 and 34 respectively, so none of the three frozen orders reaches the rank-39 target in these cases.

| Class p | q | Baseline rank | Full rank | Hecke rows | Ascending first gain | Certificate-first first gain | SHA first gain | 40-lift sum |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 122117 | 127 | 32 | 33 | 196 | 28 | 20 | 25 | 1.284 s |
| 123517 | 2749 | 32 | 34 | 208 | 25 | 15 | 15 | 0.881 s |

The p123517 second gain arrives at source 26 ascending, 29 certificate-first, and 26 in SHA order. The cumulative rank-gain prefix sums over counts 1..40 are 13/21/16 for ascending/certificate-first/SHA at p122117 and 31/38/41 at p123517. Thus the transferred order improves the first-gain count against ascending in both selected cases, while SHA has the larger cumulative gain on p123517. These are two frozen classes, not a population estimate or an established scheduler policy.

The selector retained the first two eligible classes after the earlier four-class series and sealed all three complete orders before degree-13 work. Every one of the 80 source lifts completed with `OUTSIDE_CLASS_TRACE` status. The independent Sage audit re-evaluated the public prime/order prescreen, rebuilt direct relations by pair lookup, verified all 80 source equations and 404 Hecke rows in the curve group, and recalculated every frozen prefix rank and lift-time sum. `selection.json`, `challenge.json`, the SHA receipts, raw stdout/stderr, and the checked Sage runtime receipt are retained.

The order comparison replays one shared set of lift outputs per class. Its source counts measure the availability of rank-increasing rows under each order; the recorded lift intervals are component measurements, not a live scheduler wall time. `candidate_id` and `target_online_ms` remain null. The next useful study is a larger fresh-class panel with an order chosen from group-theoretic information before lifting, followed by an actual stopped-on-rank implementation on classes whose full pools reach the target rank.

This experiment adds empirical rank measurements rather than a new general mathematical theorem. The existing full matrix/curve Lean bridge remains open in the preceding series `PROOF_MAP.md`.
