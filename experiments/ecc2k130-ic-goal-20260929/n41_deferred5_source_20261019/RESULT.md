# All-deferred W9 source on the N41 public point

Deferring all five W9 source-eligibility tests removed 925 source-table
clauses from the existing N41 five-pair circuit while retaining its 13,407
AND gates and 2,035 native XOR rows. The frozen ordinary public-point query
ran one CryptoMiniSat 5.14.7 worker for a 90-second solver window and reached
its 95-second parent cap with `BOUNDED_UNKNOWN` and no terminal model. Direct
host monitoring recorded 447 worker-RSS samples, zero monitor errors, and a
461,602,816-byte sampled peak below the 4-GiB limit.

The field is `GF(2)[u]/(u^41+u^3+1)` on `y²+xy=x³+1`, curve ID
`EC1N41Ckb1h7d5e80d3c4d0`. The target is the frozen ordinary raw public
point after Frobenius orientation 3, with reciprocal x coordinate
`1348500684618`. Each of five slots retains the exact fixed-seed
pair-output quadratic, and all four S3 addition links are imposed. The
eight-bit source code in each slot has no inverse-trace or 71-code table
constraint during the query. A constructed assignment from the archived
public-point relation satisfies all 40,598 CNF clauses and 2,035 XOR rows.

| N41 circuit | Source eligibility during SAT | AND gates | CNF clauses | Public query record |
| --- | --- | ---: | ---: | --- |
| Existing `table5` | Exact 71-code table in each slot | 13,407 | 41,523 | 180.047 s, `BOUNDED_UNKNOWN` |
| This `deferred5` run | Checked only after a model | 13,407 | 40,598 | 95.161 s, `BOUNDED_UNKNOWN` at parent cap |

The different time caps and ordinary-host conditions prevent a solver-speed
ranking. The direct model-yield question had a terminal observation: no model
was emitted before this run's cap, so no source or signed-state replay was
triggered. The [query receipt](query_result.json) preserves the command,
limits, status, resource samples, and raw stream hashes. The [build receipt](build_result.json)
preserves the formula hash, phase times, wire map, and constructed control.

The first checkout-directory creation returned `ENOSPC`, before any producer
ran. Its [receipt](workspace_first_attempt_failure.json) records the move to
the temporary volume. A first build launch under system Python failed during
dependency import because that environment lacked `psutil`; its
[receipt](build_first_attempt_failure.json) records zero formula and query
work. The same frozen builder then completed through the repository's checked
Sage launcher. Source files, protocols, raw solver streams, results, and the
checked-Sage runtime receipt were copied content-for-content into this
repository directory. The [relocation-aware auditor](audit.py) checks two
frozen protocols and 15 source hashes; its [result](audit_result.json) passes.

The all-deferred source option does not clear the unpinned N41 model-yield
gate for an N131 W29 public-point run. The next method change should target
the S3 addition-tree search itself or a target-conditioned family constraint
that prunes before solving for all five pair outputs. `candidate_id` remains
null while the full index-calculus pipeline is not specified.
