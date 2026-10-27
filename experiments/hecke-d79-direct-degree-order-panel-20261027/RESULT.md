# Direct-relation degree did not improve early rank on four fresh D79 classes

The frozen low-direct-degree order reached its first rank gain later than ascending index order in each of the three classes with a gain. At p151637, all 40 source lifts produced 190 verified Hecke rows, but those rows added zero rank over F_149. The direct-degree hypothesis is therefore unsupported by this four-class panel.

| Class p | q | Direct rank | Full rank | Hecke rows | Ascending first gain | Low-degree first gain | High-degree first gain | SHA first gain |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 129197 | 461 | 34 | 36 | 195 | 23 | 28 | 31 | 33 |
| 137957 | 137 | 31 | 33 | 198 | 19 | 21 | 21 | 26 |
| 145477 | 61 | 34 | 37 | 199 | 17 | 22 | 22 | 24 |
| 151637 | 149 | 32 | 32 | 190 | — | — | — | — |

For p145477, the three full-pool rank gains arrive at counts 17/20/36 ascending, 22/37/40 low degree, 22/32/39 high degree, and 24/30/34 SHA. None of the four full pools reaches the prespecified rank-39 target. The rank-gain prefix sums over counts 1..40 are retained in `audit.json`; ascending has the largest sum in every class with a gain. The exact direct-degree counts vary within each class (ranges 19–25, 19–37, 19–26, and 19–21), so the order test was not a tie-only comparison.

All 160 degree-13 source lifts completed with `OUTSIDE_CLASS_TRACE` status. The independent Sage audit rechecked the public prime/order prescreen, direct relations, 160 source group equations, 782 Hecke group rows, every prefix rank, and source-lift sums. Selection, orders, and baseline rows were hash-sealed before degree-13 work; producer output was sealed before the independent audit. Raw statuses, intervals, stdout/stderr, and the checked Sage runtime receipt are retained.

These are four selected classes, not an estimate of a general advantage for ascending index order. The virtual order replay shares the same source outputs and does not measure a live rank-stopped scheduler. The result directs the next experiment away from direct-row frequency and toward structure in the actual Hecke row dependencies or a provable rank-gain bound. `candidate_id` and `target_online_ms` remain null.

This panel adds empirical ranks, not a new general mathematical theorem. The full matrix/curve Lean bridge for D79 relation claims remains open in the earlier series `PROOF_MAP.md`.
