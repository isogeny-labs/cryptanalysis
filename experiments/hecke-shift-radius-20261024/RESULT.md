# Short generator shifts close 2,800-column p20023 Hecke tables

**Measured result.** For four frozen subsets containing **2,800 of the original 3,949** p20023 orbit-table columns, verified generator shifts of at most four steps complete the anchored `GF(4021)` log system with the retained degree-2/3 Hecke rows. Radius three suffices for seeds A, B, and D; seed C has one residual dimension at radius three and reaches full rank at radius four. Every radius-one through radius-four result, including 33 incomplete cells, was independently replayed.

The [protocol](protocol.json) uses the same hash-ordered subsets as the earlier [density experiment](../hecke-shift-density-20261024/RESULT.md). For each retained projected point `Q`, radius `r` tests `Q+jG`, `1 ≤ j ≤ r`, and includes an edge only when the exact curve point is another retained table point. The edge equation is `log(Q+jG)=log(Q)+j`. Contracting connected shift components leaves one unknown log per component; the retained Hecke rows and generator anchor then determine their rank.

| Retained columns | A: first full radius | B: first full radius | C: first full radius | D: first full radius | Naive probes at radius four |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2,800 | **3** | **3** | **4** | **3** | 11,200 |
| 3,000 | 3 | 3 | 3 | 3 | 12,000 |
| 3,200 | 2 | 3 | 3 | 3 | 12,800 |
| 3,400 | 2 | 2 | 3 | 3 | 13,600 |
| 3,600 | 2 | 2 | **1** | 2 | 14,400 |

At 2,800 columns, the radius-one residual dimensions are **56, 58, 72, 66** for A–D. Radius two reduces them to **4, 7, 4, 5**; radius three gives **0, 0, 1, 0**; radius four gives **0** for all four. For seed A at 2,800 columns, radius three uses **8,400** point-lookup probes, finds **5,844** successful directed shift edges, and leaves **78** shift components, whose logs the retained **1,326** Hecke relations and anchor fully determine. Radius four uses 11,200 probes on the same table. These counts describe naive sequential `+G` generation from each point, with one curve addition and one lookup per probe; they are work counts rather than isolated timing measurements.

The [producer result](result.json) retains all 80 cells, including table and radius, subset digest, retained relations, successful edges, spanning-forest size, component count, quotient rank, zero-incidence count, and nullity. The [independent validator](validation.json) reconstructed every curve point, checked every successful `Q+jG` identity and corresponding saved-log difference, scalar-replayed all 3,949 table logs, checked all 5,565 original relation equations, and recomputed all 80 graph and sparse-matrix ranks with Sage. Its output matches every producer cell. The checked [Sage runtime](sage_runtime.json), raw [producer stream](producer_stdout.jsonl), raw [validator stream](validator_stdout.jsonl), and [attempt record](ATTEMPTS.json) preserve the execution history.

At radius four, the shift graph itself becomes connected at 3,600 columns for all four seeds; those cells need no Hecke row to connect components. At 2,800 columns it still has 22–27 components, so the retained Hecke rows contribute the cross-component rank. The structural generator-shift identity is proved in the pinned [Lean module](../hecke-l29-final-kernel-search-20261024/formal/ShiftClosure.lean); this experiment adds finite graph and rank measurements, not a new general theorem.

This remains reusable table preparation with `candidate_id: null` and `timing_claim: null`. The experiment selects subsets from an already constructed table. The next gate is to build and charge an actual sparse table from its source law, then measure an unseen one-target online solve against same-point rho in a calibrated environment.
