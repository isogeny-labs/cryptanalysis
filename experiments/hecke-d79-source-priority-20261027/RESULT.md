# Baseline-incidence priority changes rank timing but does not reach the D79 goal

On eight prospectively frozen, disjoint 40-point classes, the low-incidence source order reached the first new rank direction earlier in one class and later in two classes. The other five classes gained no rank direction under either order. Both orders used the same 40 degree-13 source lifts per class and the same F_q baseline rows. All eight full pools ended at rank 30 or 31, below the fixed rank-39 goal.

| Class p | q | Baseline → final rank | Verified rows | First rank-gain prefix, original | First rank-gain prefix, low incidence |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 830237 | 467 | 30 → 31 | 191 | 37 | 38 |
| 848557 | 233 | 30 → 30 | 190 | — | — |
| 900917 | 29989 | 30 → 30 | 190 | — | — |
| 943157 | 3923 | 30 → 31 | 196 | 25 | 31 |
| 962677 | 9619 | 30 → 30 | 190 | — | — |
| 1164557 | 1583 | 30 → 30 | 190 | — | — |
| 1168877 | 191 | 30 → 30 | 190 | — | — |
| 1208117 | 15121 | 30 → 31 | 192 | 28 | 14 |

The independent Sage audit checked the public prime/order prescreen, all eight exact 40-point classes, baseline incidence and the two sealed orders, all 320 degree-13 source equations, static pair-index relation counts, every prefix rank and novel-row increment, and the full-cap stop status. It verified all case hashes against the sealed producer index. The checked Sage runtime, selector, pre-run and post-run seals, raw producer output, and audit output are retained in this directory.

This paired replay rejects low baseline incidence as a reliable source-priority rule on the measured panel. The full-pool rank is order-invariant here because both orders insert the same 40 sources; the comparison tests when each order exposes its rank increments. Since neither order reached rank 39, the experiment records no successful rank-stop improvement. The shared full-pool lift cost is charged as a diagnostic; the replay intervals are exploratory local stage timings without Tier 0/1 isolation. `candidate_id` and `target_online_ms` remain null.

The next constructive step is to change the **source family or relation support**, rather than reorder this fixed pool. The 190 common rows in every rank-30 case indicate a repeated dependent relation pattern. A prospective experiment should freeze an additional independent relation generator, such as verified five-source cancellations or another Hecke degree, and test its incremental rank against the same baseline on a new panel. Its search cost and all failed attempts must be retained.
