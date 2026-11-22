# Streaming threshold check for M31 ordinary fibers

When searching for at least t lifts among 32 coordinates, a partial fiber with more than 32−t misses can be discarded immediately. Early.lean proves that the unfinished fiber cannot qualify. The GP implementation stops generating auxiliary points at that point. Qualifying fibers are fully traversed and materialized with the same routine as the ordinary control.

Run gp -q -f panel.gp. Each process draws the same 6144 distinct fibers, in 24 blocks of 256. Each block compares both implementations at thresholds 17, 20 and 24. Before timing it compares ordered point lists for every case. Method order alternates and threshold order rotates. Wall time includes generation, testing and any materialization. It excludes correctness checks and index generation. Raw replay columns are block, threshold, arm (0 ordinary, 1 streaming), qualifying count and wall milliseconds.

| Threshold | Qualifying fibers | Initial ordinary/stream ms | Repeat ordinary/stream ms | Paired median speed ratio, initial / repeat |
|---|---:|---:|---:|---:|
| 17 | 2716 | 478/453 | 411/470 | 1.111 / 0.866 |
| 20 | 718 | 429/373 | 383/400 | 1.138 / 1.000 |
| 24 | 23 | 347/280 | 324/247 | 1.317 / 1.333 |

Both runs used the same shared M4 Pro. Only aggregate measurements from the initial run were retained. repeat.csv contains all replay rows. At threshold 24 the streaming arm was faster in 16 of 24 initial blocks and 22 of 24 replay blocks. These measurements cover threshold screening only.

From the complete histogram, under uniformly random coordinate order and full enumeration on successful fibers, expected single-coordinate tests are 29.760, 25.593 and 17.989 at the three thresholds. For a fiber with k lifts, after s checks the number seen has a hypergeometric distribution with parameters 32, k and s. Sum the probability of needing the next check over s from 0 to 31, including all 32 checks for qualifying fibers. The benchmark uses the actual kernel order; these random-order expectations describe a separate cost model.
