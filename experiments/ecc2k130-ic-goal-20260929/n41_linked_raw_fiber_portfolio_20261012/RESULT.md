# Four raw-fiber slices of the linked N41 public circuit

**A frozen four-slice target-fiber portfolio completed the N41 linked-source public search in 155.884228208 seconds, and every unpinned slice reached its 38-second cap.** All four raw preimages were covered in numeric order, including fiber 3, which contains the independently checked linked relation. The target fiber alone therefore did not make this functional full-point SAT encoding select a public relation at the declared per-slice limit.

## Instance and exact slicing

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t³+1)`, with equation `y²+xy=x³+1`, subgroup order `549756390943`, and cofactor four. The frozen public point is `[920359962848,755404565011]`. The source has nine free signed W8 pair-state selectors; positions 0 and 1 share the same state across Frobenius rotations 0 and 7, and all nine source edges must differ. Every source selector remains free in every slice. Each slice adds exactly one unit clause selecting one of the four raw target preimages to the [linked functional full-point formula](../n41_linked_functional_fullpoint_20261012/RESULT.md).

The [protocol](protocol.json) fixed numeric fiber order `(0,1,2,3)`, one worker, a 38-second parent cap per slice, a 180-second global cap, 4-GiB combined RSS, and stop-on-first-replayed-SAT before execution. The [terminal audit](audit_result.json) rebuilt the base and all four sliced XCNFs byte for byte, checked the known linked assignment in fiber 3, and matched every solver transcript and phase cost. The [archive](archive_result.json) retains all five formulas as byte-replayable gzip files; the [read-only verifier](verify.py) passes after the raw XCNFs are removed.

| Fiber | Parent solver status | Solver wall, exploratory | Restart rows |
| ---: | --- | ---: | ---: |
| 0 | `PARENT_TIME_CAP` | 38.118741875 s | 61 |
| 1 | `PARENT_TIME_CAP` | 38.019847750 s | 35 |
| 2 | `PARENT_TIME_CAP` | 38.018582500 s | 48 |
| 3 | `PARENT_TIME_CAP` | 38.087209334 s | 86 |

Each slice has 121,257 variables, 315,316 CNF clauses, 52,327 native-XOR rows, and a 6,883,625-byte XCNF. The complete attempt had sampled peak combined RSS `175046656` bytes and status `BOUNDED_UNKNOWN`. None of the four solver streams contains a terminal SAT/UNSAT line. These are capped searches, not complete source-family misses.

| Exclusive charged phase | Nanoseconds |
| --- | ---: |
| Target-dependent base construction | 3,556,528,000 |
| Base serialization | 15,314,208 |
| Four slice serializations | 57,132,042 |
| Four solver intervals, including failed searches | 152,244,381,459 |
| Bookkeeping and receipt checks | 10,872,499 |
| **Total target-dependent attempt** | **155,884,228,208** |

The monolithic linked circuit also reached its 180-second cap. The different search paths and shared-host wall times do not establish a controlled timing comparison. This experiment is a source-selection diagnostic with `candidate_id: null`.

## Next method gate

Target-fiber branching and the earlier root-branch portfolios leave source selection active. The next filter must impose a public-target condition on **two implicit partial-sum families together**, with an exact preservation proof and measured whole-family rejection before pair states are enumerated. The N41 gate remains an unpinned relation with independent group and rank replay; its N131 projection must count construction, failed probes, memory, and one-worker work under 600 seconds and 4 GiB before another public query.
