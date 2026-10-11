# A 32-state terminal fiber removes one N131 pair and S3 link

An exact public-point residual selector replaces the ninth W18 fixed-seed pair and the last S3 link in the ECC2K-130 nine-pair circuit. The resulting ordinary formula has **48,788 fewer variables, 20,049 fewer AND gates, 59,916 fewer clauses, and 28,491 fewer native-XOR rows** than the frozen nine-pair serial formula on the same public point. A challenge-field constructed control passes every CNF and XOR row, and checked Sage independently verifies all 32 signed terminal states and both sets of 32 residual points. The ordinary query reached its frozen 195-second solver parent cap with `BOUNDED_UNKNOWN`; the smaller circuit has not yet produced an ordinary relation.

The exact field is `GF(2)[t]/(t^131+t^13+t²+t+1)`, the curve is `y²+xy=x³+1`, and the subgroup order is `680564733841876926932320129493409985129` with cofactor four. The curve ID is `EC1N131Ckb1heb5f1998f20b`. Eight free pair slots use W18, seed mask 212, and Frobenius rotations `0,16,...,112`. The terminal pair uses rotation 128. The ordinary workload is the previously frozen public point `cc09e7eb202a` and raw preimage index zero from the [nine-pair comparator](../n131_fixed_seed_ninepair_cubic_20261011/RESULT.md). The solver reads the public point and source pool, not its scalar sidecar.

## Target-conditioned construction

The [frozen pool](pool.json) contains all four signed point sums from each of eight eligible pair edges: the edge used by a separate constructed control, followed by the seven smallest other canonical source codes. This law and the 32 exact point coordinates were fixed before the ordinary query. For each pool state `P₈` and supplied raw target `U`, the online preparer computes `R=U−P₈` and `a_R=1/x(R)`. One-hot choice wires select exactly one of the 32 `a_R` constants. Seven halftrace-cubic S3 links then constrain the eight free pair outputs to sum to the selected residual coordinate. All eight free pair masks remain unpinned.

The [exact source count](source_count.json) deletes edges incident to the selected terminal edge's folded columns, counts eight-edge matchings in the remaining conflict graph, then charges `8!·4⁸` ordered signed assignments per selected state. Across all 32 states, the distinct-column labeled tuple count is `3,084,438,865,729,247,153,235,885,384,531,772,377,661,440`. Dividing by the full curve order `4r` gives a **uniform raw-point mean upper ceiling of 1,133.04389441**. This is a source-support ceiling, not a measured fixed-target relation yield.

## Exact controls and ordinary query

The [constructed-control receipt](control_result.json) checks the selected residual against the known eight-pair group sum and satisfies all 588,373 clauses and 253,645 native-XOR rows. The [checked-Sage replay](sage_audit_result.json), using the saved [runtime receipt](sage_runtime_info.json), reconstructs all source points from the field polynomial, all 32 rotated signed pair sums, every control/public residual, the control witness, and the public subgroup point. The [protocol](protocol.json) binds source and solver hashes, the target, pool, one worker, 4-GiB RSS, and the 180-second CryptoMiniSat setting with a 195-second parent solver cap before either circuit was run.

| Measure | Frozen nine-pair serial | 32-state terminal fiber |
| --- | ---: | ---: |
| Variables / AND gates | 499,736 / 215,343 | **450,948 / 195,294** |
| Clauses / native-XOR rows | 648,289 / 282,136 | **588,373 / 253,645** |
| XCNF bytes | 21,470,484 | 19,271,319 |
| Solver parent status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |
| Sampled combined peak RSS | 683,196,416 B | 379,650,048 B |

The [ordinary query receipt](query_result.json) records exclusive target-dependent phases: 6.836 seconds to generate and check 32 residuals, 69.407 seconds to build the XCNF, 0.510 seconds to serialize it, 196.691 seconds for solver launch/search/stop, and 0.161 seconds for terminal parsing, totaling **273.604 seconds**. CryptoMiniSat entered search and logged 33 restart rows; stderr was empty and there was no terminal SAT/UNSAT line or model. The [terminal auditor](audit_result.json) checks the exact phase sum, source and public-point identity, formula reduction, solver transcript, resource bound, and [byte-replay archives](archive_receipt.json) for both XCNFs.

These runs used a contended local host; the structural formula reduction is exact, while wall and restart counts are exploratory. The pool's source ceiling motivates the 32-way filter, but ordinary yield and novel relation rank remain unmeasured. This is a proposal-stage component with `candidate_id: null`. The next gate is a full N41 restricted-pool relation/rank check using this terminal-fiber law, followed by an N131 query with auditable CPU entitlement or a stronger target-conditioned pruning rule. The factor-log, final matrix, scalar-recovery, and matched-rho phases remain in the active single-target goal.
