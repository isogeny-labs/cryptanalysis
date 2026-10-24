# Generator-shift closure survives a 3,800-column subset of the p20023 table

**Measured result.** Two frozen hash-ordered subsets of the original p20023 Hecke orbit table retain full anchored log rank with **3,800 of 3,949** prepared columns when all available one-generator shift identities are added to the Hecke rows that remain internal to the subset. At **3,600 columns**, the same construction leaves one residual dimension for seed B and two for seed A. The experiment therefore locates a reproducible transition between those two tested densities, rather than attributing zero-seed closure solely to the original 3,949-column table.

The curve is `X₀(11): y²+y=x³−x²−10x−20` over `F_20023`, with projected subgroup order `4,021`. The [frozen protocol](protocol.json) keeps the anchored generator column and takes the first `table_size−1` other columns under a seed-specific SHA-256 ordering. From the saved seed and degree-2/3 Hecke rows, it retains a relation only when all referenced columns survive. For every retained projected point `Q`, it checks whether `Q+G` is another retained point. Connected shift edges express each component's logs as one unknown plus known generator offsets. Reducing the retained Hecke rows to those component unknowns gives an exact `GF(4021)` rank test; the anchor contributes one further row.

| Retained columns | Seed A: relations / shift components / residual nullity | Seed B: relations / shift components / residual nullity |
| ---: | ---: | ---: |
| 3,949 | 5,565 / 70 / **0** | 5,565 / 70 / **0** |
| 3,900 | 5,304 / 117 / **0** | 5,263 / 116 / **0** |
| 3,800 | 4,769 / 207 / **0** | 4,708 / 206 / **0** |
| 3,600 | 3,796 / 377 / **2** | 3,679 / 376 / **1** |
| 3,200 | 2,294 / 660 / 13 | 2,228 / 657 / 10 |
| 2,800 | 1,326 / 857 / 56 | 1,233 / 833 / 58 |
| 2,400 | 681 / 969 / 354 | 643 / 959 / 383 |

The [producer result](result.json) retains every cell's subset digest, number of available shifts, component rank, and residual nullity. The [independent validator](validation.json) reconstructs every projected point, checks all 3,879 one-step shifts available in the full table against curve arithmetic and recovered logs, replays all 3,949 saved table logs and 5,565 original relation equations, and recomputes all 14 component ranks with Sage's separate sparse `GF(4021)` matrix implementation. The producer uses its own modular sparse elimination. Both pass for every cell. The [checked Sage runtime](sage_runtime.json) is saved alongside the experiment.

The shift-component reduction is a finite application of the generator-shift log identity proved in the pinned [Lean module](../hecke-l29-final-kernel-search-20261024/formal/ShiftClosure.lean); this sweep introduces no new general theorem. A full component rank gives unique table logs because the independently checked saved logs satisfy all retained equations. The experiment retains `candidate_id: null` and `timing_claim: null`: its selected columns come from an already prepared table, and table construction and one-target online costs have not been benchmarked here.

The next experiment should freeze additional subsets between 3,600 and 3,800, then measure the actual cost of building those subsets and their relation rows. The present two-seed result is a density sensitivity check, not a population estimate for random tables.
