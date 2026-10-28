# D79 support-eight query ordering

Reverse lexicographic order reduced signed quintuple queries through the first verified rank-39 row by **6,942,025 across eight disjoint fresh classes**, from 53,958,650 under lexicographic order to 47,016,625. This is a 12.87% reduction relative to the lex count, with the selected order lower in all eight paired cases. Each pair used the same degree-13 source stream and reached rank 39 at the same source count. The order changes which four earlier sources are queried first; it leaves the signed query set, row verification, rank rule, and stop threshold unchanged.

## Selection and controls

The frozen design panel compared four deterministic orders on eight prior full-row classes. Reverse lex had the lowest summed within-final-source query position, 172,870, versus 3,505,018 for lex, 178,414 for latest-min, and 356,110 for largest-sum. One design case already reached rank 39 from lower support rows and correctly contributed zero query position for every policy. The first design scorer failed on this zero-query case; `DESIGN_AMENDMENT.md` retains the failure and the corrected, sealed scorer. The known p=2,076,797 control reproduced its design final-source positions of 330,653 (lex) and 12,817 (reverse lex) before the holdout lifts.

The holdout selector began at odd v=1803, after the prior panel's v=1801 endpoint, and froze the next eight ready classes, their point lists, subgroup orders, baseline rows, source order, accepted Sage runtime, policy code, resource caps, and cache digest. The first producer launch was interrupted after one complete control and 33 checkpointed sources of the first fresh class; those immutable artifacts are retained under `interrupted-run/` and excluded from the aggregate. The same sealed producer restarted from source zero.

## Paired holdout

| p | q | First rank-39 source count, both | Lex probes | Reverse-lex probes | Lex / reverse | Support-seven final rank |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3280037 | 1483 | 37 | 13,293,084 | 12,064,156 | 1.102 | 37 |
| 3309077 | 277 | 28 | 3,108,205 | 2,589,014 | 1.201 | 38 |
| 3382237 | 97 | 33 | 7,594,433 | 6,444,321 | 1.178 | 35 |
| 3456197 | 6779 | 31 | 5,435,884 | 4,561,452 | 1.192 | 34 |
| 3500957 | 457 | 33 | 7,479,016 | 6,468,450 | 1.156 | 38 |
| 3530957 | 141161 | 28 | 3,108,374 | 2,591,338 | 1.200 | 35 |
| 3538477 | 32159 | 29 | 3,712,975 | 3,232,143 | 1.149 | 37 |
| 3760037 | 719 | 35 | 10,226,679 | 9,065,751 | 1.128 | 38 |

The sum ratio is **1.14765** lex/reverse. Both arms have rank-39 anchored log replay in the producer summaries. The support-seven-only arm finished the 40-source pool at ranks shown above; its rank status is retained separately. Exact probe counts, row groups, per-source phase times, source equations, hashes, and replay certificates are in `cases/` and `index.json`. This is a query-order component comparison on an ordinary local host. The run records keep `candidate_id` and `target_online_ms` null because the measured interval is support-eight relation collection, not a complete single-target IC pipeline. CPU wall times are exploratory under the repository tier contract.

## Verification and next step

The independent Sage audit verifies the frozen selection, every source group equation, complete support-four through seven relation sets, support-eight relation sets by an independent four-plus-four split, each arm's final ordered three-plus-five query prefix to its exact stopping probe, modular rank trajectories, phase sums, file hashes, and anchored log replays. The next experiment is to prioritize the first rank-raising support-eight row using a point- or rank-aware heuristic frozen on a separate design panel, then test on another disjoint prospective panel with the same paired accounting.
