# Append-only per-class journals remove growing checkpoint cost

The rank-stopped collector now writes each source step once to a compact, fsynced JSONL journal for its own class. Across eight prospectively selected 40-point classes, the total checkpoint interval stayed between **5.69 and 7.20 ms per class**, and residual loop overhead stayed between 0.26 and 0.46 ms. The previous aggregate-result rewrite had a 43.85–235.08 ms recording-and-overhead term that grew across its separate eight-class panel. The two panels differ in curve inputs and run conditions, so this is an implementation diagnostic rather than a matched wall-time performance estimate.

The known p103357 control again stopped after source 35 at rank 39. One q-projection anchor recovered and replayed all 40 class logs. All eight newly selected classes completed their 40-source caps; final ranks were 30–32. Their exact q fields, relation counts, and charged intervals are retained below.

| Cohort | p | q | Baseline → final rank | Sources | Verified rows | Collector wall (ms) | Fsynced checkpoint sum (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Known-success control | 103357 | 197 | 35 → 39 | 35 | 120 | 1309.23 | 6.21 |
| Fresh | 398477 | 6653 | 30 → 30 | 40 | 190 | 741.51 | 6.76 |
| Fresh | 408637 | 877 | 30 → 30 | 40 | 190 | 826.69 | 6.39 |
| Fresh | 411197 | 5861 | 30 → 31 | 40 | 196 | 1365.38 | 6.87 |
| Fresh | 434597 | 1523 | 30 → 32 | 40 | 206 | 1342.25 | 5.69 |
| Fresh | 447877 | 1993 | 30 → 31 | 40 | 191 | 724.67 | 5.87 |
| Fresh | 450557 | 67 | 31 → 31 | 40 | 190 | 1291.18 | 6.68 |
| Fresh | 475037 | 461 | 30 → 31 | 40 | 191 | 606.73 | 7.20 |
| Fresh | 477797 | 113 | 30 → 30 | 40 | 190 | 818.41 | 6.65 |

The independent Sage audit verified the public prime/order prescreen, direct rows, all 355 source equations, all 1,664 emitted group rows, every prefix rank, the control's stopping point and anchored log replay, every journal and summary hash, and the exclusive accounting identity:

`collector_wall = source_lifts + index_and_relation_checks + rank_updates + fsynced_checkpoints + loop_overhead`.

Each journal is 38–66 KiB and carries all newly emitted rows and source receipts. A compact aggregate index seals every journal and summary digest. The checked Sage runtime, source snapshots, stdout/stderr, and audit are retained. The phase intervals are exploratory local diagnostics without Tier 0/1 isolation; `candidate_id` and `target_online_ms` remain null.

The new checkpoint format makes source-level progress durable without serializing earlier classes again. The next experiment should inspect why full 40-source pools in these first eligible classes gain little rank, especially the outside-trace cancellation and relation-dependency distributions. A prospective source-selection rule should be frozen before the next lift panel.
