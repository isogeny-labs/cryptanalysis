# Four d13/m12 preparation queries reach their solver caps

The refrozen d13/m12 candidate has completed four distinct, seeded preparation-point queries with **zero verified relations and rank 0/4,134**. The four charged query intervals total **2,405.270532373 seconds**. Each solver reached its frozen parent timeout without a SAT or UNSAT line. The [independent archive audit](first_four_precomputation_audit_20261115.json) replayed all four [exact attempt rows](first_four_precomputation_attempts_20261115.jsonl), including compressed and uncompressed artifact hashes, complete XCNF record counts, solver stop reasons, and the 4 GiB combined RSS gate.

The candidate is `IC1N131Ckb1fb1083108PDP12satRCdirectLAgaussTDdirectISO0h195ae7ea5e75` on curve `EC1N131Ckb1heb5f1998f20b` and one-point workload `3c1992b7c92f`. Preparation points are seeded nonzero scalar multiples of the audited generator under the protocol's uniform-draw input law; their scalars are fixture inputs and are not supplied to the decomposition solver. The run uses one CryptoMiniSat thread, a 600-second parent solver cap per preparation query, and a 4 GiB combined Sage/solver RSS limit. Its actual factor base has 1,083,108 distinct subgroup-usable points and 4,134 folded columns. Each generated XCNF has 232,244 variables, 228,629 clauses, and 171,278 native XOR rows.

| Preparation query | Status | Charged query wall (s) | Solver wall (s) | Conservative combined peak RSS (B) | Verified relations |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `timeout` | 600.290775 | 598.776484 | 2,395,668,480 | 0 |
| 2 | `timeout` | 605.027071 | 598.854606 | 2,248,654,848 | 0 |
| 3 | `timeout` | 599.782920 | 598.879033 | 2,635,333,632 | 0 |
| 4 | `timeout` | 600.169767 | 598.994223 | 2,700,853,248 | 0 |

The [candidate protocol](d13_m12_single_target_protocol_v1.json) excludes reusable relation-log preparation from the eventual one-target online interval. The 600-second limit applies to the solver parent interval; charged query wall also includes target-dependent formula construction, serialization and local orchestration, which explains query 2's 605.027-second total. The full preparation attempt cap is 8,192; these four observations are a bounded status mix for the named inputs, not a natural-yield estimate for the remaining input law.

At this checkpoint the runner continued to the fifth preparation query. The live external run directory is `/Volumes/SSD990-2/ecc2k130-ic-runstore/d13-m12-20261115/IC1N131Ckb1fb1083108PDP12satRCdirectLAgaussTDdirectISO0h195ae7ea5e75W3c1992b7c92fR1`. Its append-only `precomputation_attempts.jsonl` and `precompute_progress.json` supersede this snapshot for later status. The next method test should attack the observed SAT access cost by rejecting target-conditioned families while multiple pair blocks remain free; the existing exact XOR projections and public-Q SAT arm also reached bounded caps, and the table-free two-pair inverse still needs an outer residual generator.
