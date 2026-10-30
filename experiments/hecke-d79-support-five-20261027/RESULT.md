# Five-source cancellations add 11 class-rank directions across eight D79 classes

Exact signed five-source enumeration found **43 verified rows** across the sealed eight-class panel. They added **11 F_q rank directions** beyond the base, direct, and support-at-most-four rows: five classes gained 1–4 directions, while three produced no five-source row. All eight searches completed the full canonical support/sign space without hitting the frozen row or wall cap.

| Class p | q | Rank through four sources | Five-source rows | New directions | Rank through five sources |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 830237 | 467 | 31 | 16 | 2 | 33 |
| 848557 | 233 | 30 | 10 | 4 | 34 |
| 900917 | 29989 | 30 | 0 | 0 | 30 |
| 943157 | 3923 | 31 | 5 | 2 | 33 |
| 962677 | 9619 | 30 | 0 | 0 | 30 |
| 1164557 | 1583 | 30 | 7 | 2 | 32 |
| 1168877 | 191 | 30 | 5 | 1 | 31 |
| 1208117 | 15121 | 31 | 0 | 0 | 31 |

The producer indexed all 3,120 signed source pairs per class and probed all 39,520 canonical signed source triples, accepting only disjoint ordered supports `i<j<k<l<m`. Each verified row was checked as an elliptic-curve point equation before F_q insertion. The complete enumeration interval was 64.69–152.69 ms per class on the local host; those exploratory stage intervals exclude source lifting and are not an online target metric.

The independent Sage audit constructed a separate triple-sum index, enumerated all matching signed pairs, compared every canonical support/sign pattern and class-part row with the producer, checked all 320 retained source equations and every emitted point relation, and rebuilt both the support-four baseline and final F_q rank. The checked runtime, frozen input and code hashes, raw case records, output status, and audit are retained here. All cases have `COMPLETE` producer and `PASS` audit status.

This retrospective mechanism test identifies five-source cancellation as a concrete source of additional rank. The highest final rank in this panel is 34; the fixed rank-39 goal remains an open experimental gate. The next test should freeze a disjoint class panel and a live support-five rank-stop collector before degree-13 lifts, with source-lift, pair/triple search, row verification, rank, checkpoint, and anchor-replay costs charged separately. `candidate_id` and `target_online_ms` remain null for this component study.
