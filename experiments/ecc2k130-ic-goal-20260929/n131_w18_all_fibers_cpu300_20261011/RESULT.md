# Frozen all-fiber N131 search extended to a 300-second solver CPU cap

The byte-identical one-seed, eight-free-pair public formula advanced from
50.732 sampled solver CPU seconds in the prior online attempt to **303.247
solver CPU seconds** and 3,059 restart rows. CryptoMiniSat exited on the
frozen CPU soft limit with `BOUNDED_UNKNOWN`; the full transcript contains
no SAT or UNSAT status line. The [independent receipt audit](audit_result.json)
replays the compressed source XCNF byte for byte, verifies the solver binary
and public-point hashes, and checks the saved terminal status and both clocks.

The exact curve is `y²+xy=x³+1` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, subgroup order
`680564733841876926932320129493409985129`, curve ID
`EC1N131Ckb1heb5f1998f20b`. The workload `cc09e7eb202a` fixes the same
public point as the preceding all-fiber query. Its XCNF SHA-256 is
`36d85249ec37f5a754443af94a077bbbfb0d29a23e0e25d4ae285e390fa6d2c8`.
The [frozen protocol](protocol.json) pins one CryptoMiniSat worker, exact
solver hash and flags, 300/305-second soft/hard process CPU limits, a
4,500-second outer wall cap, and a 4-GiB sampled combined RSS cap.

| Same public formula, one worker | Earlier online attempt | CPU-capped solver replay |
| --- | ---: | ---: |
| Solver CPU | 50.732 s sampled | **303.247 s child rusage** |
| Solver restart rows | 1,201 | **3,059** |
| Solver-stage wall | 552.421 s | **3,829.828 s** |
| Sampled combined peak RSS | 230,293,504 B | **271,630,336 B** |
| Terminal status | `BOUNDED_UNKNOWN` at 600.052 s total online cap | **`BOUNDED_UNKNOWN` at CPU soft limit** |

The [replay result](replay_result.json) records process exit `-24`
(`SIGXCPU`), empty stderr, no model/status lines, and the exact stdout and
stderr hashes. Its solver-stage wall interval begins after the archived
target-dependent formula has been restored and verified; the earlier
[online receipt](../n131_w18_all_fibers_inverse_20261011/query_result.json)
retains the public preimage, residual, and formula-construction phases.
This CPU-capped replay is an exploratory search-depth diagnostic on a
contended host, not a one-target online timing comparison. The next exact
ordinary-point gate is the frozen seven-pair four-seed query, which reduces
one nonlinear group link and has passed separate full-assignment and
independent Sage controls. This component has `candidate_id: null`.
