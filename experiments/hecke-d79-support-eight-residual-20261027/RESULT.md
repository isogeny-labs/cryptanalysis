# One support-eight relation closes the p1825517 D79 rank residual

An exact signed eight-source cancellation raised the frozen p1825517, q6091 class from **rank 38 to rank 39**. Adding that row to the earlier base and support-four through seven relations yielded a unique anchored solution for the 40 q-projected class-point logarithms, and all 40 scalar replays passed. The independently checked row uses sources `(0, 3, 4, 6, 8, 9, 30, 31)` with signs `(+,+,-,-,-,+,-,-)`.

| Run | Probe cap | Signed quintuple probes | Matches / verified rows | Final F_6091 rank | Search wall | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Initial frozen bound | 12,000,000 | 12,000,000 | 168 / 168 | 38 | 35.01 s | Censored at probe cap |
| Full-space follow-up | 22,000,000 | 12,323,269 | 225 / 225 | 39 | 36.31 s | Rank goal; 40 anchored replays pass |

Both runs used the same 40 sealed source equations and frozen rank-38 row set. The search indexed 39,520 signed triples and probed lexicographically ordered signed quintuples using a three-plus-five split. Every matched row was checked as an elliptic-curve point equation before rank insertion. The second run stopped at the first novel direction, 323,269 probes after the first run's cap. It did not need to enumerate the remaining search space.

The independent Sage audit rechecked the source equations, base rank, selected eight-source outside-trace cancellation, assembled class-point row, new F_6091 rank, anchored linear solve, and 40 scalar replays. The parent and follow-up protocols, code, runtime receipts, and frozen inputs are SHA-256 sealed in their separate pre-run manifests. The full protocol contains a typo in its parenthetical complete-space probe count: `binomial(40,5) * 2^5 = 21,056,256`; its **22,000,000 probe cap** and the producer's stopping rule are correct.

This measured component result shows that support-eight cancellation supplies the one missing direction for this retained class. The local wall times are exploratory and lack Tier 0/1 isolation. `candidate_id` and `target_online_ms` remain null. The next test is a prospectively frozen live support-eight collector on disjoint classes, paired with support-seven source counts and exact row audits.
