# Six-source cancellations add 36 D79 class-rank directions

Exact signed six-source enumeration produced **3,909 verified relation rows** across the eight sealed full-source D79 classes. Those rows added **36 F_q rank directions** beyond their base, direct, and support-at-most-five relations. Every class gained 3–7 directions, and three reached rank 37. All eight searches completed the full canonical support/sign space within the frozen row and wall caps.

| Class p | q | Rank through five sources | Six-source rows | New directions | Rank through six sources | Search wall (ms) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1212517 | 11551 | 33 | 696 | 4 | 37 | 210.43 |
| 1343597 | 521 | 32 | 471 | 5 | 37 | 208.70 |
| 1366877 | 8537 | 30 | 453 | 3 | 33 | 202.09 |
| 1395077 | 907 | 31 | 445 | 4 | 35 | 243.98 |
| 1418797 | 439 | 30 | 445 | 4 | 34 | 205.20 |
| 1442717 | 1031 | 30 | 468 | 7 | 37 | 202.36 |
| 1491157 | 359 | 30 | 500 | 6 | 36 | 200.79 |
| 1510757 | 75521 | 31 | 431 | 3 | 34 | 202.67 |

For each class, the producer inserted 39,520 canonical signed first triples and probed 79,040 signed latter triples, retaining only ordered disjoint supports. It verified every emitted class-point equation before inserting the row into the F_q basis. The reported search interval includes triple-index construction and queries, but excludes the previously charged source lifts and support-at-most-five collection. These are exploratory local component times without Tier 0/1 isolation; `candidate_id` and `target_online_ms` remain null.

The independent Sage audit used the reverse indexing direction. It rechecked all 320 retained source equations, source and result hashes, baseline point relations and rank, every six-source support/sign/row tuple, every emitted point equation, complete triple operation counts, caps, and final F_q ranks. All eight cases have `COMPLETE` producer and `PASS` audit status. The frozen runtime and source receipts are retained here.

Six-source cancellation supplies independent directions in every class, substantially changing the rank-yield pattern seen with five sources. The highest final rank is 37 on this panel. The next mechanism test should evaluate exact seven-source cancellations, preferably with a bounded three-plus-four index, before freezing a new live collector. A prospective collector must charge all source lifts and search attempts and verify any rank-39 anchor-log solution.
