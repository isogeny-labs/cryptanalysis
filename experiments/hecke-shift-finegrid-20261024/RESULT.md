# Fine-grid shift closure reveals isolated components as the rank bottleneck

**Measured result.** Across 36 frozen subsets of the p20023 Hecke orbit table, every observed residual log dimension is a generator-shift component untouched by any retained Hecke row or the generator anchor. All components with relation incidence have full rank over `GF(4021)` in these cells. At 25-column checkpoints from 3,600 to 3,800 prepared columns, the first full-rank checkpoint is **3,700** for seed A, **3,675** for seeds B and D, and **3,600** for seed C. Full rank persists at every later sampled checkpoint for each seed.

The [protocol](protocol.json) extends the preceding [density sweep](../hecke-shift-density-20261024/RESULT.md) using the same four-term/five-term saved degree-2/3 Hecke rows, subgroup projection, anchored generator, and SHA-256 subset law. It retains a row only when every referenced table column survives, includes every internal `Q+G` identity, contracts the resulting shift graph, and ranks the quotient Hecke system. The two added subset seeds are C and D; A and B reproduce the prior endpoints.

| Table columns | Seed A nullity | Seed B nullity | Seed C nullity | Seed D nullity |
| ---: | ---: | ---: | ---: | ---: |
| 3,600 | 2 | 1 | **0** | 2 |
| 3,625 | 1 | 1 | 0 | 1 |
| 3,650 | 1 | 1 | 0 | 1 |
| 3,675 | 1 | **0** | 0 | **0** |
| 3,700 | **0** | 0 | 0 | 0 |
| 3,725–3,800, every 25 columns | 0 | 0 | 0 | 0 |

For each of the 36 cells, [result.json](result.json) retains the selected-subset digest, accepted relation count, available shift count, component count, quotient rank, residual nullity, and zero-incidence count. In every cell, `residual_nullity == zero_incidence_components`. This identifies a concrete repair target: connect or constrain the unvisited components, for example by checking short multi-generator shifts across missing table points, before seeking more Hecke rows.

The [independent validator](validation.json) rebuilt every projected point and all 3,879 full-table one-step shifts, scalar-replayed the 3,949 saved table logs, checked all 5,565 original relation equations, and recomputed every quotient rank and zero-incidence count with Sage's graph and sparse-matrix implementations. It matched the producer in all 36 cells. The checked [Sage runtime](sage_runtime.json) and raw [producer](producer_stdout.jsonl) and [validator](validator_stdout.jsonl) cell streams are retained. The structural log-shift identity has the pinned [Lean proof](../hecke-l29-final-kernel-search-20261024/formal/ShiftClosure.lean); this finite sweep adds no new general theorem.

These are rank and incidence measurements for deterministic subsets of a previously built table, with `candidate_id: null` and `timing_claim: null`. Four seeds and 25-column spacing support the observed cells, not an exact or population-wide threshold. The next experiment is to freeze a short-shift radius and determine whether it repairs the isolated components at smaller table sizes, recording its additional curve-addition and lookup work.
