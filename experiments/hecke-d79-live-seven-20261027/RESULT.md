# Live seven-source collection reaches rank 39 on seven fresh D79 classes

The prospective live collector reached **rank 39 with independently replayed logs for all 40 q-projected class points** in seven of eight newly frozen D79 classes. Their measured source stops were 33–40 degree-13 lifts. The eighth class, p1825517, completed the 40-source cap at rank 38. On the separately retained p103357 control, the collector stopped after **14 lifts**, compared with 30 for the preceding live support-five collector on the same class and source order.

| Cohort | p | q | Baseline → final rank | Lifts | Rows with support ≤4 / 5 / 6 / 7 | Collector wall (ms) | Seven-source search (ms) | Status |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Known control | 103357 | 197 | 35 → 39 | 14 | 3 / 0 / 3 / 3 | 635.99 | 30.16 | Rank goal, replay pass |
| Fresh | 1590437 | 2341 | 30 → 39 | 35 | 105 / 3 / 134 / 406 | 2522.96 | 1749.62 | Rank goal, replay pass |
| Fresh | 1636157 | 163477 | 30 → 39 | 33 | 91 / 4 / 113 / 366 | 2711.90 | 1369.72 | Rank goal, replay pass |
| Fresh | 1692917 | 2777 | 30 → 39 | 33 | 91 / 0 / 118 / 265 | 2688.69 | 1342.85 | Rank goal, replay pass |
| Fresh | 1713797 | 607 | 30 → 39 | 36 | 136 / 0 / 152 / 398 | 3550.63 | 1995.71 | Rank goal, replay pass |
| Fresh | 1771877 | 83 | 30 → 39 | 40 | 190 / 4 / 430 / 1316 | 4818.65 | 3080.38 | Rank goal, replay pass |
| Fresh | 1793237 | 44843 | 30 → 39 | 34 | 105 / 0 / 109 / 194 | 2299.10 | 1541.25 | Rank goal, replay pass |
| Fresh | 1825517 | 6091 | 30 → 38 | 40 | 190 / 0 / 480 / 1180 | 4918.05 | 3106.99 | Full cap, rank 38 |
| Fresh | 1852637 | 2939 | 30 → 39 | 34 | 91 / 1 / 224 / 474 | 2959.77 | 1542.52 | Rank goal, replay pass |

The source order, classes, q fields, cache/source digests, rank-39 stop, and 40-source cap were frozen before new degree-13 lifts. An exact preflight matched the incremental six- and seven-source indexes against all 3,909 and 10,171 rows of the earlier audited full-pool panel. The live producer wrote and fsynced each source journal record before moving to the next source. Its charged interval partitions into lift, support-at-most-four, support-five, support-six, support-seven, triple-index update, rank, checkpoint, and residual loop terms; setup and anchor replay are separately recorded.

The independent Sage audit checked the public prescreen, all **299 retained source equations**, exhaustive direct rows, exact support-at-most-four through support-seven relation sets on each retained prefix, every F_q rank increment and stop, journal hashes, exclusive phase sums, and all eight anchored replays. It confirmed the p1825517 full-cap rank-38 result. All nine cases have `PASS` audit status.

The control's 14-versus-30 comparison is a source-count result on the same frozen class. The wall intervals are exploratory local component diagnostics without Tier 0/1 isolation and do not supply a calibrated timing ratio. `candidate_id` and `target_online_ms` remain null. The next experiment should inspect the p1825517 rank-38 residual with an exact bounded support-eight search, then freeze a new disjoint live panel if the added relation family proves useful.
