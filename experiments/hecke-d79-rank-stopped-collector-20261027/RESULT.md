# A live incremental collector stops at rank 39 and replays 40 class logs

The append-only pair index, verified source lifts, and incremental F_q row basis reached rank 39 on the known p103357 control after **35 source lifts**. A q-projection anchor then determined all 40 class logs, and every projected point replayed. The independently audited collector emitted exactly the 120 relations available on that prefix. This live stop reproduces the earlier retained-prefix result with charged lift, index, rank, and recording intervals.

The eight prospectively selected classes each exhausted the 40-source cap. Their full-pool ranks stayed at 30–32; three gained one rank direction and five gained none. Each result is retained as `FULL_POOL_BELOW_RANK_GOAL`, with its q field, source equations, verified rows, rank trajectory, and wall accounting.

| Cohort | p | q | Baseline → final rank | Sources | Verified rows | Collector wall (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Known-success control | 103357 | 197 | 35 → 39 | 35 | 120 | 1267.21 |
| Fresh | 167597 | 97 | 31 → 31 | 40 | 190 | 752.09 |
| Fresh | 212837 | 593 | 32 → 32 | 40 | 190 | 774.17 |
| Fresh | 231677 | 1447 | 31 → 32 | 40 | 191 | 693.61 |
| Fresh | 249317 | 521 | 30 → 30 | 40 | 190 | 1369.17 |
| Fresh | 290837 | 313 | 30 → 31 | 40 | 196 | 850.71 |
| Fresh | 303917 | 409 | 30 → 31 | 40 | 191 | 1496.59 |
| Fresh | 315037 | 31489 | 30 → 30 | 40 | 190 | 1050.93 |
| Fresh | 335557 | 431 | 31 → 31 | 40 | 190 | 999.11 |

The control's charged collector interval partitions into 1241.41 ms of source lifting, 6.57 ms of source/index verification and relation insertion, 1.74 ms of rank updates, and 17.50 ms of checkpoint I/O and loop overhead. Anchor solve and replay are recorded separately. Across the eight fresh classes, the median collector interval was 924.91 ms and the median source-lift sum was 723.71 ms. Checkpoint serialization grows with the accumulated result file, contributing 43.85–235.08 ms across the fresh sequence; this must be fixed before treating the wall record as a scheduler optimization result. These are exploratory local stage intervals without a Tier 0/1 isolation receipt. `candidate_id` and `target_online_ms` remain null.

The independent Sage audit rebuilt the public prime/order prescreen, direct relations, 355 source equations, all 1,648 emitted class rows, every prefix rank and novel-row count, the stop condition, and the control's anchored log replay. It compared each emitted relation set with the pinned complete pair-index enumerator on that exact retained prefix. A separate ten-class retrospective replay checked the incremental index and rank basis against the sealed prior traces before the live run.

The new collector is a working rank-stopped relation and class-log component. The fresh panel shows that selecting the first eight eligible classes yields little rank gain from the allowed four-source cancellations. The next experiment should study the outside-trace collision distribution and class-rank structure before committing additional source lifts, while a new collector version should checkpoint each class separately to remove growing serialization overhead.
