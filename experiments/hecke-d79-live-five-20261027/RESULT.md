# Live five-source collection reaches D79 control rank 39 after 30 lifts

The rank-stopped collector integrated exact signed five-source cancellations into the source-by-source D79 pipeline. On the separately retained p103357 control, it reached rank 39 after **30 degree-13 source lifts**, then recovered and independently replayed all 40 q-projected class logs. The earlier support-at-most-four collector required 35 lifts on the same frozen class and source order. This is a source-count improvement on that control; the two versions' local wall intervals are exploratory and do not establish a matched timing ratio.

The eight newly frozen classes all exhausted the 40-source cap. Five-source rows added one rank direction in two classes, and none in six. Final ranks were 30–33. Every full-cap status and zero-yield case is retained.

| Cohort | p | q | Baseline → final rank | Lifts | Rows with support ≤4 | Five-source rows | New directions from five | Collector wall (ms) | Five-source search (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Known control | 103357 | 197 | 35 → 39 | 30 | 50 | 4 | 1 | 1589.61 | 47.88 |
| Fresh | 1212517 | 11551 | 31 → 33 | 40 | 196 | 3 | 1 | 3100.78 | 229.17 |
| Fresh | 1343597 | 521 | 32 → 32 | 40 | 190 | 0 | 0 | 1652.64 | 187.01 |
| Fresh | 1366877 | 8537 | 30 → 30 | 40 | 190 | 0 | 0 | 2555.06 | 205.61 |
| Fresh | 1395077 | 907 | 30 → 31 | 40 | 190 | 30 | 1 | 1683.37 | 239.53 |
| Fresh | 1418797 | 439 | 30 → 30 | 40 | 190 | 0 | 0 | 2230.93 | 209.81 |
| Fresh | 1442717 | 1031 | 30 → 30 | 40 | 190 | 0 | 0 | 2455.59 | 231.33 |
| Fresh | 1491157 | 359 | 30 → 30 | 40 | 190 | 0 | 0 | 2517.81 | 186.76 |
| Fresh | 1510757 | 75521 | 31 → 31 | 40 | 190 | 0 | 0 | 1302.46 | 181.65 |

The producer wrote a compact, fsynced journal record after each source and stopped immediately when the rank goal was attained. Its charged collector interval partitions exactly into source lift, four-source index and row verification, five-source search and row verification, rank update, checkpoint, and loop overhead. Setup and anchored log replay were recorded separately. The local wall intervals are exploratory component diagnostics without Tier 0/1 isolation; `candidate_id` and `target_online_ms` remain null.

Before this run, the live five-source index matched every exact relation in the earlier audited eight-class panel. The independent Sage audit then verified the new panel's public prescreen, all 350 retained source equations, complete four- and five-source row sets on each retained prefix, every F_q rank increment and stop, every journal hash, exclusive phase sums, and the control's anchored log replay. All nine cases have `PASS` audit status.

The control demonstrates an operational benefit from five-source relations. The fresh panel shows that five-source zero sums are sparse and often add no new direction at this 40-source cap. The next mechanism test should evaluate exact six-source cancellations with a three-plus-three index on these sealed records, including zero-yield cases and search costs, before freezing another prospective collector.
