# Prospective projection round-robin source order did not improve the D79 rank stop

The first two new primes selected by the frozen prescreen were p63317 (`v=251`, `#E=63275`, largest order prime 2531) and p68437 (`v=261`, `#E=68670`, largest order prime 109). Both yielded the expected 40-point conductor-four D79 class with strata 10/10/20, and every degree-13 source lifted and passed its Hecke, modular-polynomial, orbit and group checks. The source orders were sealed from the order-five projection before any degree-13 lift.

| Prime | Order-five class residues | Base + direct rational rank | Direct / Hecke candidates | Ascending rational-rank stop | Projection round-robin stop | Final rank over Q / Fq |
| ---: | --- | ---: | ---: | --- | --- | --- |
| 63317 | 1:20, 4:20 | 37 | 220 / 237 | 14 sources, rank 40 | 16 sources, rank 40 | 40 / 39 |
| 68437 | 1:20, 3:20 | 33 | 200 / 196 | 40-source cap, rank 34 | 40-source cap, rank 34 | 34 / 34 |

Thus the specified projection-only round-robin priority lost two source lifts at p63317. At p68437, its 196 verified outside-trace cancellations added only one rational dimension to the direct-plus-base matrix, and both orders retained a six-dimensional rational kernel at the 40-source cap. This new case shows that full rational rank in the earlier D79 panel does not extend uniformly to the next qualifying primes. The result concerns this exact support-four relation family and source policy.

The frozen prescreen examined ascending odd `v` from 251; the first two qualifying values were 251 and 261, with no substitution after observing their classes or fibers. `post_class.json` binds the class and source orders before the degree-13 producer; `post_source.json` binds all fibers before candidate enumeration; `post_analysis.json` binds the rows and rank paths before independent audit. The audit independently reconstructed all three conductor strata, rebuilt degree-13 functions, freshly replayed all 80 fibers, enumerated direct and trace candidates using Sage group operations, and recomputed both rank paths. Its two cases pass. `verify.py` cross-links the frozen stage receipts and passes.

The producer loaded the 419,160-byte pinned degree-13 function artifact with zero fresh degree-13 builds. The 80 source lifts took 1.77 and 1.58 seconds by case; the direct and trace enumerations took 1.72/1.58 seconds and 1.92/1.68 seconds. These timings are ordinary-host stage diagnostics; the experiment's comparison is exact source count and rank under the frozen 1,800-second per-job cap. `candidate_id` and `target_online_ms` are null.

The finite rank proof certificates and open formal bridges are in [PROOF_MAP.md](PROOF_MAP.md). The next research step is to identify the six-dimensional p68437 kernel's support and whether it follows the conductor-stratum or class-action structure, then prespecify a broader test. A new priority score would need an explicit mechanism for finding rank-raising source sets from information available before lifting.
