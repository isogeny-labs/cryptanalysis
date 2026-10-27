# Verified relation volume does not predict D79 class-rank gain

The sealed nine-case journal analysis shows that the eight fresh classes emitted **190–206 verified relation rows each**, but gained only **0–2 rank directions** over their direct-relation baselines. Four fresh classes gained no direction, three gained one, and one gained two. The known p103357 control began at rank 35 and gained four directions by source 35, reaching the rank-39 goal. The first fresh rank increase, when present, appeared at source 18, 22, 27, or 35. Exact per-source row/rank trajectories and source file hashes are in [`analysis.json`](analysis.json).

| Class p | q | Baseline → final rank | Verified rows | Rows dependent modulo baseline | Sources with rows | First rank gain | Outside-trace incidences |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 103357 control | 197 | 35 → 39 | 120 | 116 | 17 | 23 | 35 |
| 398477 | 6653 | 30 → 30 | 190 | 190 | 19 | — | 160 |
| 408637 | 877 | 30 → 30 | 190 | 190 | 19 | — | 120 |
| 411197 | 5861 | 30 → 31 | 196 | 195 | 20 | 18 | 40 |
| 434597 | 1523 | 30 → 32 | 206 | 204 | 21 | 22 | 40 |
| 447877 | 1993 | 30 → 31 | 191 | 190 | 20 | 27 | 160 |
| 450557 | 67 | 31 → 31 | 190 | 190 | 19 | — | 80 |
| 475037 | 461 | 30 → 31 | 191 | 190 | 19 | 35 | 240 |
| 477797 | 113 | 30 → 30 | 190 | 190 | 19 | — | 120 |

Every outside trace within each class journal was distinct as an exact encoded point. The relation collector forms four-source cancellations from pair sums, so repeated single traces are not required for verified rows. The wide range of outside-trace incidence counts (40–240 in the fresh panel) did not distinguish the classes with rank gains from those without them. This is an observed feature of this fixed panel, not a causal test of trace multiplicity.

The analysis checks each journal and summary against the preceding run's aggregate SHA-256 index, then checks source sequence, emitted-row totals, and rank increments against each case summary. It preserves all full-cap outcomes. Its contribution is a concrete next gate: screen for **baseline rank and incremental rank yield**, not raw relation count alone. A next prospective experiment should freeze a disjoint class panel before any degree-13 lifts, stratify by baseline rank, and compare a fixed source-priority rule against source order on the same exact class. The original 40-source cap and q-field rank goal should stay fixed; successes require independent anchor-log replay. This diagnostic is a component record with `candidate_id` and `target_online_ms` null.
